package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * What a plot's settings may hold, and how the three scopes fold together.
 *
 * <p>The schema is here rather than in the file format, so a command can complete a
 * key name, reject a bad value with a reason, and explain what a key is for without
 * anybody opening a wiki. The file is the truth; this is what makes the file
 * writable from inside the game.
 *
 * <p><b>Which fields a plot has depends on what the plot is.</b> A street plot has no
 * weight, because the codec behind it picks uniform random and has nowhere to put
 * one. A monorail plot has no variation index worth setting, because the codec takes
 * a string. Offering every field everywhere would teach the format wrong.
 */
public final class Settings {

    public enum Type { STRING, CHAR, INT, FLOAT, BOOL, STRING_LIST, INT_LIST }

    /** Which plots a field belongs to. */
    public enum Applies {
        /** Every catalogue plot, but not the front desk. */
        SHAPE,
        /** The front desk at the origin. */
        CORE,
        /** Plots that become a Building or a MultiBuilding. */
        BUILDING,
        /** Plots whose entry carries a `factor`, so every ObjectSelector row. */
        WEIGHTED,
        /** Plots whose names land in a city style, so the style has to be named. */
        CITY_SCOPED,
        /** Plots that are one part rather than a stack of them. */
        FLAT
    }

    /**
     * @param fallback what the exporter uses when the key is unset, as text. Null
     *                 where there is no sensible default and the export will ask.
     */
    public record Field(String name, Type type, Applies applies,
                        @Nullable String fallback, String help) {
    }

    private static final List<Field> FIELDS = List.of(
            // ---------------------------------------------------------- the desk
            new Field("namespace", Type.STRING, Applies.CORE, "mypack",
                    "The datapack namespace every asset is written under. A bare "
                            + "reference elsewhere means lostcities:, never this, so "
                            + "every name this pack emits is written in full."),
            new Field("packName", Type.STRING, Applies.CORE, "My City",
                    "The pack's display name, for pack.mcmeta."),
            new Field("description", Type.STRING, Applies.CORE, "",
                    "The pack description, for pack.mcmeta."),
            new Field("worldStyle", Type.STRING, Applies.CORE, "main",
                    "The name of the world style this pack emits. A profile points "
                            + "at exactly one, and it is the join between config and "
                            + "datapack."),
            new Field("format", Type.STRING, Applies.CORE, "json",
                    "json or json5. json5 keeps comments and trailing commas, and "
                            + "needs this mod to load."),

            // --------------------------------------------------------- every plot
            new Field("name", Type.STRING, Applies.SHAPE, null,
                    "The asset name. Defaults to the plot's own id with the slashes "
                            + "replaced, which is unique but not memorable."),
            new Field("skip", Type.BOOL, Applies.SHAPE, "false",
                    "Leave this plot out of the export entirely, without deleting "
                            + "what is built on it."),
            new Field("palette", Type.STRING, Applies.SHAPE, "part",
                    "Where this plot's palette goes. part gives every part its own, "
                            + "building gives the whole building one, global puts "
                            + "everything in the pack's shared palette."),

            // ------------------------------------------------------- city styles
            new Field("citystyles", Type.STRING_LIST, Applies.CITY_SCOPED, null,
                    "Which city styles this belongs to. Streets, buildings, parks "
                            + "and the rest live on a city style, so a pack with two "
                            + "styles needs to say which. Highways, railways and "
                            + "monorails have no such key: they live on the world "
                            + "style, and a pack has one."),

            // ----------------------------------------------------------- weights
            new Field("factor", Type.FLOAT, Applies.WEIGHTED, "1.0",
                    "The weight of this variation against the others in the same "
                            + "selector. Relative to its siblings, not to 1."),
            new Field("minSpawnDistance", Type.INT, Applies.WEIGHTED, null,
                    "Blocks from the origin below which the weight is zero. Stops "
                            + "working past about 46,000 blocks, where the mod's "
                            + "squared distance overflows a 32-bit int."),
            new Field("maxSpawnDistance", Type.INT, Applies.WEIGHTED, null,
                    "Blocks from the origin above which the weight is zero. Same "
                            + "overflow applies."),
            new Field("feather", Type.INT, Applies.WEIGHTED, null,
                    "The width of the fade band at both edges of the distance "
                            + "window. Zero is a hard cutoff."),

            // --------------------------------------------------------- buildings
            new Field("floors", Type.INT, Applies.BUILDING, "1",
                    "Levels above ground, not counting the ground floor. The stride "
                            + "is always 6 blocks whatever a part's height is."),
            new Field("cellars", Type.INT, Applies.BUILDING, "0",
                    "Levels below ground. Note the profile's own maximum is a base "
                            + "and not a cap: the chunk's city level is added to it."),
            new Field("tops", Type.INT_LIST, Applies.BUILDING, null,
                    "The height in blocks of each top variation, read upward from "
                            + "where the floors stop. They are alternatives, not a "
                            + "stack: the mod picks one. Free height, because "
                            + "nothing is placed above a top."),
            new Field("filler", Type.CHAR, Applies.BUILDING, null,
                    "The palette character for the skirt around cellars. Resolved "
                            + "in the building's palette, not the part's."),
            new Field("rubble", Type.CHAR, Applies.BUILDING, null,
                    "The palette character the ruin pass uses. Same palette as "
                            + "filler."),
            new Field("preferslonely", Type.FLOAT, Applies.BUILDING, null,
                    "The chance this type suppresses a building in each neighbouring "
                            + "chunk. Measured: 1.0 thins a city hard and does not "
                            + "empty it, so treat it as a strong preference."),

            // ------------------------------------------------------- flat shapes
            new Field("height", Type.INT, Applies.FLAT, "6",
                    "How many blocks tall this part is, read up from the plot floor. "
                            + "Six is the level stride. A part of one slice draws "
                            + "nothing at all, so one is never right.")
    );

    private Settings() {
    }

    /** Every field that applies to a plot, in schema order. */
    public static List<Field> fieldsFor(@Nullable Catalogue.Row row) {
        List<Field> out = new ArrayList<>();
        for (Field f : FIELDS) {
            if (applies(f, row)) {
                out.add(f);
            }
        }
        return out;
    }

    private static boolean applies(Field f, @Nullable Catalogue.Row row) {
        if (row == null) {
            return f.applies() == Applies.CORE;
        }
        return switch (f.applies()) {
            case CORE -> false;
            case SHAPE -> true;
            case CITY_SCOPED -> row.cityStyleScoped();
            case WEIGHTED -> row.kind() == Catalogue.Kind.SELECTOR;
            // A building plot is one whose asset stacks parts by level. Every east
            // row does; a park or a street is one part and has no floors.
            case BUILDING -> "buildings".equals(row.key())
                    || "multibuildings".equals(row.key());
            case FLAT -> !("buildings".equals(row.key())
                    || "multibuildings".equals(row.key()));
        };
    }

    @Nullable
    public static Field field(@Nullable Catalogue.Row row, String name) {
        for (Field f : fieldsFor(row)) {
            if (f.name().equals(name)) {
                return f;
            }
        }
        return null;
    }

    // ------------------------------------------------------------------ values

    /** Turn typed text into the value the file will hold, or say why it cannot. */
    public static JsonElement parse(Field field, String text) {
        String t = text.trim();
        try {
            return switch (field.type()) {
                case STRING -> new JsonPrimitive(t);
                case CHAR -> {
                    if (t.isEmpty()) {
                        throw new IllegalArgumentException("a character, not nothing");
                    }
                    // The mod keeps the first UTF-16 unit of any character key, so
                    // taking more than one here would quietly lose the rest.
                    yield new JsonPrimitive(String.valueOf(t.charAt(0)));
                }
                case INT -> new JsonPrimitive(Integer.parseInt(t));
                case FLOAT -> new JsonPrimitive(Float.parseFloat(t));
                case BOOL -> {
                    if (!t.equalsIgnoreCase("true") && !t.equalsIgnoreCase("false")) {
                        throw new IllegalArgumentException("true or false");
                    }
                    yield new JsonPrimitive(Boolean.parseBoolean(t));
                }
                case STRING_LIST -> {
                    JsonArray a = new JsonArray();
                    for (String part : split(t)) {
                        a.add(part);
                    }
                    yield a;
                }
                case INT_LIST -> {
                    JsonArray a = new JsonArray();
                    for (String part : split(t)) {
                        a.add(Integer.parseInt(part));
                    }
                    yield a;
                }
            };
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(
                    "a " + field.type().name().toLowerCase(Locale.ROOT));
        }
    }

    private static List<String> split(String text) {
        List<String> out = new ArrayList<>();
        for (String part : text.split(",")) {
            String p = part.trim();
            if (!p.isEmpty()) {
                out.add(p);
            }
        }
        return out;
    }

    /** What tab completion should offer for a field's value. */
    public static List<String> suggestions(Field field) {
        return switch (field.name()) {
            case "format" -> List.of("json", "json5");
            case "palette" -> List.of("part", "building", "global");
            default -> field.type() == Type.BOOL
                    ? List.of("true", "false")
                    : (field.fallback() == null ? List.of() : List.of(field.fallback()));
        };
    }

    // ------------------------------------------------------------------ scopes

    /**
     * Fold the three scopes into the values that apply to one level of one chunk.
     *
     * <p>Most specific wins, and each scope stores only what differs from the one
     * above it. The common case a multi-chunk plot has, every building sharing a
     * floor count so the structure generates as one thing rather than four separate
     * towers, is therefore the default rather than something to repeat four times.
     *
     * <pre>
     *   plot
     *     plot.levels[n]        every chunk, that level
     *       chunks[dx,dz]       that chunk, every level
     *         chunks[dx,dz].levels[n]
     * </pre>
     */
    public static JsonObject resolve(JsonObject plot, int dx, int dz, int level) {
        JsonObject out = shallow(plot);
        overlay(out, nested(plot, "levels", String.valueOf(level)));
        JsonObject chunk = nested(plot, "chunks", dx + "," + dz);
        overlay(out, chunk);
        if (chunk != null) {
            overlay(out, nested(chunk, "levels", String.valueOf(level)));
        }
        return out;
    }

    /** The plot's own values, without the scope containers. */
    public static JsonObject shallow(JsonObject plot) {
        JsonObject out = new JsonObject();
        for (String key : plot.keySet()) {
            if (!key.equals("chunks") && !key.equals("levels")) {
                out.add(key, plot.get(key));
            }
        }
        return out;
    }

    @Nullable
    private static JsonObject nested(JsonObject parent, String container, String key) {
        if (!parent.has(container) || !parent.get(container).isJsonObject()) {
            return null;
        }
        JsonObject c = parent.getAsJsonObject(container);
        return c.has(key) && c.get(key).isJsonObject() ? c.getAsJsonObject(key) : null;
    }

    private static void overlay(JsonObject target, @Nullable JsonObject source) {
        if (source == null) {
            return;
        }
        for (String key : source.keySet()) {
            if (!key.equals("chunks") && !key.equals("levels")) {
                target.add(key, source.get(key));
            }
        }
    }
}
