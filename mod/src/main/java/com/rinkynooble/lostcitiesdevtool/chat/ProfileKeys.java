package com.rinkynooble.lostcitiesdevtool.chat;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;

import javax.annotation.Nullable;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * What Lost Cities itself says about each profile key, for hover text in chat.
 *
 * <p>The mod writes a comment above every key when it generates a config file, and
 * that comment is the closest thing to an official description any of them have. A
 * person reading a report should not have to leave the game to find out what
 * {@code ruinChance} means.
 *
 * <p>Both files are resources rather than code. {@code profile_keys.json} is
 * generated from the jar by {@code mod/tools/extract-profile-keys.py} and holds all
 * 131 keys. {@code profile_key_corrections.json} is written by hand and holds the
 * few whose comment says something the code does not do; the comment is still shown,
 * because that is what the reader will find in their own config file, with the
 * correction under it.
 *
 * <p>Missing or unreadable data is not an error. Hover text is a courtesy, and a
 * report is still worth printing without it.
 */
public final class ProfileKeys {

    /** One key: what the mod declares about it, and what it says about it. */
    public record Key(String name, @Nullable String section, @Nullable String type,
                      @Nullable String comment, @Nullable String min,
                      @Nullable String max, @Nullable String defaultValue,
                      @Nullable Correction correction) {
    }

    /** A key whose shipped comment misleads. */
    public record Correction(String says, String actually, String evidence) {
    }

    private static final String KEYS = "/data/lostcitiesdevtool/profile_keys.json";
    private static final String FIXES = "/data/lostcitiesdevtool/profile_key_corrections.json";

    /**
     * Volatile because these are published from one thread and read from others.
     *
     * <p>Every caller is on the server thread today, and that is an invariant nothing
     * enforces. Without volatile the failure mode is unsafe publication: a reader sees
     * the reference before the object it points at is fully built. That appears once,
     * on somebody else's machine, and never reproduces. `Json5Overrides` in this same
     * codebase already does it this way.
     */
    private static volatile Map<String, Key> keys;

    private ProfileKeys() {
    }

    /** The key, or null if it is not one the mod declares. */
    @Nullable
    public static Key get(String name) {
        return all().get(name);
    }

    public static Map<String, Key> all() {
        if (keys == null) {
            keys = load();
        }
        return keys;
    }

    private static Map<String, Key> load() {
        Map<String, Correction> fixes = loadCorrections();
        Map<String, Key> out = new HashMap<>();
        JsonObject root = read(KEYS);
        if (root == null || !root.has("keys")) {
            return Collections.emptyMap();
        }
        for (Map.Entry<String, JsonElement> e : root.getAsJsonObject("keys").entrySet()) {
            JsonObject o = e.getValue().getAsJsonObject();
            out.put(e.getKey(), new Key(e.getKey(),
                    str(o, "section"), str(o, "type"), str(o, "comment"),
                    str(o, "min"), str(o, "max"), str(o, "default"),
                    fixes.get(e.getKey())));
        }
        return Collections.unmodifiableMap(out);
    }

    private static Map<String, Correction> loadCorrections() {
        Map<String, Correction> out = new HashMap<>();
        JsonObject root = read(FIXES);
        if (root == null || !root.has("corrections")) {
            return out;
        }
        for (Map.Entry<String, JsonElement> e
                : root.getAsJsonObject("corrections").entrySet()) {
            JsonObject o = e.getValue().getAsJsonObject();
            out.put(e.getKey(), new Correction(
                    String.valueOf(str(o, "says")),
                    String.valueOf(str(o, "actually")),
                    String.valueOf(str(o, "evidence"))));
        }
        return out;
    }

    @Nullable
    private static JsonObject read(String path) {
        try (InputStream in = ProfileKeys.class.getResourceAsStream(path)) {
            if (in == null) {
                return null;
            }
            return JsonParser.parseReader(
                    new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        } catch (Exception e) {
            // A courtesy that failed to load is not worth failing a command over.
            LostCitiesDevTool.LOGGER.warn("could not read {}: {}", path, e.toString());
            return null;
        }
    }

    @Nullable
    private static String str(JsonObject o, String field) {
        JsonElement e = o.get(field);
        return e == null || e.isJsonNull() ? null : e.getAsString();
    }
}
