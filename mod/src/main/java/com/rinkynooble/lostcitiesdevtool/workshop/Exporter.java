package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.rinkynooble.lostcitiesdevtool.chat.ProfileKeys;
import com.rinkynooble.lostcitiesdevtool.validate.AssetValidator;
import com.rinkynooble.lostcitiesdevtool.validate.Finding;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;

import javax.annotation.Nullable;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/**
 * The compiler: what is built in the workshop, turned into a Lost Cities datapack.
 *
 * <p>Reads every plot that has settings, cuts it into parts on a stride of six, gives
 * every distinct cell a character, and writes the assets that reference each other
 * correctly. Nothing is written until the whole pack has been through the same
 * checks the mod runs on a datapack at load time, so a pack that would fail in a
 * world fails here instead, where the message can name the plot.
 */
public final class Exporter {

    /** Vanilla's ceiling. Only used to say when a build could not fit a real world. */
    private static final int VANILLA_CEILING = 319;

    /** The default ground level a profile uses, for the height warning. */
    private static final int DEFAULT_GROUND = 71;

    public record Result(int plots, int parts, int buildings, int palettes,
                         List<String> warnings, List<Finding> findings, Path root) {

        public boolean failed() {
            return findings.stream()
                    .anyMatch(f -> f.severity() == Finding.Severity.ERROR);
        }
    }

    private final MinecraftServer server;
    private final ServerLevel level;
    private final PaletteLedger ledger;
    private final JsonObject core;
    private final String namespace;

    /** cell key -> the palette entry it becomes. Built as the parts are read. */
    private final Map<String, JsonObject> cells = new LinkedHashMap<>();
    private final Map<String, JsonObject> assets = new LinkedHashMap<>();
    private final List<String> warnings = new ArrayList<>();

    /** city style -> selector key -> the entries collected for it. */
    private final Map<String, Map<String, JsonArray>> selectors = new TreeMap<>();
    /** city style -> street shape -> the part names collected for it. */
    private final Map<String, Map<String, JsonArray>> streets = new TreeMap<>();
    /** world style family -> shape -> part names. */
    private final Map<String, Map<String, JsonArray>> worldParts = new TreeMap<>();

    private int partCount;
    private int buildingCount;

    private Exporter(MinecraftServer server, ServerLevel level, PaletteLedger ledger,
                     JsonObject core) {
        this.server = server;
        this.level = level;
        this.ledger = ledger;
        this.core = core;
        this.namespace = string(core, "namespace", "mypack");
    }

    // -------------------------------------------------------------------- entry

    public static Result run(MinecraftServer server, ServerLevel level, String name,
                             boolean force) throws IOException {
        JsonObject core = SettingsStore.load(server, Layout.CORE_ID);
        PaletteLedger ledger = PaletteLedger.load(server);
        Exporter exporter = new Exporter(server, level, ledger, core);

        Path root = exportsRoot(server).resolve(name);
        if (Files.exists(root) && !force) {
            throw new IOException("an export named " + name + " is already there. "
                    + "Pass -f to overwrite it");
        }

        int plots = exporter.compile();
        List<Finding> findings = exporter.check();
        if (findings.stream().anyMatch(f -> f.severity() == Finding.Severity.ERROR)) {
            return new Result(plots, exporter.partCount, exporter.buildingCount,
                    exporter.cells.isEmpty() ? 0 : 1, exporter.warnings, findings,
                    root);
        }
        exporter.write(root, name);
        ledger.save(server);
        return new Result(plots, exporter.partCount, exporter.buildingCount,
                exporter.cells.isEmpty() ? 0 : 1, exporter.warnings, findings, root);
    }

    public static Path exportsRoot(MinecraftServer server) {
        return Path.of("config", "lostcitiesdevtool", "exports")
                .toAbsolutePath().normalize();
    }

    // ------------------------------------------------------------------ compile

    private int compile() throws IOException {
        int done = 0;
        for (Layout.Plot plot : Layout.plots()) {
            if (plot.row() == null) {
                continue;
            }
            JsonObject settings = SettingsStore.load(server, plot.id());
            if (settings.keySet().isEmpty() || bool(settings, "skip", false)) {
                continue;
            }
            compilePlot(plot, settings);
            done++;
        }
        buildStyles();
        return done;
    }

    private void compilePlot(Layout.Plot plot, JsonObject settings) {
        Catalogue.Row row = plot.row();
        String name = string(settings, "name", plot.id().replace('/', '_'));
        boolean stacked = "buildings".equals(row.key())
                || "multibuildings".equals(row.key());

        if (!stacked) {
            // One part, read from the plot floor up.
            int height = Math.max(2, intOf(settings, "height", 6));
            String partName = name;
            emitPart(partName, plot, 0, 0, Boundaries.BASE, height, settings);
            record(row, plot, settings, name, partName);
            return;
        }

        // A stack of levels, per chunk. A multi-chunk plot is one Building per chunk
        // plus a MultiBuilding naming them, which is what the format expects.
        List<String> buildings = new ArrayList<>();
        for (int dz = 0; dz < plot.height(); dz++) {
            for (int dx = 0; dx < plot.width(); dx++) {
                String buildingName = plot.width() == 1 && plot.height() == 1
                        ? name : name + "_" + dx + "_" + dz;
                buildings.add(namespace + ":" + buildingName);
                emitBuilding(buildingName, plot, dx, dz, settings);
            }
        }
        if (plot.width() > 1 || plot.height() > 1) {
            JsonObject multi = new JsonObject();
            multi.addProperty("dimx", plot.width());
            multi.addProperty("dimz", plot.height());
            JsonArray list = new JsonArray();
            buildings.forEach(list::add);
            multi.add("buildings", list);
            assets.put("multibuildings/" + name, multi);
            record(row, plot, settings, name, name);
        } else {
            record(row, plot, settings, name, name);
        }
    }

    /** One building: its levels, each a part, with the conditions that pick them. */
    private void emitBuilding(String name, Layout.Plot plot, int dx, int dz,
                              JsonObject plotSettings) {
        JsonObject settings = Settings.resolve(plotSettings, dx, dz, 0);
        int cellars = Math.max(0, intOf(settings, "cellars", 0));
        int floors = Math.max(0, intOf(settings, "floors", 1));
        List<Integer> tops = ints(settings, "tops");

        JsonObject building = new JsonObject();
        building.addProperty("refpalette", namespace + ":main");
        // `filler` is required on every building, whether or not it has cellars, so
        // the export has to have one. Defaulting to the commonest character on the
        // ground floor makes the skirt look like the walls above it, which is what
        // somebody would have chosen by hand.
        building.addProperty("minfloors", floors);
        building.addProperty("maxfloors", floors);
        building.addProperty("mincellars", cellars);
        building.addProperty("maxcellars", cellars);
        building.addProperty("overrideFloors", true);

        if (settings.has("rubble")) {
            building.addProperty("rubble", string(settings, "rubble", " "));
        }
        if (settings.has("preferslonely")) {
            building.addProperty("preferslonely",
                    settings.get("preferslonely").getAsFloat());
        }

        JsonArray parts = new JsonArray();
        char commonest = PaletteLedger.AIR;
        int y = Boundaries.BASE;
        for (int c = cellars; c >= 1; c--) {
            String part = name + "_c" + c;
            emitPart(part, plot, dx, dz, y, Boundaries.STRIDE,
                    Settings.resolve(plotSettings, dx, dz, -c));
            parts.add(ref(part, "floor", -c));
            y += Boundaries.STRIDE;
        }
        for (int f = 0; f <= floors; f++) {
            String part = name + "_f" + f;
            char drew = emitPart(part, plot, dx, dz, y, Boundaries.STRIDE,
                    Settings.resolve(plotSettings, dx, dz, f));
            if (f == 0) {
                commonest = drew;
            }
            parts.add(ref(part, "floor", f));
            y += Boundaries.STRIDE;
        }
        // The tops are alternatives, all conditioned on being at the top, so the mod
        // picks one. Their heights are free because nothing is placed above a top.
        for (int t = 0; t < tops.size(); t++) {
            int height = Math.max(2, tops.get(t));
            String part = name + "_t" + (t + 1);
            emitPart(part, plot, dx, dz, y, height,
                    Settings.resolve(plotSettings, dx, dz, floors + 1 + t));
            JsonObject r = new JsonObject();
            r.addProperty("part", namespace + ":" + part);
            r.addProperty("top", true);
            parts.add(r);
            y += height;
        }
        warnIfTooTall(name, cellars, floors, tops);

        building.addProperty("filler", settings.has("filler")
                ? string(settings, "filler", String.valueOf(commonest))
                : String.valueOf(commonest));
        if (commonest == PaletteLedger.AIR && cellars > 0) {
            warnings.add(name + " has cellars and nothing solid on its ground floor, "
                    + "so its filler skirt is air. Set filler on the plot.");
        }
        building.add("parts", parts);
        assets.put("buildings/" + name, building);
        buildingCount++;
    }

    private JsonObject ref(String part, String key, int value) {
        JsonObject r = new JsonObject();
        r.addProperty("part", namespace + ":" + part);
        r.addProperty(key, value);
        return r;
    }

    /**
     * Read one part out of the world.
     *
     * <p>{@code slices} is one string per layer, and inside a layer the mod reads
     * {@code z * xsize + x}, so a row runs east and the row index runs south.
     *
     * <p>Never one slice. A part of a single layer draws nothing at all, measured, so
     * a height of one is silently raised to two rather than producing a part that
     * loads and does nothing.
     */
    private char emitPart(String name, Layout.Plot plot, int dx, int dz,
                          int baseY, int height, JsonObject settings) {
        int x0 = plot.blockMinX() + dx * 16;
        int z0 = plot.blockMinZ() + dz * 16;
        JsonObject marks = settings.has("marks") && settings.get("marks").isJsonObject()
                ? settings.getAsJsonObject("marks") : new JsonObject();
        JsonObject conversions = merged("conversions", settings);

        Map<Character, Integer> seen = new LinkedHashMap<>();
        JsonArray slices = new JsonArray();
        for (int y = 0; y < Math.max(2, height); y++) {
            JsonArray layer = new JsonArray();
            for (int z = 0; z < 16; z++) {
                StringBuilder row = new StringBuilder(16);
                for (int x = 0; x < 16; x++) {
                    char c = characterAt(x0 + x, baseY + y, z0 + z,
                            dx * 16 + x, baseY + y, dz * 16 + z, marks, conversions);
                    row.append(c);
                    if (c != PaletteLedger.AIR) {
                        seen.merge(c, 1, Integer::sum);
                    }
                }
                layer.add(row.toString());
            }
            slices.add(layer);
        }

        JsonObject part = new JsonObject();
        part.addProperty("xsize", 16);
        part.addProperty("zsize", 16);
        part.addProperty("refpalette", namespace + ":main");
        part.add("slices", slices);
        assets.put("parts/" + name, part);
        partCount++;
        return seen.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse(PaletteLedger.AIR);
    }

    /** The character for one block, assigning one where the cell is new. */
    private char characterAt(int wx, int wy, int wz, int lx, int ly, int lz,
                             JsonObject marks, JsonObject conversions) {
        // ly is the world height the mark was recorded against, not the layer index.
        BlockState state = level.getBlockState(new BlockPos(wx, wy, wz));
        if (state.isAir() || state.is(Blocks.STRUCTURE_VOID)) {
            // Lost Cities has no "leave this alone" character: every position in a
            // slice places something. A structure void therefore becomes air, which
            // is the closest thing the format has.
            return PaletteLedger.AIR;
        }
        String block = describe(state);
        String converted = conversions.has(block)
                ? conversions.get(block).getAsString()
                : conversions.has(idOf(state))
                        ? conversions.get(idOf(state)).getAsString() : block;

        JsonObject mark = null;
        String at = lx + "," + (wy - Boundaries.BASE) + "," + lz;
        if (marks.has(at) && marks.get(at).isJsonObject()) {
            mark = marks.getAsJsonObject(at);
        }
        String key = converted + (mark == null ? "" : " " + mark);
        char c = ledger.characterFor(key);
        if (c == 0) {
            warnings.add("Ran out of palette characters at " + wx + "," + wy + ","
                    + wz + ". The pool holds " + ledger.capacity() + ".");
            return PaletteLedger.AIR;
        }
        if (!cells.containsKey(key)) {
            JsonObject entry = new JsonObject();
            entry.addProperty("char", String.valueOf(c));
            entry.addProperty("block", converted);
            if (mark != null) {
                for (String k : mark.keySet()) {
                    entry.add(k, mark.get(k));
                }
            }
            cells.put(key, entry);
        }
        return c;
    }

    /** Where this plot's name goes: a selector, a street shape, or the world style. */
    private void record(Catalogue.Row row, Layout.Plot plot, JsonObject settings,
                        String assetName, String partName) {
        String full = namespace + ":" + assetName;
        if (!row.cityStyleScoped()) {
            worldParts.computeIfAbsent(family(row), k -> new TreeMap<>())
                    .computeIfAbsent(row.key(), k -> new JsonArray())
                    .add(namespace + ":" + partName);
            return;
        }
        List<String> styles = strings(settings, "citystyles");
        if (styles.isEmpty()) {
            warnings.add(plot.id() + " names no city style, so nothing references it. "
                    + "Set citystyles on it.");
            return;
        }
        for (String style : styles) {
            if ("StreetParts".equals(row.family())) {
                streets.computeIfAbsent(style, k -> new TreeMap<>())
                        .computeIfAbsent(row.key(), k -> new JsonArray())
                        .add(namespace + ":" + partName);
            } else {
                JsonObject entry = new JsonObject();
                entry.addProperty("factor", settings.has("factor")
                        ? settings.get("factor").getAsFloat() : 1.0f);
                entry.addProperty("value", full);
                for (String k : List.of("feather", "minSpawnDistance",
                        "maxSpawnDistance")) {
                    if (settings.has(k)) {
                        entry.add(k, settings.get(k));
                    }
                }
                selectors.computeIfAbsent(style, k -> new TreeMap<>())
                        .computeIfAbsent(row.key(), k -> new JsonArray())
                        .add(entry);
            }
        }
    }

    private static String family(Catalogue.Row row) {
        return switch (row.family()) {
            case "HighwayParts" -> "highways";
            case "RailwayParts" -> "railways";
            case "MonorailParts" -> "monorails";
            default -> "highways";
        };
    }

    // ------------------------------------------------------------- the top level

    private void buildStyles() {
        JsonArray palette = new JsonArray();
        JsonObject air = new JsonObject();
        air.addProperty("char", String.valueOf(PaletteLedger.AIR));
        air.addProperty("block", "minecraft:air");
        palette.add(air);
        cells.values().forEach(palette::add);
        JsonObject paletteAsset = new JsonObject();
        paletteAsset.add("palette", palette);
        assets.put("palettes/main", paletteAsset);

        // The mod's own palettes first so the shipped parts a city style inherits
        // still resolve, and this pack's last so its characters win. The pack's
        // characters are Greek, Cyrillic and six punctuation marks, none of which
        // the mod uses, so nothing is taken away from anything.
        for (String which : List.of("main", "outside")) {
            JsonArray groups = new JsonArray();
            for (String p : List.of("common", "default", "bricks_standard",
                    "glass_full", "glass_side_variant_glass")) {
                groups.add(group(p));
            }
            groups.add(group(namespace + ":main"));
            JsonObject style = new JsonObject();
            style.add("randompalettes", groups);
            assets.put("styles/" + which, style);
        }

        Set<String> styles = new LinkedHashSet<>(selectors.keySet());
        styles.addAll(streets.keySet());
        for (String style : styles) {
            JsonObject city = new JsonObject();
            city.addProperty("inherit", "citystyle_common");
            city.addProperty("style", namespace + ":main");
            if (streets.containsKey(style)) {
                JsonObject parts = new JsonObject();
                streets.get(style).forEach(parts::add);
                JsonObject street = new JsonObject();
                street.add("parts", parts);
                city.add("streetblocks", street);
            }
            if (selectors.containsKey(style)) {
                JsonObject sel = new JsonObject();
                selectors.get(style).forEach(sel::add);
                city.add("selectors", sel);
            }
            assets.put("citystyles/" + style, city);
        }

        JsonObject world = new JsonObject();
        world.addProperty("outsidestyle", namespace + ":outside");
        JsonArray list = new JsonArray();
        for (String style : styles) {
            JsonObject e = new JsonObject();
            e.addProperty("factor", 1.0);
            e.addProperty("citystyle", namespace + ":" + style);
            list.add(e);
        }
        world.add("citystyles", list);
        if (!worldParts.isEmpty()) {
            JsonObject parts = new JsonObject();
            worldParts.forEach((fam, shapes) -> {
                JsonObject o = new JsonObject();
                shapes.forEach(o::add);
                parts.add(fam, o);
            });
            world.add("parts", parts);
        }
        assets.put("worldstyles/" + string(core, "worldStyle", "main"), world);
    }

    private JsonArray group(String palette) {
        JsonObject one = new JsonObject();
        one.addProperty("factor", 1.0);
        one.addProperty("palette", palette);
        JsonArray g = new JsonArray();
        g.add(one);
        return g;
    }

    // ------------------------------------------------------------------ checking

    /** The same rules the mod runs on a datapack at load time, before writing. */
    private List<Finding> check() {
        List<Finding> out = new ArrayList<>();
        for (Map.Entry<String, JsonObject> e : assets.entrySet()) {
            String kind = e.getKey().substring(0, e.getKey().indexOf('/'));
            String text = json(e.getValue());
            out.addAll(AssetValidator.validate(e.getKey() + ".json", kind,
                    e.getValue(), text));
        }
        return out;
    }

    private void warnIfTooTall(String name, int cellars, int floors,
                               List<Integer> tops) {
        int top = DEFAULT_GROUND + (floors + 1) * Boundaries.STRIDE
                + tops.stream().mapToInt(Integer::intValue).max().orElse(0);
        if (top > VANILLA_CEILING) {
            warnings.add(name + " reaches y " + top + " on a default profile, above "
                    + "vanilla's " + VANILLA_CEILING + ". Fine with a mod that "
                    + "raises the ceiling, clipped without one.");
        }
        if (cellars > 0 && DEFAULT_GROUND - cellars * Boundaries.STRIDE < -64) {
            warnings.add(name + " has more cellars than a default profile has room "
                    + "for below ground.");
        }
    }

    // ------------------------------------------------------------------- writing

    private void write(Path root, String name) throws IOException {
        if (Files.exists(root)) {
            deleteTree(root);
        }
        Path data = root.resolve("data").resolve(namespace).resolve("lostcities");
        for (Map.Entry<String, JsonObject> e : assets.entrySet()) {
            Path file = data.resolve(e.getKey() + ".json");
            Files.createDirectories(file.getParent());
            Files.writeString(file, json(e.getValue()), StandardCharsets.UTF_8);
        }

        JsonObject meta = new JsonObject();
        JsonObject pack = new JsonObject();
        pack.addProperty("pack_format", 15);
        pack.addProperty("description", string(core, "description",
                string(core, "packName", name)));
        meta.add("pack", pack);
        Files.writeString(root.resolve("pack.mcmeta"), json(meta),
                StandardCharsets.UTF_8);

        // The profile is config, not datapack, so it sits beside the pack rather
        // than inside it. Its worldStyle is the join between the two.
        //
        // Every key goes in the section the mod registered it under, looked up
        // rather than guessed. A profile key in the wrong section is not an error
        // and is not reported: it is simply never read, and the setting silently
        // does nothing. `cityChance` is in `cities`, not `lostcity`, and putting it
        // in the obvious place is how this export produced a world with no
        // buildings in it the first time.
        JsonObject profile = new JsonObject();
        Map<String, JsonObject> sections = new LinkedHashMap<>();
        JsonObject raw = merged("profile", core);
        for (String key : raw.keySet()) {
            ProfileKeys.Key known = ProfileKeys.get(key);
            if (known == null) {
                warnings.add(key + " is not a profile key this version declares, so "
                        + "it was written under lostcity and will be ignored.");
            }
            String section = known == null || known.section() == null
                    ? "lostcity" : known.section();
            sections.computeIfAbsent(section, k -> new JsonObject())
                    .add(key, raw.get(key));
        }
        sections.computeIfAbsent("lostcity", k -> new JsonObject())
                .addProperty("worldStyle",
                        namespace + ":" + string(core, "worldStyle", "main"));
        sections.forEach(profile::add);
        Path profileDir = root.resolve("profile");
        Files.createDirectories(profileDir);
        Files.writeString(profileDir.resolve(name + ".json"), json(profile),
                StandardCharsets.UTF_8);
    }

    private static void deleteTree(Path root) throws IOException {
        try (var walk = Files.walk(root)) {
            for (Path p : walk.sorted((a, b) -> b.getNameCount() - a.getNameCount())
                    .toList()) {
                Files.deleteIfExists(p);
            }
        }
    }

    // ----------------------------------------------------------------- plumbing

    /** A block state as Lost Cities writes one: id, then properties in brackets. */
    private static String describe(BlockState state) {
        String id = idOf(state);
        if (state.getValues().isEmpty()) {
            return id;
        }
        StringBuilder out = new StringBuilder(id).append('[');
        boolean first = true;
        for (Map.Entry<Property<?>, Comparable<?>> e : state.getValues().entrySet()) {
            if (!first) {
                out.append(',');
            }
            first = false;
            out.append(e.getKey().getName()).append('=')
                    .append(value(e.getKey(), e.getValue()));
        }
        return out.append(']').toString();
    }

    @SuppressWarnings("unchecked")
    private static <T extends Comparable<T>> String value(Property<?> property,
                                                          Comparable<?> value) {
        return ((Property<T>) property).getName((T) value);
    }

    private static String idOf(BlockState state) {
        return String.valueOf(BuiltInRegistries.BLOCK.getKey(state.getBlock()));
    }

    private static String json(JsonElement e) {
        return new GsonBuilder().setPrettyPrinting().disableHtmlEscaping()
                .create().toJson(e) + "\n";
    }

    private JsonObject merged(String key, JsonObject from) {
        JsonObject out = new JsonObject();
        if (from.has(key) && from.get(key).isJsonObject()) {
            from.getAsJsonObject(key).entrySet()
                    .forEach(e -> out.add(e.getKey(), e.getValue()));
        }
        if (from != core && core.has(key) && core.get(key).isJsonObject()) {
            core.getAsJsonObject(key).entrySet()
                    .forEach(e -> out.add(e.getKey(), e.getValue()));
        }
        return out;
    }

    private static String string(JsonObject o, String key, String fallback) {
        try {
            return o.has(key) ? o.get(key).getAsString() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    private static int intOf(JsonObject o, String key, int fallback) {
        try {
            return o.has(key) ? o.get(key).getAsInt() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    private static boolean bool(JsonObject o, String key, boolean fallback) {
        try {
            return o.has(key) ? o.get(key).getAsBoolean() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    private static List<String> strings(JsonObject o, String key) {
        List<String> out = new ArrayList<>();
        if (o.has(key) && o.get(key).isJsonArray()) {
            o.getAsJsonArray(key).forEach(e -> out.add(e.getAsString()));
        }
        return out;
    }

    private static List<Integer> ints(JsonObject o, String key) {
        List<Integer> out = new ArrayList<>();
        if (o.has(key) && o.get(key).isJsonArray()) {
            o.getAsJsonArray(key).forEach(e -> {
                try {
                    out.add(e.getAsInt());
                } catch (RuntimeException ignored) {
                    // Malformed entries are the file's problem; the check reports it.
                }
            });
        }
        return out;
    }
}
