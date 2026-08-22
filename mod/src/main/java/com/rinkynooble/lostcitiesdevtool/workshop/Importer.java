package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import javax.annotation.Nullable;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * The other direction: a loaded pack, pasted into the workshop.
 *
 * <p>Starts from a world style and follows the references the way generation does:
 * city styles, then their selectors and street shapes, then the buildings those name,
 * then the parts those stack, then the palettes those resolve through. Every asset
 * that lands somewhere gets a plot, and every plot gets the settings that would
 * export it back again.
 *
 * <p><b>Rows grow to fit.</b> A row starts at three plots because that is a sensible
 * catalogue, not because a pack holds three of anything. The one exception is a row
 * the codec allows a single value for: a monorail row stays at one plot however many
 * the pack has, because a list there is a load error rather than a bigger row.
 */
public final class Importer {

    /** How many alternatives of an unpinned building a plot shows at most. */
    private static final int MAX_SHOWN = 8;

    public record Result(String worldStyle, int assets, int plots, int blocks,
                         int unpinned, Map<String, Integer> grown,
                         List<String> warnings) {
    }

    private final MinecraftServer server;
    private final ServerLevel level;
    private final Assets assets;
    private final Map<String, String> reverse;
    private final List<String> warnings = new ArrayList<>();

    /** row id -> the asset names bound for it, in the order they were found. */
    private final Map<String, List<String>> queued = new LinkedHashMap<>();
    /** asset name -> the city styles that referenced it. */
    private final Map<String, Set<String>> owners = new LinkedHashMap<>();
    /** asset name -> the selector entry it came from, for factor and distances. */
    private final Map<String, JsonObject> entries = new LinkedHashMap<>();
    /** asset name -> the Style whose palettes its characters resolve through. */
    private final Map<String, String> styleOf = new LinkedHashMap<>();
    /** Style name -> its merged palette, built once. */
    private final Map<String, Map<Character, BlockState>> stylePalettes =
            new LinkedHashMap<>();

    /** For parts that belong to no city style: highways, railways, monorails. */
    private String outsideStyle = "outside";

    private int blocks;
    private int unpinned;

    private Importer(MinecraftServer server, ServerLevel level, Assets assets,
                     Map<String, String> reverse) {
        this.server = server;
        this.level = level;
        this.assets = assets;
        this.reverse = reverse;
    }

    // -------------------------------------------------------------------- entry

    public static Result run(MinecraftServer server, ServerLevel level,
                             String worldStyleName, boolean reverseConversions)
            throws IOException {
        Assets loaded = Assets.load(server);
        JsonObject world = loaded.get("worldstyles", worldStyleName);
        if (world == null) {
            throw new IOException("no world style named " + worldStyleName
                    + " is loaded. /lcdev import lists what is");
        }
        Map<String, String> reverse = reverseConversions
                ? reverseTable(SettingsStore.load(server, Layout.CORE_ID))
                : Map.of();

        Importer importer = new Importer(server, level, loaded, reverse);
        importer.walk(world);
        importer.growRows();
        int plots = importer.paste();
        Workshop.build(level);
        return new Result(worldStyleName, importer.queued.values().stream()
                .mapToInt(List::size).sum(), plots, importer.blocks,
                importer.unpinned, Layout.grown(), importer.warnings);
    }

    /** Every world style the server has loaded, for tab completion. */
    public static List<String> worldStyles(MinecraftServer server) {
        return new ArrayList<>(Assets.load(server).folder("worldstyles").keySet());
    }

    /**
     * The block conversion table, inverted.
     *
     * <p>An export turns a placeholder into the real block. An import has to turn it
     * back, or the first round trip loses every placeholder somebody used to stand
     * in for a block that is hard to place by hand.
     */
    private static Map<String, String> reverseTable(JsonObject core) {
        Map<String, String> out = new HashMap<>();
        if (core.has("conversions") && core.get("conversions").isJsonObject()) {
            JsonObject table = core.getAsJsonObject("conversions");
            for (String from : table.keySet()) {
                out.put(table.get(from).getAsString(), from);
            }
        }
        return out;
    }

    // --------------------------------------------------------------------- walk

    private void walk(JsonObject world) {
        if (world.has("outsidestyle")) {
            outsideStyle = world.get("outsidestyle").getAsString();
        }
        for (JsonElement e : array(world, "citystyles")) {
            if (!e.isJsonObject() || !e.getAsJsonObject().has("citystyle")) {
                continue;
            }
            walkCityStyle(e.getAsJsonObject().get("citystyle").getAsString());
        }
        JsonObject parts = object(world, "parts");
        if (parts != null) {
            walkFamily(parts, "highways", "highway");
            walkFamily(parts, "railways", "railway");
            walkFamily(parts, "monorails", "monorail");
        }
    }

    private void walkCityStyle(String name) {
        JsonObject style = assets.cityStyle(name);
        if (style == null) {
            warnings.add("city style " + name + " is referenced and not loaded");
            return;
        }
        String shortName = name.contains(":") ? name.substring(name.indexOf(':') + 1)
                : name;
        // Where this style's characters come from. A part in the mod's own pack
        // carries no palette of its own at all: every character it draws is defined
        // in the Style the city style names, and a part read without it is a grid of
        // characters that resolve to nothing.
        String styleName = style.has("style")
                ? style.get("style").getAsString() : "standard";

        JsonObject selectors = object(style, "selectors");
        if (selectors != null) {
            for (String key : selectors.keySet()) {
                String rowId = "buildings".equals(key) ? "building/1x1"
                        : "multibuildings".equals(key) ? null
                                : "selector/" + key;
                for (JsonElement e : selectors.getAsJsonArray(key)) {
                    if (!e.isJsonObject() || !e.getAsJsonObject().has("value")) {
                        continue;
                    }
                    JsonObject entry = e.getAsJsonObject();
                    String value = entry.get("value").getAsString();
                    String target = rowId != null ? rowId : multiRow(value);
                    if (target == null || Catalogue.row(target) == null) {
                        continue;
                    }
                    queue(target, value);
                    entries.put(value, entry);
                    styleOf.put(value, styleName);
                    owners.computeIfAbsent(value, k -> new LinkedHashSet<>())
                            .add(shortName);
                }
            }
        }

        JsonObject street = object(style, "streetblocks");
        JsonObject streetParts = street == null ? null : object(street, "parts");
        if (streetParts != null) {
            for (String shape : streetParts.keySet()) {
                String rowId = "street/" + shape;
                if (Catalogue.row(rowId) == null) {
                    continue;
                }
                for (String part : names(streetParts.get(shape))) {
                    queue(rowId, part);
                    styleOf.put(part, styleName);
                    owners.computeIfAbsent(part, k -> new LinkedHashSet<>())
                            .add(shortName);
                }
            }
        }
    }

    /** Which multibuilding row a name belongs in, from the footprint it declares. */
    @Nullable
    private String multiRow(String name) {
        JsonObject multi = assets.get("multibuildings", name);
        if (multi == null) {
            warnings.add("multibuilding " + name + " is referenced and not loaded");
            return null;
        }
        int w = intOf(multi, "dimx", 1);
        int h = intOf(multi, "dimz", 1);
        String id = "multibuilding/" + w + "x" + h;
        if (Catalogue.row(id) == null) {
            warnings.add(name + " is " + w + "x" + h + ", which the catalogue has no "
                    + "row for. Add one and import again.");
            return null;
        }
        return id;
    }

    private void walkFamily(JsonObject parts, String family, String prefix) {
        JsonObject shapes = object(parts, family);
        if (shapes == null) {
            return;
        }
        for (String shape : shapes.keySet()) {
            String rowId = prefix + "/" + shape;
            if (Catalogue.row(rowId) == null) {
                continue;
            }
            for (String part : names(shapes.get(shape))) {
                queue(rowId, part);
            }
        }
    }

    private void queue(String rowId, String name) {
        List<String> list = queued.computeIfAbsent(rowId, k -> new ArrayList<>());
        if (!list.contains(name)) {
            list.add(name);
        }
    }

    private void growRows() {
        for (Map.Entry<String, List<String>> e : queued.entrySet()) {
            Catalogue.Row row = Catalogue.row(e.getKey());
            if (row == null) {
                continue;
            }
            if (row.kind() == Catalogue.Kind.SINGLE && e.getValue().size() > 1) {
                warnings.add(row.id() + " holds one variation only, so "
                        + (e.getValue().size() - 1) + " of the "
                        + e.getValue().size() + " the pack has were left out.");
                continue;
            }
            Layout.grow(row.id(), e.getValue().size());
        }
    }

    // -------------------------------------------------------------------- paste

    private int paste() throws IOException {
        Map<String, Layout.Plot> byId = new HashMap<>();
        for (Layout.Plot plot : Layout.plots()) {
            byId.put(plot.id(), plot);
        }
        int used = 0;
        for (Map.Entry<String, List<String>> e : queued.entrySet()) {
            Catalogue.Row row = Catalogue.row(e.getKey());
            List<String> names = e.getValue();
            int limit = row != null && row.kind() == Catalogue.Kind.SINGLE
                    ? Math.min(1, names.size()) : names.size();
            for (int i = 0; i < limit; i++) {
                Layout.Plot plot = byId.get(e.getKey() + "/" + i);
                if (plot == null) {
                    warnings.add("no plot for " + e.getKey() + "/" + i);
                    continue;
                }
                pasteOne(plot, names.get(i));
                used++;
            }
        }
        return used;
    }

    private void pasteOne(Layout.Plot plot, String name) throws IOException {
        JsonObject settings = new JsonObject();
        settings.addProperty("name", shortOf(name));
        Set<String> styles = owners.get(name);
        if (styles != null && plot.row() != null && plot.row().cityStyleScoped()) {
            JsonArray list = new JsonArray();
            styles.forEach(list::add);
            settings.add("citystyles", list);
        }
        JsonObject entry = entries.get(name);
        if (entry != null) {
            for (String key : List.of("factor", "feather", "minSpawnDistance",
                    "maxSpawnDistance")) {
                if (entry.has(key)) {
                    settings.add(key, entry.get(key));
                }
            }
        }

        String styleName = styleOf.getOrDefault(name, outsideStyle);
        JsonObject building = assets.get("buildings", name);
        JsonObject multi = assets.get("multibuildings", name);
        if (multi != null) {
            pasteMulti(plot, multi, settings, styleName);
        } else if (building != null) {
            pasteBuilding(plot, 0, 0, building, settings, styleName);
        } else {
            JsonObject part = assets.get("parts", name);
            if (part == null) {
                warnings.add("nothing named " + name + " is loaded, so "
                        + plot.id() + " is empty");
                return;
            }
            int height = pastePart(plot, 0, 0, Boundaries.BASE, part, styleName, null);
            settings.addProperty("height", height);
        }
        SettingsStore.save(server, plot.id(), plot.row(), settings);
    }

    /**
     * A multibuilding, chunk by chunk.
     *
     * <p>The grid is {@code buildings[x][z]}: <b>the outer list is the X axis</b> and
     * the inner list is Z. It is not laid out the way it looks, and reading it the
     * other way round pastes a structure that is transposed against the one the pack
     * generates.
     */
    private void pasteMulti(Layout.Plot plot, JsonObject multi, JsonObject settings,
                            String styleName) throws IOException {
        JsonElement grid = multi.get("buildings");
        if (grid == null || !grid.isJsonArray()) {
            warnings.add("a multibuilding has no buildings grid");
            return;
        }
        JsonArray columns = grid.getAsJsonArray();
        int first = 0;
        for (int dx = 0; dx < plot.width() && dx < columns.size(); dx++) {
            JsonElement column = columns.get(dx);
            List<String> down = names(column);
            for (int dz = 0; dz < plot.height() && dz < down.size(); dz++) {
                JsonObject b = assets.get("buildings", down.get(dz));
                if (b != null) {
                    pasteBuilding(plot, dx, dz, b,
                            first++ == 0 ? settings : new JsonObject(), styleName);
                }
            }
        }
    }

    /**
     * One building, level by level.
     *
     * <p>Where several parts match a level the mod picks at random. An import cannot,
     * so it takes the first that matches, which is one of the buildings the pack
     * would have produced rather than an average of them. Anything the settings
     * schema cannot express about the choice is lost, and that is the honest limit
     * of pasting a random thing into a fixed place.
     */
    private void pasteBuilding(Layout.Plot plot, int dx, int dz, JsonObject building,
                               JsonObject settings, String styleName) {
        JsonArray parts = building.has("parts") && building.get("parts").isJsonArray()
                ? building.getAsJsonArray("parts") : new JsonArray();

        // A building that pins no count is a bag of interchangeable floors, which is
        // how the mod's own are written: no bounds, and every part conditioned
        // `top: false`. A plot is a fixed place and has to show something, so it
        // shows the alternatives one above the other, which is what the building can
        // be made of. pinFloors keeps the export from writing a count back.
        boolean pinned = intOf(building, "maxfloors", -1) >= 0;
        List<JsonObject> bag = new ArrayList<>();
        for (JsonElement e : parts) {
            if (e.isJsonObject() && e.getAsJsonObject().has("part")
                    && !bool(e.getAsJsonObject(), "top", false)) {
                bag.add(e.getAsJsonObject());
            }
        }
        int floors = pinned ? Math.max(intOf(building, "maxfloors", 0), 0)
                : Math.max(0, Math.min(bag.size(), MAX_SHOWN) - 1);
        int cellars = Math.max(intOf(building, "maxcellars", -1), 0);

        settings.addProperty("floors", floors);
        settings.addProperty("cellars", cellars);
        settings.addProperty("pinFloors", pinned);
        if (!pinned) {
            unpinned++;
        }
        if (building.has("filler")) {
            settings.addProperty("filler", building.get("filler").getAsString());
        }
        if (building.has("rubble")) {
            settings.addProperty("rubble", building.get("rubble").getAsString());
        }
        if (building.has("preferslonely")) {
            settings.add("preferslonely", building.get("preferslonely"));
        }

        int y = Boundaries.BASE;
        for (int level = -cellars; level <= floors; level++) {
            // Unpinned, walk the bag rather than taking the same entry every time:
            // eight identical floors would hide the eight parts the pack holds.
            JsonObject ref = !pinned && level >= 0 && !bag.isEmpty()
                    ? bag.get(level % bag.size())
                    : firstMatching(parts, level, floors);
            if (ref != null) {
                JsonObject part = assets.get("parts",
                        ref.get("part").getAsString());
                if (part != null) {
                    pastePart(plot, dx, dz, y, part, styleName, building);
                }
            }
            y += Boundaries.STRIDE;
        }

        // Anything conditioned on the top that was not used for a level is an
        // alternative roof. They stack in the plot, which is how the workshop shows
        // alternatives, and their heights go into the settings so the export can cut
        // them apart again.
        JsonArray tops = new JsonArray();
        boolean firstTop = true;
        for (JsonElement e : parts) {
            if (!e.isJsonObject()) {
                continue;
            }
            JsonObject ref = e.getAsJsonObject();
            if (!bool(ref, "top", false)) {
                continue;
            }
            if (firstTop) {
                // The first `top` entry was already drawn as the topmost level.
                firstTop = false;
                continue;
            }
            JsonObject part = assets.get("parts", ref.get("part").getAsString());
            if (part == null) {
                continue;
            }
            int height = pastePart(plot, dx, dz, y, part, styleName, building);
            tops.add(height);
            y += height;
        }
        if (!tops.isEmpty()) {
            settings.add("tops", tops);
        }
    }

    /** The first part reference that applies to a level, matching the mod's tests. */
    @Nullable
    private JsonObject firstMatching(JsonArray parts, int level, int floors) {
        for (JsonElement e : parts) {
            if (!e.isJsonObject()) {
                continue;
            }
            JsonObject ref = e.getAsJsonObject();
            if (!ref.has("part")) {
                continue;
            }
            if (ref.has("top") && ref.get("top").getAsBoolean() != (level >= floors)) {
                continue;
            }
            if (ref.has("ground")
                    && ref.get("ground").getAsBoolean() != (level == 0)) {
                continue;
            }
            if (ref.has("cellar") && ref.get("cellar").getAsBoolean() != (level < 0)) {
                continue;
            }
            if (ref.has("floor") && ref.get("floor").getAsInt() != level) {
                continue;
            }
            if (ref.has("range")) {
                int[] r = range(ref.get("range").getAsString());
                if (r == null || level < r[0] || level > r[1]) {
                    continue;
                }
            }
            return ref;
        }
        return null;
    }

    @Nullable
    private static int[] range(String text) {
        String[] halves = text.split(",");
        if (halves.length != 2) {
            return null;
        }
        try {
            return new int[]{Integer.parseInt(halves[0].trim()),
                    Integer.parseInt(halves[1].trim())};
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /** Draw a part into the world. Returns how tall it was. */
    private int pastePart(Layout.Plot plot, int dx, int dz, int baseY,
                          JsonObject part, String styleName,
                          @Nullable JsonObject building) {
        Map<Character, BlockState> palette = paletteFor(part, styleName, building);
        JsonArray slices = part.has("slices") && part.get("slices").isJsonArray()
                ? part.getAsJsonArray("slices") : new JsonArray();
        int x0 = plot.blockMinX() + dx * 16;
        int z0 = plot.blockMinZ() + dz * 16;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();

        for (int y = 0; y < slices.size(); y++) {
            List<String> rows = rowsOf(slices.get(y));
            for (int z = 0; z < 16; z++) {
                String row = z < rows.size() ? rows.get(z) : "";
                for (int x = 0; x < 16; x++) {
                    char c = x < row.length() ? row.charAt(x) : ' ';
                    BlockState state = palette.get(c);
                    pos.set(x0 + x, baseY + y, z0 + z);
                    level.setBlock(pos, state == null
                            ? Blocks.AIR.defaultBlockState() : state, 2);
                    blocks++;
                }
            }
        }
        return slices.size();
    }

    /**
     * A part's characters, resolved in the order the mod merges them.
     *
     * <p>The Style's palettes first, then the building's, then the part's, each one
     * overwriting the last. The style is not optional: a part in the mod's own pack
     * carries no palette at all, and reading one without its style gives a grid of
     * characters that resolve to nothing and a plot that pastes as air.
     *
     * <p>A Style rolls one palette per group per chunk. An import cannot roll, so it
     * takes the first choice in each group. That is one of the buildings the pack
     * would have made rather than an average of them, which is the same compromise
     * pasting anything random into a fixed place makes.
     */
    private Map<Character, BlockState> paletteFor(JsonObject part, String styleName,
                                                  @Nullable JsonObject building) {
        Map<Character, BlockState> out = new HashMap<>(stylePalette(styleName));
        out.put(' ', Blocks.AIR.defaultBlockState());
        if (building != null) {
            if (building.has("refpalette")) {
                JsonObject named = assets.get("palettes",
                        building.get("refpalette").getAsString());
                if (named != null) {
                    readPalette(named, out);
                }
            }
            if (building.has("palette") && building.get("palette").isJsonObject()) {
                readPalette(building.getAsJsonObject("palette"), out);
            }
        }
        if (part.has("refpalette")) {
            JsonObject named = assets.get("palettes",
                    part.get("refpalette").getAsString());
            if (named != null) {
                readPalette(named, out);
            }
        }
        if (part.has("palette") && part.get("palette").isJsonObject()) {
            readPalette(part.getAsJsonObject("palette"), out);
        }
        return out;
    }

    private Map<Character, BlockState> stylePalette(String styleName) {
        Map<Character, BlockState> have = stylePalettes.get(styleName);
        if (have != null) {
            return have;
        }
        Map<Character, BlockState> out = new HashMap<>();
        JsonObject style = assets.get("styles", styleName);
        if (style == null) {
            warnings.add("style " + styleName + " is referenced and not loaded, so "
                    + "the parts using it pasted as air");
        } else {
            for (JsonElement group : array(style, "randompalettes")) {
                if (!group.isJsonArray() || group.getAsJsonArray().isEmpty()) {
                    continue;
                }
                JsonElement first = group.getAsJsonArray().get(0);
                if (!first.isJsonObject() || !first.getAsJsonObject().has("palette")) {
                    continue;
                }
                JsonObject palette = assets.get("palettes",
                        first.getAsJsonObject().get("palette").getAsString());
                if (palette != null) {
                    readPalette(palette, out);
                }
            }
        }
        stylePalettes.put(styleName, out);
        return out;
    }

    private void readPalette(JsonObject palette, Map<Character, BlockState> into) {
        for (JsonElement e : array(palette, "palette")) {
            if (!e.isJsonObject()) {
                continue;
            }
            JsonObject entry = e.getAsJsonObject();
            if (!entry.has("char")) {
                continue;
            }
            String ch = entry.get("char").getAsString();
            if (ch.isEmpty()) {
                continue;
            }
            BlockState state = representative(entry);
            if (state == null && entry.has("frompalette")) {
                // An alias copies another character's resolved value, and resolves
                // once when the palettes merge rather than per placement.
                String from = entry.get("frompalette").getAsString();
                if (!from.isEmpty()) {
                    state = into.get(from.charAt(0));
                }
            }
            if (state != null) {
                into.put(ch.charAt(0), state);
            }
        }
    }

    /**
     * One block for a palette entry.
     *
     * <p>A weighted list has no single answer, so the first entry stands for it. The
     * workshop shows one instance of a thing that varies, which is the same
     * compromise pasting a random building at all makes.
     */
    @Nullable
    private BlockState representative(JsonObject entry) {
        if (entry.has("block")) {
            return parse(entry.get("block").getAsString());
        }
        if (entry.has("blocks") && entry.get("blocks").isJsonArray()) {
            for (JsonElement e : entry.getAsJsonArray("blocks")) {
                if (e.isJsonObject() && e.getAsJsonObject().has("block")) {
                    return parse(e.getAsJsonObject().get("block").getAsString());
                }
            }
        }
        if (entry.has("variant")) {
            JsonObject variant = assets.get("variants",
                    entry.get("variant").getAsString());
            if (variant != null) {
                for (JsonElement e : array(variant, "blocks")) {
                    if (e.isJsonObject() && e.getAsJsonObject().has("block")) {
                        return parse(e.getAsJsonObject().get("block").getAsString());
                    }
                }
            }
        }
        return null;
    }

    @Nullable
    private BlockState parse(String description) {
        String wanted = reverse.getOrDefault(description, description);
        try {
            return BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK.asLookup(),
                    wanted, false).blockState();
        } catch (CommandSyntaxException e) {
            // A shipped palette carries at least one 1.12 block id with an @meta
            // suffix that has never been valid here. Saying so once is useful;
            // failing the import over somebody else's bug is not.
            warnings.add("could not read the block '" + wanted + "', left as air");
            return null;
        }
    }

    // ----------------------------------------------------------------- plumbing

    private static List<String> rowsOf(JsonElement layer) {
        List<String> out = new ArrayList<>();
        if (layer.isJsonArray()) {
            layer.getAsJsonArray().forEach(e -> out.add(e.getAsString()));
        } else if (layer.isJsonPrimitive()) {
            // One string per layer is the shape the mod holds internally.
            String all = layer.getAsString();
            for (int i = 0; i + 16 <= all.length(); i += 16) {
                out.add(all.substring(i, i + 16));
            }
        }
        return out;
    }

    /** A name, or a list of them: three families accept either. */
    private static List<String> names(@Nullable JsonElement e) {
        List<String> out = new ArrayList<>();
        if (e == null || e.isJsonNull()) {
            return out;
        }
        if (e.isJsonArray()) {
            e.getAsJsonArray().forEach(x -> out.add(x.getAsString()));
        } else {
            out.add(e.getAsString());
        }
        return out;
    }

    private static String shortOf(String name) {
        return name.contains(":") ? name.substring(name.indexOf(':') + 1) : name;
    }

    private static JsonArray array(JsonObject o, String key) {
        return o.has(key) && o.get(key).isJsonArray()
                ? o.getAsJsonArray(key) : new JsonArray();
    }

    @Nullable
    private static JsonObject object(JsonObject o, String key) {
        return o.has(key) && o.get(key).isJsonObject()
                ? o.getAsJsonObject(key) : null;
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
}
