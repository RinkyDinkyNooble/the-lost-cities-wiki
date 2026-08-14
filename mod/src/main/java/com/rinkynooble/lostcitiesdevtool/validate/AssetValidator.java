package com.rinkynooble.lostcitiesdevtool.validate;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.util.ArrayList;
import java.util.List;

/**
 * The rules, applied to one asset file at a time.
 *
 * <p>Every rule here reproduces a failure that has been observed in a running world,
 * and every one of them currently surfaces only during chunk generation, long after
 * the file was read. Checking at load turns a wall of failed chunks into one line
 * naming a file and a line number.
 *
 * <p>Only single-file rules live here. Anything needing the merged view of several
 * assets, such as whether a palette character resolves after inheritance, cannot be
 * decided from one file and is left to generation.
 */
public final class AssetValidator {

    /** Levels a condition can be decided from without knowing anything else. */
    private static final List<String> LEVEL_KEYS =
            List.of("top", "ground", "cellar", "floor", "range");

    private static final List<String> CONDITION_KEYS = List.of(
            "top", "ground", "cellar", "isbuilding", "issphere", "floor",
            "chunkx", "chunkz", "range", "inpart", "belowpart", "inbuilding", "inbiome");

    private AssetValidator() {
    }

    public static List<Finding> validate(String file, String kind, JsonObject json,
                                         String rawText) {
        List<Finding> out = new ArrayList<>();
        switch (kind) {
            case "buildings" -> checkBuilding(out, file, json, rawText);
            case "palettes" -> checkPalette(out, file, json, rawText);
            case "parts" -> checkPart(out, file, json, rawText);
            default -> {
            }
        }
        return out;
    }

    // ---------------------------------------------------------------- buildings

    private static void checkBuilding(List<Finding> out, String file, JsonObject json,
                                      String raw) {
        if (!json.has("filler")) {
            out.add(Finding.error(file, 1, "no 'filler'",
                    "'filler' is required. It is the character used below the building, "
                            + "and it resolves against the BUILDING's palette, not the part's"));
        }
        if (!json.has("parts") || !json.get("parts").isJsonArray()
                || json.getAsJsonArray("parts").isEmpty()) {
            out.add(Finding.error(file, 1, "no 'parts'", "'parts' is required and must not be empty"));
            return;
        }

        JsonArray parts = json.getAsJsonArray("parts");
        boolean hasFallback = false;
        List<String> unprovable = new ArrayList<>();
        List<String> deadReported = new ArrayList<>();

        for (JsonElement e : parts) {
            if (!e.isJsonObject()) {
                continue;
            }
            JsonObject ref = e.getAsJsonObject();

            for (String dead : List.of("inpart", "belowpart")) {
                if (ref.has(dead) && !deadReported.contains(dead)) {
                    deadReported.add(dead);
                    out.add(Finding.error(file, lineOf(raw, dead),
                            "'" + dead + "' in a building's parts list never matches",
                            "The floor loop has no current part yet and passes the literal "
                                    + "<none>, so neither key can match. 'belowpart' also tests "
                                    + "the current part rather than the one below, in every "
                                    + "version that declares it. Select by height with 'floor', "
                                    + "'range', 'ground' and 'top'"));
                }
            }
            if (ref.has("range")) {
                String value = ref.get("range").getAsString();
                if (parseRange(value) == null) {
                    out.add(Finding.error(file, lineOf(raw, "range"),
                            "range \"" + value + "\" does not parse as two integers",
                            "The mod throws 'Bad range specification: " + value + "!'. "
                                    + "Write two integers separated by a comma and no space"));
                } else if (value.split(",").length > 2) {
                    out.add(Finding.warn(file, lineOf(raw, "range"),
                            "range \"" + value + "\" has more than two numbers",
                            "The mod reads the first two and discards the rest, silently. "
                                    + "The floor range in effect is not the one written"));
                }
            }
            boolean conditioned = CONDITION_KEYS.stream().anyMatch(ref::has);
            if (!conditioned) {
                hasFallback = true;
            }
            for (String k : CONDITION_KEYS) {
                if (ref.has(k) && !LEVEL_KEYS.contains(k) && !unprovable.contains(k)) {
                    unprovable.add(k);
                }
            }
        }

        if (hasFallback) {
            return;
        }
        if (!unprovable.isEmpty()) {
            out.add(Finding.error(file, 1,
                    "no unconditioned part reference, and coverage cannot be proven "
                            + "because " + unprovable + " depend on more than the level index",
                    "Add one entry in 'parts' with no condition keys on it"));
            return;
        }

        // A building does not have to declare bounds. Conditions written as top true
        // and top false cover every level at any height, which is what the mod's own
        // content does. So where a bound is declared, check that height; where it is
        // not, check every height the profile could plausibly roll, and report the
        // first that leaves a level uncovered.
        int declaredTop = Math.max(intOr(json, "maxfloors", -1), intOr(json, "minfloors", -1));
        int declaredDeep = Math.max(intOr(json, "maxcellars", -1), intOr(json, "mincellars", -1));

        int topFrom = declaredTop >= 0 ? declaredTop : 0;
        int topTo = declaredTop >= 0 ? declaredTop : PROBED_MAX_FLOORS;
        int deepFrom = declaredDeep >= 0 ? declaredDeep : 0;
        int deepTo = declaredDeep >= 0 ? declaredDeep : PROBED_MAX_CELLARS;

        for (int deepest = deepFrom; deepest <= deepTo; deepest++) {
            for (int top = topFrom; top <= topTo; top++) {
                List<Integer> uncovered = new ArrayList<>();
                for (int level = -deepest; level <= top; level++) {
                    boolean matched = false;
                    for (JsonElement e : parts) {
                        if (e.isJsonObject() && matchesLevel(e.getAsJsonObject(), level, top)) {
                            matched = true;
                            break;
                        }
                    }
                    if (!matched) {
                        uncovered.add(level);
                    }
                }
                if (uncovered.isEmpty()) {
                    continue;
                }
                String at = declaredTop >= 0
                        ? "Levels run -" + deepest + " to " + top + " INCLUSIVE, so "
                          + "'maxfloors': " + top + " is a " + (top + 1) + "-storey building."
                        : "This building declares no floor bounds, so the profile decides "
                          + "the height. At " + (top + 1) + " storeys and " + deepest
                          + " cellars, which the profile can roll, those levels match "
                          + "nothing.";
                out.add(Finding.error(file, lineOf(raw, "parts"),
                        "levels " + uncovered + " match no part",
                        at + " Generation throws 'Misconfiguration! Floor were generated "
                           + "for a building where no part condition matches!', and every "
                           + "chunk that queries this one fails the same way"));
                return;
            }
        }
    }

    /** The profile's own maximums, used when a building declares no bounds. */
    private static final int PROBED_MAX_FLOORS = 20;
    private static final int PROBED_MAX_CELLARS = 3;

    /** Tests chain with AND, never OR. */
    private static boolean matchesLevel(JsonObject ref, int level, int topIndex) {
        if (ref.has("ground") && (level == 0) != ref.get("ground").getAsBoolean()) {
            return false;
        }
        if (ref.has("top") && (level >= topIndex) != ref.get("top").getAsBoolean()) {
            return false;
        }
        if (ref.has("cellar") && (level < 0) != ref.get("cellar").getAsBoolean()) {
            return false;
        }
        if (ref.has("floor") && level != ref.get("floor").getAsInt()) {
            return false;
        }
        if (ref.has("range")) {
            int[] bounds = parseRange(ref.get("range").getAsString());
            return bounds != null && level >= bounds[0] && level <= bounds[1];
        }
        return true;
    }

    private static int[] parseRange(String text) {
        String[] pieces = text.split(",");
        if (pieces.length < 2) {
            return null;
        }
        try {
            return new int[]{Integer.parseInt(pieces[0]), Integer.parseInt(pieces[1])};
        } catch (NumberFormatException e) {
            return null;
        }
    }

    // ----------------------------------------------------------------- palettes

    private static void checkPalette(List<Finding> out, String file, JsonObject json,
                                     String raw) {
        if (!json.has("palette") || !json.get("palette").isJsonArray()) {
            return;
        }
        for (JsonElement e : json.getAsJsonArray("palette")) {
            if (!e.isJsonObject()) {
                continue;
            }
            JsonObject entry = e.getAsJsonObject();
            String c = entry.has("char") ? entry.get("char").getAsString() : null;
            if (c == null || c.isEmpty()) {
                out.add(Finding.error(file, lineOf(raw, "char"), "palette entry with no 'char'",
                        "An empty 'char' throws at load with a string index out of range"));
                continue;
            }
            char key = c.charAt(0);
            if (Character.isSurrogate(key)) {
                out.add(Finding.error(file, lineOf(raw, "\"" + c + "\""),
                        "char " + quoted(c) + " starts above U+FFFF",
                        "The mod keeps the leading surrogate only, so every character in the "
                                + "same block of 1024 collapses onto one key. In a part's slices "
                                + "it also occupies two positions and shifts the layer"));
            } else if (c.length() > 1) {
                out.add(Finding.warn(file, lineOf(raw, "\"" + c + "\""),
                        "char " + quoted(c) + " is " + c.length() + " characters",
                        "The mod registers '" + key + "' and discards the rest, silently"));
            }

            for (String k : List.of("loot", "mob")) {
                if (entry.has(k) && entry.get(k).getAsString().contains("/")) {
                    String v = entry.get(k).getAsString();
                    out.add(Finding.error(file, lineOf(raw, k),
                            "'" + k + "': \"" + v + "\" looks like an ID, but '" + k
                                    + "' names a Condition",
                            "Wrap it in a one-entry condition and name that. Generation throws "
                                    + "'Error getting resource " + v + "!' during the "
                                    + "post-generation pass, which leaves chests that open, are "
                                    + "empty, and render invisible"));
                }
            }

            if (entry.has("blocks") && entry.get("blocks").isJsonArray()) {
                checkWeightedList(out, file, raw, quoted(c), entry.getAsJsonArray("blocks"));
            }
        }
    }

    /** A weighted list fills a fixed array of 128 slots, in list order. */
    private static void checkWeightedList(List<Finding> out, String file, String raw,
                                          String label, JsonArray blocks) {
        int total = 0;
        int running = 0;
        for (int i = 0; i < blocks.size(); i++) {
            JsonObject b = blocks.get(i).getAsJsonObject();
            int weight = b.has("random") ? b.get("random").getAsInt() : 0;
            if (running >= 128) {
                out.add(Finding.error(file, lineOf(raw, b.has("block")
                                ? b.get("block").getAsString() : "random"),
                        "char " + label + " entry " + i + " is unreachable, 128 slots "
                                + "already filled",
                        "The list fills 128 slots in order. Put the large catch-all entry "
                                + "last, which is the mod's own idiom"));
                break;
            }
            running += weight;
            total += weight;
        }
        if (total < 128) {
            out.add(Finding.error(file, lineOf(raw, "blocks"),
                    "char " + label + " weighted list totals " + total + ", must reach 128",
                    "The mod throws 'Not enough blocks in the random list'. Add a catch-all "
                            + "entry last with a large weight"));
        }
    }

    // -------------------------------------------------------------------- parts

    private static void checkPart(List<Finding> out, String file, JsonObject json,
                                  String raw) {
        int xsize = intOr(json, "xsize", -1);
        int zsize = intOr(json, "zsize", -1);
        if (xsize <= 0 || zsize <= 0 || !json.has("slices")) {
            return;
        }
        if (json.has("metadata")) {
            out.add(Finding.error(file, lineOf(raw, "metadata"), "key is 'meta', not 'metadata'",
                    "'metadata' parses into nothing and is never read"));
        }
        JsonArray slices = json.getAsJsonArray("slices");
        int expected = xsize * zsize;
        for (int y = 0; y < slices.size(); y++) {
            if (!slices.get(y).isJsonArray()) {
                continue;
            }
            JsonArray layer = slices.get(y).getAsJsonArray();
            int units = 0;
            for (JsonElement row : layer) {
                units += row.getAsString().length();
            }
            if (units == expected) {
                continue;
            }
            // A layer is read as one flat string, charAt(z * xsize + x), so row breaks
            // in the JSON are formatting and only the total matters.
            String detail = "layer " + y + " holds " + units + " characters, expected "
                    + expected + " (" + xsize + " x " + zsize + ")";
            if (units < expected) {
                out.add(Finding.error(file, lineOf(raw, firstRow(layer)), detail,
                        "Generation fails the chunk with 'String index out of range: "
                                + (expected - 1) + "'"));
            } else {
                out.add(Finding.error(file, lineOf(raw, firstRow(layer)), detail,
                        "Too many characters is silent. Everything after the extra one "
                                + "shifts along, and the tail past position " + (expected - 1)
                                + " is never read"));
            }
        }
    }

    private static String firstRow(JsonArray layer) {
        return layer.isEmpty() ? "slices" : layer.get(0).getAsString();
    }

    // ------------------------------------------------------------------- helpers

    private static int intOr(JsonObject json, String key, int fallback) {
        return json.has(key) ? json.get(key).getAsInt() : fallback;
    }

    private static String quoted(String s) {
        return "'" + s + "'";
    }

    /**
     * The line a token first appears on.
     *
     * <p>A parsed {@code JsonObject} carries no position, so the line is recovered by
     * searching the source text. It points at the right area rather than at an exact
     * token, which is enough for an editor to jump to.
     */
    static int lineOf(String raw, String needle) {
        if (raw == null || needle == null || needle.isEmpty()) {
            return 0;
        }
        int at = raw.indexOf(needle);
        if (at < 0) {
            return 0;
        }
        int line = 1;
        for (int i = 0; i < at; i++) {
            if (raw.charAt(i) == '\n') {
                line++;
            }
        }
        return line;
    }
}
