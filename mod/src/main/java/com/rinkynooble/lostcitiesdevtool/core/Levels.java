package com.rinkynooble.lostcitiesdevtool.core;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.List;

/**
 * Which part reference applies at a level, decided the way Lost Cities decides it.
 *
 * <p>Written once for the two readers that need it. The load check and the import
 * each had their own copy of the level tests and of the range parser, and the copies
 * disagreed with each other and with Lost Cities. The check split a range on every
 * comma, so {@code "0,,2"} was reported as broken; the import wanted exactly two
 * numbers and trimmed spaces, so {@code "0,2,9"} imported with those levels empty
 * while generation built them, and {@code "0, 2"} imported while generation threw.
 *
 * <p><b>A test written with the wrong type is no test at all.</b> Every one of them
 * is an optional field, and the optional field codec in the DataFixerUpper 1.20.1
 * ships reads a value it cannot parse as absent rather than as an error. What it can
 * parse follows {@code JsonOps}: a boolean test also takes a number, true when its
 * byte value is not zero; a number takes a boolean as 1 or 0; a string takes only a
 * string. {@code "top": "yes"} therefore places a part on every level.
 *
 * <p>Holds no Minecraft type, so it can be exercised without a server.
 */
public final class Levels {

    private Levels() {
    }

    /**
     * Whether a part reference applies at this level of a building whose top level
     * is {@code top}. Tests chain with AND, never OR.
     *
     * <p>Only the tests a level decides. The rest, {@code chunkx} and the like,
     * depend on where the building stands, and a caller that meets one has to treat
     * it on its own.
     */
    public static boolean matches(JsonObject ref, int level, int top) {
        Boolean ground = bool(ref.get("ground"));
        if (ground != null && (level == 0) != ground) {
            return false;
        }
        Boolean isTop = bool(ref.get("top"));
        if (isTop != null && (level >= top) != isTop) {
            return false;
        }
        Boolean cellar = bool(ref.get("cellar"));
        if (cellar != null && (level < 0) != cellar) {
            return false;
        }
        Integer floor = integer(ref.get("floor"));
        if (floor != null && level != floor) {
            return false;
        }
        String range = string(ref.get("range"));
        if (range != null) {
            int[] bounds = range(range);
            return bounds != null && level >= bounds[0] && level <= bounds[1];
        }
        return true;
    }

    /**
     * A floor range as {@code ConditionContext} reads one: split on commas with the
     * empty pieces dropped, which is {@code StringUtils.split}, then the first two
     * parsed exactly as written and the rest ignored.
     *
     * @return {@code {low, high}}, or null where Lost Cities throws
     *         {@code Bad range specification}
     */
    @Nullable
    public static int[] range(@Nullable String text) {
        List<String> pieces = pieces(text);
        if (pieces.size() < 2) {
            return null;
        }
        try {
            return new int[]{Integer.parseInt(pieces.get(0)),
                    Integer.parseInt(pieces.get(1))};
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /** How many numbers a range carries, of which Lost Cities reads two. */
    public static int numbers(@Nullable String text) {
        return pieces(text).size();
    }

    private static List<String> pieces(@Nullable String text) {
        List<String> out = new ArrayList<>();
        if (text == null) {
            return out;
        }
        for (String piece : text.split(",")) {
            if (!piece.isEmpty()) {
                out.add(piece);
            }
        }
        return out;
    }

    // --------------------------------------------- values as the codec reads them

    /** A boolean test's value, or null where the codec would read none. */
    @Nullable
    public static Boolean bool(@Nullable JsonElement e) {
        JsonPrimitive p = primitive(e);
        if (p == null) {
            return null;
        }
        if (p.isBoolean()) {
            return p.getAsBoolean();
        }
        return p.isNumber() ? p.getAsNumber().byteValue() != 0 : null;
    }

    /** A number test's value, or null where the codec would read none. */
    @Nullable
    public static Integer integer(@Nullable JsonElement e) {
        JsonPrimitive p = primitive(e);
        if (p == null) {
            return null;
        }
        if (p.isNumber()) {
            return p.getAsNumber().intValue();
        }
        return p.isBoolean() ? (p.getAsBoolean() ? 1 : 0) : null;
    }

    /** A string test's value, or null where the codec would read none. */
    @Nullable
    public static String string(@Nullable JsonElement e) {
        JsonPrimitive p = primitive(e);
        return p != null && p.isString() ? p.getAsString() : null;
    }

    @Nullable
    private static JsonPrimitive primitive(@Nullable JsonElement e) {
        return e != null && e.isJsonPrimitive() ? e.getAsJsonPrimitive() : null;
    }
}
