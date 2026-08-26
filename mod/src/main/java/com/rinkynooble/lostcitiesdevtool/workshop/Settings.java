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

    public enum Type { STRING, INT, FLOAT, BOOL, STRING_LIST, INT_LIST }

    /** Which plots a field belongs to. */
    public enum Applies {
        /** Every catalogue plot, but not the front desk. */
        SHAPE,
        /** The front desk at the origin. */
        CORE,
        /**
         * The front desk and every catalogue plot alike.
         *
         * <p>For a setting the pack states once and a plot overrides where it has
         * reason to, rather than one that belongs to one or the other.
         */
        ANY,
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
            new Field("inherit", Type.STRING, Applies.CORE, "citystyle_common",
                    "The city style every style this pack writes inherits from. "
                            + "Selectors accumulate rather than replace, so "
                            + "citystyle_common adds the mod's own buildings, parks "
                            + "and bridges to yours instead of standing aside for "
                            + "them, and there is no way to take its plumbing and "
                            + "leave its buildings. none inherits nothing and writes "
                            + "the street, park, corridor, rail and sphere blocks "
                            + "directly, which gives cities built only out of the "
                            + "workshop and leaves every kind you did not build "
                            + "empty."),
            new Field("format", Type.STRING, Applies.CORE, "json",
                    "The extension the assets are written under. json is read by "
                            + "Lost Cities on its own. json5 is read only where "
                            + "this mod is installed, and is the extension to use "
                            + "for a pack meant to be edited afterwards, since "
                            + "json5 allows the comments and trailing commas that "
                            + "json rejects. What is written is the same text "
                            + "either way."),

            // --------------------------------------------------------- every plot
            new Field("name", Type.STRING, Applies.SHAPE, null,
                    "The asset name. Defaults to the plot's own id with the slashes "
                            + "replaced, which is unique but not memorable."),
            new Field("skip", Type.BOOL, Applies.SHAPE, "false",
                    "Leave this plot out of the export entirely, without deleting "
                            + "what is built on it."),
            new Field("tagkeys", Type.STRING_LIST, Applies.ANY, null,
                    "Which of a block's NBT reaches the pack. An export reads what "
                            + "a block entity is carrying, because for some blocks "
                            + "that is the whole asset: a command block without its "
                            + "command is nothing. It also reads what you never "
                            + "meant to ship, like the items in a chest you opened "
                            + "while building. Naming keys plainly keeps only those; "
                            + "prefixing one with ! drops it and keeps the rest; a "
                            + "dot reaches inside, as in Base.Color. Set on the "
                            + "front desk it is the pack's rule, and a plot naming "
                            + "the same key again overrides it. Unset, everything "
                            + "the block carries is kept."),
            new Field("palette", Type.STRING, Applies.SHAPE, "global",
                    "Where this plot's characters are written. global puts them in "
                            + "the pack's shared palette and points the assets at "
                            + "it, so one entry covers every part using that block "
                            + "and changing it changes them all. part writes each "
                            + "part's own characters into the part, and building "
                            + "writes the whole building's into the building: both "
                            + "make the file readable on its own and repeat an "
                            + "entry wherever a block is reused. A flat plot is one "
                            + "part, so part and building mean the same there."),

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
            new Field("pinFloors", Type.BOOL, Applies.BUILDING, "true",
                    "Whether the export writes the floor and cellar counts into the "
                            + "building. False leaves them out, so the profile "
                            + "decides how tall it is and the parts become a bag the "
                            + "generator draws from, which is how the mod's own "
                            + "buildings are written."),
            new Field("tops", Type.INT_LIST, Applies.BUILDING, null,
                    "The height in blocks of each top variation, read upward from "
                            + "where the floors stop. They are alternatives, not a "
                            + "stack: the mod picks one. Free height, because "
                            + "nothing is placed above a top."),
            new Field("filler", Type.STRING, Applies.BUILDING, null,
                    "What the skirt around cellars is made of. A block id gets a "
                            + "palette entry of its own and comes back as whatever "
                            + "character this pack gave that block, which is what "
                            + "survives being imported somewhere else. A single "
                            + "character is written through untouched, and is "
                            + "resolved in the building's palette, not the part's."),
            new Field("rubble", Type.STRING, Applies.BUILDING, null,
                    "What the ruin pass fills with. A block id or a single "
                            + "character, read the same way filler is, in the same "
                            + "palette."),
            new Field("preferslonely", Type.FLOAT, Applies.BUILDING, null,
                    "The chance this type suppresses a building in each neighbouring "
                            + "chunk. Measured: 1.0 thins a city hard and does not "
                            + "empty it, so treat it as a strong preference."),

            // ------------------------------------------------------- flat shapes
            new Field("height", Type.INT, Applies.FLAT, "6",
                    "How many blocks tall this part is, read up from the plot floor. "
                            + "Six is the level stride. One slice is fine here and is "
                            + "what every street shape the mod ships uses, because a "
                            + "road is one layer; it is only a level of a building "
                            + "that draws nothing at a single slice.")
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
            return f.applies() == Applies.CORE || f.applies() == Applies.ANY;
        }
        return switch (f.applies()) {
            case CORE -> false;
            case SHAPE, ANY -> true;
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
                case INT -> new JsonPrimitive(Integer.parseInt(t));
                case FLOAT -> {
                    float f = Float.parseFloat(t);
                    // Float.parseFloat takes "NaN" and overflows quietly to
                    // Infinity: a float stops at about 3.4e38, so `1e99` is a
                    // plausible typo rather than a silly value. Gson then writes
                    // the word Infinity into the file, which reads back because
                    // its parser is lenient and which no strict JSON reader will
                    // take, so the pack that carries it into a datapack does not
                    // load and nothing between here and there says why.
                    if (!Float.isFinite(f)) {
                        throw new IllegalArgumentException(
                                "a number a float can hold, which stops at about "
                                        + "3.4e38. " + t + " reads as " + f);
                    }
                    yield new JsonPrimitive(f);
                }
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
            case "inherit" -> List.of("citystyle_common", "none");
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
