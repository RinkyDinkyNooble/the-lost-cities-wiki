package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Which parts of a block's NBT belong in a palette entry.
 *
 * <p>An export reads the NBT a block is carrying, because for some blocks the NBT is
 * the whole asset: a command block without its command is nothing, and a painting
 * without its variant draws the wrong picture. But a block entity carries everything
 * it was saved with, and a good deal of that is workshop noise rather than pack
 * content. A chest somebody opened while building carries its inventory, and a chest
 * meant to generate loot carries a {@code LootTableSeed} that would pin the same roll
 * into every copy in every world.
 *
 * <p>So the tag is filtered. The rules are a list of paths, dot separated for nesting:
 *
 * <pre>
 *   ["Command", "auto"]      keep only these two, drop the rest
 *   ["!Items", "!LootTableSeed"]   keep everything except these two
 * </pre>
 *
 * <p><b>One bare path turns the whole list into a keep-list.</b> Mixing the two is
 * allowed and reads the way it looks: the bare paths say what to keep, and a
 * {@code !} path carves an exception out of one of them.
 *
 * <p>Holds no Minecraft type, so it can be exercised without a server.
 */
public final class TagFilter {

    /** The setting both a plot and the pack's core settings may carry. */
    public static final String KEY = "tagkeys";

    /** Keeps everything, which is what an export does when nothing says otherwise. */
    public static final TagFilter ALL = new TagFilter(Map.of(), false);

    /** path -> keep it. Absent means the mode decides. */
    private final Map<String, Boolean> rules;
    /**
     * Whether any bare path was written, making this a keep-list.
     *
     * <p>Decided by what was <b>written</b>, not by what survived. A plot naming
     * {@code !Command} against a pack that keeps only {@code Command} means "not
     * even that one", and it would be a nasty surprise if cancelling the pack's
     * last keep-rule quietly turned its keep-list into a drop-list and exported
     * everything the pack had been excluding.
     */
    private final boolean keepList;

    private TagFilter(Map<String, Boolean> rules, boolean keepList) {
        this.rules = rules;
        this.keepList = keepList;
    }

    /**
     * Read the rules, later entries winning.
     *
     * <p>Callers concatenate the pack's core list and then the plot's, so a plot can
     * take back a key the pack dropped, or drop one the pack kept, by naming it
     * again.
     */
    public static TagFilter of(JsonArray paths) {
        if (paths == null || paths.isEmpty()) {
            return ALL;
        }
        Map<String, Boolean> rules = new LinkedHashMap<>();
        boolean sawKeep = false;
        for (JsonElement e : paths) {
            String raw;
            try {
                raw = e.getAsString().trim();
            } catch (RuntimeException bad) {
                // A malformed entry is the settings file's problem. The export's
                // own check reports it; dropping the whole filter over one would be
                // worse than ignoring it.
                continue;
            }
            if (raw.isEmpty()) {
                continue;
            }
            boolean keep = !raw.startsWith("!");
            String path = keep ? raw : raw.substring(1).trim();
            if (!path.isEmpty()) {
                // Re-inserted so the last mention of a path decides its rule.
                rules.remove(path);
                rules.put(path, keep);
                sawKeep |= keep;
            }
        }
        return rules.isEmpty() ? ALL : new TagFilter(rules, sawKeep);
    }

    /** Whether this would keep the whole tag untouched. */
    public boolean keepsEverything() {
        return rules.isEmpty();
    }

    /**
     * The tag, with what the rules exclude removed.
     *
     * @return the filtered tag, or null where nothing survived
     */
    public JsonObject apply(JsonObject tag) {
        if (tag == null || rules.isEmpty()) {
            return tag;
        }
        JsonObject out = filter(tag, "");
        return out.keySet().isEmpty() ? null : out;
    }

    private JsonObject filter(JsonObject in, String base) {
        JsonObject out = new JsonObject();
        for (String key : in.keySet()) {
            String path = base.isEmpty() ? key : base + "." + key;
            Boolean rule = explicit(path);
            if (Boolean.FALSE.equals(rule)) {
                continue;
            }
            JsonElement value = in.get(key);
            boolean wanted = rule != null || !keepList;
            boolean worthDescending = value.isJsonObject() && hasKeptBelow(path);
            if (!wanted && !worthDescending) {
                continue;
            }
            if (value.isJsonObject()) {
                JsonObject sub = filter(value.getAsJsonObject(), path);
                // An object kept only because something below it was wanted is
                // worth nothing once that turns out to be absent.
                if (sub.keySet().isEmpty() && !wanted) {
                    continue;
                }
                out.add(key, sub);
            } else {
                out.add(key, value);
            }
        }
        return out;
    }

    /** The nearest rule on this path or an ancestor of it, or null for none. */
    private Boolean explicit(String path) {
        String at = path;
        while (true) {
            Boolean rule = rules.get(at);
            if (rule != null) {
                return rule;
            }
            int dot = at.lastIndexOf('.');
            if (dot < 0) {
                return null;
            }
            at = at.substring(0, dot);
        }
    }

    /** Whether some rule keeps something nested under this path. */
    private boolean hasKeptBelow(String path) {
        String prefix = path + ".";
        for (Map.Entry<String, Boolean> e : rules.entrySet()) {
            if (e.getValue() && e.getKey().startsWith(prefix)) {
                return true;
            }
        }
        return false;
    }
}
