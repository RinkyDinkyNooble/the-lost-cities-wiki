package com.rinkynooble.lostcitiesdevtool.core;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.List;

/**
 * Reading a file somebody edited by hand, and writing one for somebody to edit.
 *
 * <p><b>A read answers its fallback rather than throwing</b> where the key is missing
 * or Gson cannot give it the type asked for. A plot's settings, a pack's assets and a
 * Condition are all written by hand, so a word where a number belongs is the ordinary
 * case, and one bad value must not cost the rest of the file. Gson converts where it
 * can: a number reads as its text, {@code "5"} as 5 and 5.7 as 5 for a whole number,
 * and any text or number other than {@code true} as false.
 *
 * <p>Where a wrong type has to be reported rather than read past, the caller asks for
 * the element itself: the load check does, and so does the export for the settings it
 * refuses by plot and key.
 *
 * <p><b>Written without HTML escaping.</b> Gson's default turns every equals sign into
 * a six-character unicode escape, so a block state in a file meant to be read came
 * back unreadable.
 */
public final class Json {

    /** Indented, for a file a person reads. */
    public static final Gson PRETTY = new GsonBuilder().setPrettyPrinting()
            .disableHtmlEscaping().create();

    /** On one line, for a value inside a file laid out by hand. */
    public static final Gson COMPACT = new GsonBuilder().disableHtmlEscaping().create();

    private Json() {
    }

    public static String string(JsonObject o, String key, String fallback) {
        try {
            return o.has(key) ? o.get(key).getAsString() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    public static int intOf(JsonObject o, String key, int fallback) {
        try {
            return o.has(key) ? o.get(key).getAsInt() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    public static float floatOf(JsonObject o, String key, float fallback) {
        try {
            return o.has(key) ? o.get(key).getAsFloat() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    public static boolean bool(JsonObject o, String key, boolean fallback) {
        try {
            return o.has(key) ? o.get(key).getAsBoolean() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    /** The whole numbers in a list. An entry that is not one is skipped, not fatal. */
    public static List<Integer> ints(JsonObject o, String key) {
        List<Integer> out = new ArrayList<>();
        for (JsonElement e : array(o, key)) {
            try {
                out.add(e.getAsInt());
            } catch (RuntimeException ignored) {
                // One bad entry does not cost the rest of the list.
            }
        }
        return out;
    }

    /** A list, or an empty one where the key is missing or holds something else. */
    public static JsonArray array(JsonObject o, String key) {
        return o.has(key) && o.get(key).isJsonArray()
                ? o.getAsJsonArray(key) : new JsonArray();
    }

    /** An object, or null where the key is missing or holds something else. */
    @Nullable
    public static JsonObject object(JsonObject o, String key) {
        return o.has(key) && o.get(key).isJsonObject()
                ? o.getAsJsonObject(key) : null;
    }
}
