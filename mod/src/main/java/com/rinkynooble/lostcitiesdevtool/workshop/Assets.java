package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import com.rinkynooble.lostcitiesdevtool.json5.Json5;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.server.packs.resources.ResourceManager;

import java.lang.ref.WeakReference;

import javax.annotation.Nullable;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Every Lost Cities asset the server has loaded, as the JSON it was written as.
 *
 * <p>Read from the resource manager rather than from the mod's own objects. The
 * runtime objects have lost most of what the file said: a Building keeps no list of
 * its part references, only a predicate per entry, and a registry's iterable is a
 * cache that fills as things are asked for by name rather than a listing. The JSON
 * is what the author wrote, and it is what the import has to be able to give back.
 *
 * <p>This reads what is loaded, so the mod's own built-in pack and every datapack in
 * the world are all in here, later packs having replaced earlier ones by name
 * exactly as they do in generation.
 */
public final class Assets {

    private static final String ROOT = "lostcities/";

    private final Map<String, Map<String, JsonObject>> byFolder = new LinkedHashMap<>();
    /** The same keys, holding the extension each asset was written under. */
    private final Map<String, Map<String, String>> extByFolder = new LinkedHashMap<>();
    /** The same keys, holding which loaded pack each asset was read out of. */
    private final Map<String, Map<String, String>> sourceByFolder =
            new LinkedHashMap<>();

    /**
     * The manager the cache was built from, weakly, and what was built.
     *
     * <p>Static because there is one server per process and the resource manager it
     * hands out is the thing that changes. Every caller is on the server thread:
     * commands run there, and so does the packet that asks for suggestions.
     */
    private static WeakReference<ResourceManager> cachedFor = new WeakReference<>(null);
    @Nullable
    private static Assets cached;

    private Assets() {
    }

    /**
     * Every loaded asset, read once per datapack load.
     *
     * <p><b>Cached, because tab completion asks per keystroke.</b> Completing
     * {@code /lcdev import <name>} calls this for every character typed and again
     * for every backspace, and reading it afresh means opening and parsing every
     * Lost Cities file the server has. Measured on a server holding 911 of them,
     * that was 99 ms a keystroke, so typing one name cost close to two seconds of
     * server time.
     *
     * <p>The cache is keyed on the resource manager itself rather than on an event.
     * Minecraft builds a new one for every datapack load, so an edit is picked up by
     * the identity check without anything having to remember to invalidate, and a
     * stale read is not possible. The reference to the manager is weak so that
     * holding the cache cannot keep a discarded one alive.
     */
    public static Assets load(MinecraftServer server) {
        ResourceManager manager = server.getResourceManager();
        Assets have = cached;
        if (have != null && cachedFor.get() == manager) {
            return have;
        }
        Assets built = read(manager);
        cached = built;
        cachedFor = new WeakReference<>(manager);
        return built;
    }

    private static Assets read(ResourceManager manager) {
        Assets out = new Assets();
        Map<ResourceLocation, Resource> found = manager
                .listResources(ROOT.substring(0, ROOT.length() - 1),
                        id -> id.getPath().endsWith(Json5.EXT_JSON)
                                || id.getPath().endsWith(Json5.EXT_JSON5));
        for (Map.Entry<ResourceLocation, Resource> e : found.entrySet()) {
            ResourceLocation id = e.getKey();
            String path = id.getPath();
            if (!path.startsWith(ROOT)) {
                continue;
            }
            String rest = path.substring(ROOT.length());
            int slash = rest.indexOf('/');
            if (slash <= 0) {
                continue;
            }
            String folder = rest.substring(0, slash);
            String name = rest.substring(slash + 1);
            name = name.substring(0, name.lastIndexOf('.'));
            JsonObject json = read(e.getValue(), id);
            if (json != null) {
                String key = id.getNamespace() + ":" + name;
                out.byFolder.computeIfAbsent(folder, k -> new HashMap<>())
                        .put(key, json);
                out.sourceByFolder.computeIfAbsent(folder, k -> new HashMap<>())
                        .put(key, e.getValue().sourcePackId());
                out.extByFolder.computeIfAbsent(folder, k -> new HashMap<>())
                        .put(key, path.substring(path.lastIndexOf('.')));
            }
        }
        return out;
    }

    @Nullable
    private static JsonObject read(Resource resource, ResourceLocation id) {
        try (InputStream in = resource.open()) {
            String text = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            JsonElement parsed = JsonParser.parseString(Json5.sanitise(text));
            return parsed.isJsonObject() ? parsed.getAsJsonObject() : null;
        } catch (Exception e) {
            LostCitiesDevTool.LOGGER.warn("could not read {}: {}", id, e.toString());
            return null;
        }
    }

    /**
     * One asset by name.
     *
     * <p>A bare name means {@code lostcities:}, never the pack the reference was
     * written in. That is the mod's own rule and the commonest way a pack breaks.
     */
    @Nullable
    public JsonObject get(String folder, String name) {
        Map<String, JsonObject> all = byFolder.get(folder);
        if (all == null || name == null) {
            return null;
        }
        return all.get(qualify(name));
    }

    /**
     * Which loaded pack an asset came out of.
     *
     * <p>The pack knows things the assets do not: what it is called, and what its
     * author wrote in its description. Neither is in any file under
     * {@code lostcities/}, so an import that did not ask would lose them.
     */
    @Nullable
    public String source(String folder, String name) {
        Map<String, String> all = sourceByFolder.get(folder);
        if (all == null || name == null) {
            return null;
        }
        return all.get(qualify(name));
    }

    /**
     * The extension an asset was written under.
     *
     * <p>{@code .json5} is a decision its author made, and one only this mod can
     * read. An export of what was imported writes json unless it is told, which
     * would quietly rename every file in somebody's pack.
     */
    @Nullable
    public String extension(String folder, String name) {
        Map<String, String> all = extByFolder.get(folder);
        if (all == null || name == null) {
            return null;
        }
        return all.get(qualify(name));
    }

    /**
     * A name in the one form everything else can compare.
     *
     * <p>Selectors are written both ways, and the same building reached as
     * {@code tower} and as {@code lostcities:tower} is one asset. Anything keying a
     * map on a reference has to put it through here first or it holds the same
     * asset twice under two spellings.
     */
    public static String qualify(String name) {
        return name.contains(":") ? name : "lostcities:" + name;
    }

    public Map<String, JsonObject> folder(String folder) {
        return byFolder.getOrDefault(folder, Map.of());
    }

    /**
     * A city style with its inheritance resolved.
     *
     * <p>Scalars and blocks come from the child where it sets them. <b>Selectors
     * accumulate</b> rather than replacing, which is the behaviour that surprises
     * nearly everyone: adding one building to a style that inherits three leaves you
     * with four. <b>{@code streetblocks.parts} is the exception and is all or
     * nothing</b>: writing any of it discards the parent's whole block.
     */
    @Nullable
    public JsonObject cityStyle(String name) {
        JsonObject child = get("citystyles", name);
        if (child == null) {
            return null;
        }
        if (!child.has("inherit")) {
            return child;
        }
        JsonObject parent = cityStyle(child.get("inherit").getAsString());
        if (parent == null) {
            return child;
        }
        JsonObject out = deepCopy(parent);
        for (String key : child.keySet()) {
            if (key.equals("inherit")) {
                continue;
            }
            if (key.equals("selectors") && out.has("selectors")) {
                JsonObject merged = out.getAsJsonObject("selectors");
                JsonObject add = child.getAsJsonObject("selectors");
                for (String sel : add.keySet()) {
                    JsonArray into = merged.has(sel)
                            ? merged.getAsJsonArray(sel) : new JsonArray();
                    add.getAsJsonArray(sel).forEach(into::add);
                    merged.add(sel, into);
                }
            } else if (key.equals("streetblocks") && out.has("streetblocks")) {
                JsonObject merged = out.getAsJsonObject("streetblocks");
                JsonObject add = child.getAsJsonObject("streetblocks");
                for (String k : add.keySet()) {
                    // parts included: writing any of it replaces the whole block.
                    merged.add(k, add.get(k));
                }
            } else {
                out.add(key, child.get(key));
            }
        }
        return out;
    }

    private static JsonObject deepCopy(JsonObject o) {
        return JsonParser.parseString(o.toString()).getAsJsonObject();
    }
}
