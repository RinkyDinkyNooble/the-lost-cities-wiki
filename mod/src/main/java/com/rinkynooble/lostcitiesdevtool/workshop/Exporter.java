package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.rinkynooble.lostcitiesdevtool.chat.ProfileKeys;
import com.rinkynooble.lostcitiesdevtool.json5.Json5;
import com.rinkynooble.lostcitiesdevtool.validate.AssetValidator;
import com.rinkynooble.lostcitiesdevtool.validate.Finding;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.packs.PackType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

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

/**
     * The area a multibuilding is placed inside, unless the world style says
     * otherwise.
     *
     * <p>The world is tiled into squares of {@code areasize} chunks and each square
     * gets its own roll. Placement is {@code random(areasize - dimx + 1)}, so a
     * footprint wider than the area makes that bound zero or negative and the mod
     * throws: this is the real ceiling on how large a multibuilding can be.
     *
     * <p>{@code minimum} and {@code maximum} are <b>how many</b> multibuildings are
     * attempted per area, not how large one may be. Raising them for a large
     * footprint would put more buildings in the world and do nothing about its size.
     */
    private static final int DEFAULT_MULTI_AREASIZE = 10;

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
    /** {@code family/shape} for the keys whose codec takes one name, not a list. */
    private final Set<String> singleValued = new LinkedHashSet<>();

    /** asset key -> the plot that claimed it, so a second claim can name the first. */
    private final Map<String, String> claimedBy = new LinkedHashMap<>();
    /** Faults found while compiling, which the file-by-file rules cannot see. */
    private final List<Finding> faults = new ArrayList<>();

    private int partCount;
    private int buildingCount;
    /** The largest footprint any multibuilding in this pack has. */
    private int largestMulti;

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
            // Honoured as written. A part that is not a level of a building
            // draws fine at a single slice, and every street shape the mod ships
            // is exactly one: a road is one layer of blocks.
            int height = Math.max(1, intOf(settings, "height", 6));
            String partName = name;
            // A flat plot is one part, so `building` and `part` mean the same
            // thing here: its own palette, carried in the file.
            emitPart(partName, plot, 0, 0, Boundaries.BASE, height, settings,
                    sinkFor(settings, "global".equals(placement(settings))
                            ? null : new LinkedHashMap<>()));
            applyRaw("parts/" + partName, settings);
            record(row, plot, settings, name, partName);
            return;
        }

        // A stack of levels, per chunk. A multi-chunk plot is one Building per chunk
        // plus a MultiBuilding naming them, which is what the format expects.
        //
        // The grid is `buildings[x][z]`: **the outer list is the X axis** and the
        // inner list is Z. It is not laid out the way it looks, and a flat list or
        // the axes the other way round produces a structure that loads and comes out
        // transposed.
        JsonArray grid = new JsonArray();
        for (int dx = 0; dx < plot.width(); dx++) {
            JsonArray column = new JsonArray();
            for (int dz = 0; dz < plot.height(); dz++) {
                String buildingName = plot.width() == 1 && plot.height() == 1
                        ? name : name + "_" + dx + "_" + dz;
                column.add(namespace + ":" + buildingName);
                emitBuilding(buildingName, plot, dx, dz, settings);
            }
            grid.add(column);
        }
        if (plot.width() > 1 || plot.height() > 1) {
            JsonObject multi = new JsonObject();
            largestMulti = Math.max(largestMulti,
                    Math.max(plot.width(), plot.height()));
            multi.addProperty("dimx", plot.width());
            multi.addProperty("dimz", plot.height());
            multi.add("buildings", grid);
            putAsset("multibuildings/" + name, multi, plot);
            applyRaw("multibuildings/" + name, settings);
            record(row, plot, settings, name, name);
        } else {
            applyRaw("buildings/" + name, settings);
            record(row, plot, settings, name, name);
        }
    }

    /**
     * Merge a plot's {@code raw} object into the asset it produced.
     *
     * <p>The escape hatch, and the settings file tells its reader in as many words
     * that this is what happens to it. The format has keys the schema here does not
     * cover, {@code parts2}, {@code variants}, {@code scattered} and the conditions
     * beyond a level index among them, and without this the only way to reach one is
     * to edit the export by hand after every run.
     *
     * <p>Written last and over the top, so it can correct the compiler as well as
     * add to it. That is the point of an escape hatch: the person using it has read
     * further than the tool has.
     */
    private void applyRaw(String assetKey, JsonObject settings) {
        if (!settings.has("raw") || !settings.get("raw").isJsonObject()) {
            return;
        }
        JsonObject target = assets.get(assetKey);
        if (target == null) {
            return;
        }
        JsonObject raw = settings.getAsJsonObject("raw");
        for (String key : raw.keySet()) {
            target.add(key, raw.get(key));
        }
    }

    /** One building: its levels, each a part, with the conditions that pick them. */
    private void emitBuilding(String name, Layout.Plot plot, int dx, int dz,
                              JsonObject plotSettings) {
        JsonObject settings = Settings.resolve(plotSettings, dx, dz, 0);
        int cellars = Math.max(0, intOf(settings, "cellars", 0));
        int floors = Math.max(0, intOf(settings, "floors", 1));
        List<Integer> tops = ints(settings, "tops");

        // A pack may leave the count to the profile, in which case the parts are a
        // bag the generator draws from rather than a fixed stack. Writing bounds
        // then would pin a building that was never meant to be pinned.
        boolean pin = bool(settings, "pinFloors", true);
        if (!pin && tops.isEmpty()) {
            // An unpinned building's floors are all conditioned `top: false`, so
            // without a roof the topmost level of every height it could be rolled
            // at matches nothing at all. The mod's own are written the same way and
            // every one of them has roofs: building1 has nine floors and five.
            faults.add(Finding.error(plot.id(), 0,
                    name + " has pinFloors false and no tops",
                    "An unpinned building's floors all carry `top: false`, so with "
                            + "no roof the top of it matches no part at whatever "
                            + "height the profile rolls. Set `tops`, or set "
                            + "`pinFloors true` and let the plot fix its own height"));
        }

        // Where this building's characters go. `building` gives the whole thing
        // one palette of its own; `part` gives each of its parts one and leaves the
        // building pointing at the shared palette, because `filler` and `rubble` are
        // resolved in the building's palette and not in any part's.
        String placement = placement(settings);
        boolean perBuilding = "building".equals(placement);
        boolean perPart = "part".equals(placement);
        Map<String, JsonObject> buildingSink =
                perBuilding ? new LinkedHashMap<>() : cells;

        JsonObject building = new JsonObject();
        if (!perBuilding) {
            building.addProperty("refpalette", namespace + ":main");
        }
        // `filler` is required on every building, whether or not it has cellars, so
        // the export has to have one. Defaulting to the commonest character on the
        // ground floor makes the skirt look like the walls above it, which is what
        // somebody would have chosen by hand.
        if (pin) {
            building.addProperty("minfloors", floors);
            building.addProperty("maxfloors", floors);
            building.addProperty("mincellars", cellars);
            building.addProperty("maxcellars", cellars);
            building.addProperty("overrideFloors", true);
        }

        if (settings.has("rubble")) {
            building.addProperty("rubble", paletteValue(
                    string(settings, "rubble", " "), name + " rubble", buildingSink));
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
                    Settings.resolve(plotSettings, dx, dz, -c),
                    perPart ? new LinkedHashMap<>() : buildingSink);
            parts.add(ref(part, "floor", -c));
            y += Boundaries.STRIDE;
        }
        for (int f = 0; f <= floors; f++) {
            String part = name + "_f" + f;
            char drew = emitPart(part, plot, dx, dz, y, Boundaries.STRIDE,
                    Settings.resolve(plotSettings, dx, dz, f),
                    perPart ? new LinkedHashMap<>() : buildingSink);
            if (f == 0) {
                commonest = drew;
            }
            // Unpinned, the entry carries `top: false` and no level: the parts are
            // a bag the generator draws from, and `top` is a boolean, not a number.
            parts.add(pin ? ref(part, "floor", f) : bodyRef(part));
            y += Boundaries.STRIDE;
        }
        // The tops are alternatives, all conditioned on being at the top, so the mod
        // picks one. Their heights are free above the minimum, because nothing is
        // placed above a top.
        for (int t = 0; t < tops.size(); t++) {
            int height = Math.max(Boundaries.MIN_HEIGHT, tops.get(t));
            if (tops.get(t) < Boundaries.MIN_HEIGHT) {
                warnings.add(name + " top " + (t + 1) + " is set to " + tops.get(t)
                        + " and was read as " + height + ". A part of one slice "
                        + "draws nothing at all, so it is the shortest a top can be.");
            }
            String part = name + "_t" + (t + 1);
            emitPart(part, plot, dx, dz, y, height,
                    Settings.resolve(plotSettings, dx, dz, floors + 1 + t),
                    perPart ? new LinkedHashMap<>() : buildingSink);
            JsonObject r = new JsonObject();
            r.addProperty("part", namespace + ":" + part);
            r.addProperty("top", true);
            parts.add(r);
            y += height;
        }
        warnIfTooTall(name, cellars, floors, tops);

        building.addProperty("filler", settings.has("filler")
                ? paletteValue(string(settings, "filler", String.valueOf(commonest)),
                        name + " filler", buildingSink)
                : String.valueOf(commonest));
        if (commonest == PaletteLedger.AIR && cellars > 0) {
            warnings.add(name + " has cellars and nothing solid on its ground floor, "
                    + "so its filler skirt is air. Set filler on the plot.");
        }
        if (perBuilding) {
            building.add("palette", palette(buildingSink, false));
        }
        building.add("parts", parts);
        putAsset("buildings/" + name, building, plot);
        buildingCount++;
    }

    /** A part that may go on any non-top level. */
    private JsonObject bodyRef(String part) {
        JsonObject r = new JsonObject();
        r.addProperty("part", namespace + ":" + part);
        r.addProperty("top", false);
        return r;
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
     * <p>The height is whatever the caller asked for. A level of a building is
     * never one slice, because one draws nothing there, but that is the building
     * path's rule to apply: a street is one slice and has to stay one.
     */
    private char emitPart(String name, Layout.Plot plot, int dx, int dz,
                          int baseY, int height, JsonObject settings,
                          Map<String, JsonObject> sink) {
        int x0 = plot.blockMinX() + dx * 16;
        int z0 = plot.blockMinZ() + dz * 16;
        JsonObject marks = settings.has("marks") && settings.get("marks").isJsonObject()
                ? settings.getAsJsonObject("marks") : new JsonObject();
        JsonObject conversions = merged("conversions", settings);

        Map<Character, Integer> seen = new LinkedHashMap<>();
        JsonArray slices = new JsonArray();
        for (int y = 0; y < Math.max(1, height); y++) {
            JsonArray layer = new JsonArray();
            for (int z = 0; z < 16; z++) {
                StringBuilder row = new StringBuilder(16);
                for (int x = 0; x < 16; x++) {
                    char c = characterAt(x0 + x, baseY + y, z0 + z,
                            dx * 16 + x, baseY + y, dz * 16 + z, marks, conversions,
                            sink);
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
        // Where this part's characters were put decides how it reaches them. A part
        // with its own palette is readable on its own; one pointing at the pack's
        // shared palette is smaller and changes with it.
        if (sink == cells) {
            part.addProperty("refpalette", namespace + ":main");
        } else if (sink != null) {
            part.add("palette", palette(sink, false));
        }
        part.add("slices", slices);
        putAsset("parts/" + name, part, plot);
        partCount++;
        return seen.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse(PaletteLedger.AIR);
    }

    /** The character for one block, assigning one where the cell is new. */
    private char characterAt(int wx, int wy, int wz, int lx, int ly, int lz,
                             JsonObject marks, JsonObject conversions,
                             Map<String, JsonObject> sink) {
        // ly is the world height the mark was recorded against, not the layer index.
        BlockState state = level.getBlockState(new BlockPos(wx, wy, wz));
        if (state.isAir() || state.is(Blocks.STRUCTURE_VOID)) {
            // Lost Cities has no "leave this alone" character: every position in a
            // slice places something. A structure void therefore becomes air, which
            // is the closest thing the format has.
            return PaletteLedger.AIR;
        }
        String block = PaletteLedger.describe(state);
        String converted = conversions.has(block)
                ? conversions.get(block).getAsString()
                : conversions.has(idOf(state))
                        ? conversions.get(idOf(state)).getAsString() : block;

        JsonObject mark = null;
        String at = lx + "," + (wy - Boundaries.BASE) + "," + lz;
        if (marks.has(at) && marks.get(at).isJsonObject()) {
            mark = marks.getAsJsonObject(at);
        }
        return cell(converted, mark, wx + "," + wy + "," + wz, sink);
    }

    /**
     * The character for one cell, recording the palette entry where it is new.
     *
     * <p>A cell is a block together with whatever was marked on it, because a
     * palette entry is that pair: the same block with a loot table and without one
     * are two entries and two characters.
     */
    private char cell(String block, @Nullable JsonObject mark, String where,
                      Map<String, JsonObject> sink) {
        String key = block + (mark == null ? "" : " " + mark);
        char c = ledger.characterFor(key);
        if (c == 0) {
            warnings.add("Ran out of palette characters at " + where
                    + ". The pool holds " + ledger.capacity() + ".");
            return PaletteLedger.AIR;
        }
        if (!sink.containsKey(key)) {
            JsonObject entry = new JsonObject();
            entry.addProperty("char", String.valueOf(c));
            entry.addProperty("block", block);
            if (mark != null) {
                for (String k : mark.keySet()) {
                    entry.add(k, mark.get(k));
                }
            }
            sink.put(key, entry);
        }
        return c;
    }

    /**
     * A settings value that names a palette character, resolved.
     *
     * <p>{@code filler} and {@code rubble} are characters in the building's palette,
     * and a character only means anything next to the palette it was written for. A
     * block id is therefore the value that survives being carried anywhere: it is
     * looked up here, gets a palette entry if the build did not already use that
     * block, and comes out as this pack's own character. A single character is taken
     * as written, for anyone who knows which one they want.
     */
    private String paletteValue(String value, String where,
                                Map<String, JsonObject> sink) {
        if (value.length() <= 1) {
            return value;
        }
        return String.valueOf(cell(value, null, where, sink));
    }

    /** Where this plot's name goes: a selector, a street shape, or the world style. */
    private void record(Catalogue.Row row, Layout.Plot plot, JsonObject settings,
                        String assetName, String partName) {
        String full = namespace + ":" + assetName;
        if (!row.cityStyleScoped()) {
            String fam = family(row);
            worldParts.computeIfAbsent(fam, k -> new TreeMap<>())
                    .computeIfAbsent(row.key(), k -> new JsonArray())
                    .add(namespace + ":" + partName);
            if (row.kind() == Catalogue.Kind.SINGLE) {
                singleValued.add(fam + "/" + row.key());
            }
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
        assets.put("palettes/main", palette(cells, true));

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
        // What a city style inherits is the author's decision, because selectors
        // accumulate: inheriting citystyle_common adds the mod's eight buildings,
        // twelve multibuildings, parks, bridges and stairs to whatever the workshop
        // holds, and there is no way to write a style that takes the plumbing and
        // leaves the buildings. Standalone writes the plumbing out instead.
        String inherit = string(core, "inherit", "citystyle_common");
        boolean standalone = inherit.isBlank() || "none".equalsIgnoreCase(inherit);

        for (String style : styles) {
            JsonObject city = new JsonObject();
            if (!standalone) {
                city.addProperty("inherit", inherit);
            }
            city.addProperty("style", namespace + ":main");

            JsonObject street = standalone ? streetBlocks() : new JsonObject();
            if (streets.containsKey(style)) {
                JsonObject parts = new JsonObject();
                streets.get(style).forEach(parts::add);
                street.add("parts", parts);
            }
            if (!street.keySet().isEmpty()) {
                city.add("streetblocks", street);
            }
            if (standalone) {
                blockGroups(city);
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

        // A footprint wider than the placement area makes the mod throw rather
        // than skip it, so a pack holding one has to widen the area. Every key in
        // the block is required by the codec once any of it is written, so the
        // defaults are written alongside rather than left to be inferred.
        if (largestMulti > DEFAULT_MULTI_AREASIZE) {
            JsonObject multi = new JsonObject();
            multi.addProperty("areasize", largestMulti);
            multi.addProperty("minimum", 1);
            multi.addProperty("maximum", 5);
            world.add("multisettings", multi);
            warnings.add("The largest multibuilding here is " + largestMulti
                    + " chunks across, wider than the default placement area of "
                    + DEFAULT_MULTI_AREASIZE + ", so the world style widens it. A "
                    + "footprint wider than its area throws during generation.");
        }
        if (!worldParts.isEmpty()) {
            JsonObject parts = new JsonObject();
            worldParts.forEach((fam, shapes) -> {
                JsonObject o = new JsonObject();
                shapes.forEach((key, names) -> {
                    // The monorail keys take one name. Their codec is a plain
                    // string, unlike the highway and railway keys beside them,
                    // which accept either, so a list here is not a longer row: it
                    // is a world style that does not decode and takes everything
                    // else in the file down with it.
                    if (singleValued.contains(fam + "/" + key)) {
                        if (names.size() > 1) {
                            warnings.add(fam + " " + key + " holds one part only, "
                                    + "so " + (names.size() - 1) + " of the "
                                    + names.size() + " built were left out.");
                        }
                        o.addProperty(key, names.get(0).getAsString());
                    } else {
                        o.add(key, names);
                    }
                });
                parts.add(fam, o);
            });
            world.add("parts", parts);
        }
        assets.put("worldstyles/" + string(core, "worldStyle", "main"), world);
    }

    /**
     * The blocks a city style needs that are not parts of anything.
     *
     * <p>The characters are the ones the shipped city styles use, and they resolve
     * because this pack's Style still lists the shipped palettes underneath its own.
     * A standalone style that left these out would generate a road with no kerb and
     * a park with no ground.
     */
    private JsonObject streetBlocks() {
        JsonObject out = new JsonObject();
        out.addProperty("border", "y");
        out.addProperty("wall", "w");
        out.addProperty("street", "S");
        out.addProperty("streetbase", "b");
        out.addProperty("streetvariant", "B");
        out.addProperty("width", 8);
        return out;
    }

    private void blockGroups(JsonObject city) {
        JsonArray tags = new JsonArray();
        tags.add("rubble");
        city.add("stuff_tags", tags);
        city.add("parkblocks", pairs("elevation", "x"));
        city.add("corridorblocks", pairs("roof", "x", "glass", "+"));
        city.add("railblocks", pairs("railmain", "y"));
        city.add("sphereblocks", pairs("glass", "Z", "border", "9", "inner", "b"));
    }

    private static JsonObject pairs(String... keyThenValue) {
        JsonObject out = new JsonObject();
        for (int i = 0; i + 1 < keyThenValue.length; i += 2) {
            out.addProperty(keyThenValue[i], keyThenValue[i + 1]);
        }
        return out;
    }

    /**
     * Record an asset, and refuse to let two plots write the same file.
     *
     * <p>An asset is named by its plot's {@code name} setting, and nothing stops two
     * plots choosing the same one. Without this the second simply replaced the
     * first: the pack came out a file short, the city style listed the surviving
     * name twice, and the plot whose work had gone still looked finished in the
     * workshop. Every part of that is silent, which is what makes it worth an error
     * rather than a warning.
     */
    private void putAsset(String key, JsonObject value, Layout.Plot plot) {
        String first = claimedBy.get(key);
        if (first != null && !first.equals(plot.id())) {
            faults.add(Finding.error(key + ".json", 0,
                    plot.id() + " and " + first + " both compile to " + key,
                    "Two plots cannot write one file. Give one of them a different "
                            + "`name`, or the second would replace the first and "
                            + "everything built on it would be missing from the pack "
                            + "with nothing to say so"));
            return;
        }
        claimedBy.put(key, plot.id());
        assets.put(key, value);
    }

    /**
     * Where a plot asked its characters to be written.
     *
     * <p>{@code global} is the default because it is what a pack usually wants: one
     * place to change a block, one entry per cell however many parts use it, and the
     * ledger keeping the characters steady between exports. {@code part} and
     * {@code building} are for assets meant to be readable, or liftable, on their
     * own.
     */
    private static String placement(JsonObject settings) {
        String value = string(settings, "palette", "global");
        return switch (value) {
            case "part", "building", "global" -> value;
            default -> "global";
        };
    }

    /**
     * A sink, or the shared one.
     *
     * <p>Null means the shared map, which is also the signal {@link #emitPart} reads
     * to decide between a {@code refpalette} and a palette written in the file.
     */
    private Map<String, JsonObject> sinkFor(JsonObject settings,
                                            @Nullable Map<String, JsonObject> own) {
        return own == null ? cells : own;
    }

    /**
     * Palette entries as the format wants them, in character order.
     *
     * <p>The order says nothing, so letting it depend on which plot was read first
     * would make two exports of one workshop differ over nothing, and a round trip
     * cannot tell that kind of difference from a real one.
     *
     * @param withAir the shared palette carries the air entry; a part's own does
     *                not need to, because air is the one character never assigned
     */
    private static JsonObject palette(Map<String, JsonObject> from,
                                      boolean withAir) {
        List<JsonObject> sorted = new ArrayList<>(from.values());
        if (withAir) {
            JsonObject air = new JsonObject();
            air.addProperty("char", String.valueOf(PaletteLedger.AIR));
            air.addProperty("block", "minecraft:air");
            sorted.add(air);
        }
        sorted.sort((a, b) -> Character.compare(charOf(a), charOf(b)));
        JsonArray entries = new JsonArray();
        sorted.forEach(entries::add);
        // An object wrapping the list, whether it stands alone as a palette asset
        // or sits inside a part. The mod's own building7 and park_trees are written
        // this way, and a bare list is read as no palette at all: every character
        // in the asset then resolves to nothing and it draws air.
        JsonObject out = new JsonObject();
        out.add("palette", entries);
        return out;
    }

    private static char charOf(JsonObject entry) {
        String c = entry.has("char") ? entry.get("char").getAsString() : "";
        return c.isEmpty() ? PaletteLedger.AIR : c.charAt(0);
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
        List<Finding> out = new ArrayList<>(faults);
        for (Map.Entry<String, JsonObject> e : assets.entrySet()) {
            String kind = e.getKey().substring(0, e.getKey().indexOf('/'));
            String text = json(e.getValue());
            try {
                out.addAll(AssetValidator.validate(e.getKey() + ".json", kind,
                        e.getValue(), text));
            } catch (RuntimeException ex) {
                // The rules are written to tolerate any shape, and `raw` lets a
                // plot put any shape into an asset, so the two have to be held
                // apart: a rule that trips over one is a fault in the rule, and
                // reporting it as one beats ending the export in a stack trace.
                out.add(Finding.warn(e.getKey() + ".json", 0,
                        "this asset could not be checked: " + ex,
                        "It is written either way. The check itself failed, which "
                                + "is a fault in this mod rather than in the pack"));
            }
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
        // json5 is the mod's own extension for these files, and a pack using it
        // needs this mod present to load at all. Plain JSON is valid JSON5, so what
        // is written is the same text under a different name; the extension is the
        // part that decides which loader reads it.
        String format = string(core, "format", "json");
        boolean json5 = "json5".equalsIgnoreCase(format);
        if (!json5 && !"json".equalsIgnoreCase(format)) {
            warnings.add(format + " is not a format this writes. Use json or json5. "
                    + "Written as json.");
        }
        String ext = json5 ? Json5.EXT_JSON5 : Json5.EXT_JSON;

        Path data = root.resolve("data").resolve(namespace).resolve("lostcities");
        for (Map.Entry<String, JsonObject> e : assets.entrySet()) {
            Path file = data.resolve(e.getKey() + ext);
            Files.createDirectories(file.getParent());
            Files.writeString(file, json(e.getValue()), StandardCharsets.UTF_8);
        }

        JsonObject meta = new JsonObject();
        JsonObject pack = new JsonObject();
        // Asked of the running game rather than written down. 15 is right for
        // 1.20.1 and wrong for every other version, and a datapack declaring the
        // wrong one is refused with a message about the pack being for a newer or
        // older game, which says nothing about the tool that wrote it.
        pack.addProperty("pack_format", SharedConstants.getCurrentVersion()
                .getPackVersion(PackType.SERVER_DATA));
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
