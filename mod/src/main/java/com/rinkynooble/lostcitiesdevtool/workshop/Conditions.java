package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.rinkynooble.lostcitiesdevtool.core.Json;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * What a Condition holds, read back out of the pack that defines it.
 *
 * <p><b>A Condition is what {@code loot} and {@code mob} name.</b> Not a loot table
 * and not an entity: a palette entry marked {@code loot} points at an asset under
 * {@code lostcities/conditions/}, which is a weighted list of values, each entry
 * carrying its own test for where it applies. That is not guessable and the game
 * says it nowhere, so the only way to write one used to be reading somebody else's
 * pack and copying a name out of it.
 *
 * <p>Reading rather than resolving. The runtime object keeps a compiled predicate
 * per entry and not the text it came from, so the file is the only place the shape
 * survives, exactly as it is for every other asset the workshop reads.
 */
public final class Conditions {

    /** The folder a Condition lives in, under a namespace's {@code lostcities/}. */
    public static final String FOLDER = "conditions";

    /**
     * One entry of a Condition.
     *
     * @param factor its weight against the others in the same list, relative to
     *               them rather than to 1
     * @param value  what is chosen when this entry wins
     * @param tests  the keys deciding where this entry applies, in the order the
     *               file wrote them. Empty means it always applies
     */
    public record Entry(float factor, String value, Map<String, String> tests) {

        /** Whether this entry applies everywhere its Condition is consulted. */
        public boolean always() {
            return tests.isEmpty();
        }
    }

    private Conditions() {
    }

    /** Every loaded Condition, by its fully qualified name. */
    public static Map<String, JsonObject> all(MinecraftServer server) {
        return Assets.load(server).folder(FOLDER);
    }

    /**
     * Every loaded Condition's name, as resource locations for tab completion.
     *
     * <p>Locations rather than strings so that completion matches the namespace or
     * the name, the way every resource argument in the game does. Over strings it
     * would match the whole thing and a bare name would offer nothing.
     */
    public static List<ResourceLocation> ids(MinecraftServer server) {
        List<ResourceLocation> out = new ArrayList<>();
        for (String name : all(server).keySet()) {
            try {
                out.add(new ResourceLocation(name));
            } catch (RuntimeException ignored) {
                // Not addressable, so not suggestible.
            }
        }
        return out;
    }

    /** One Condition by name, qualified the way every other reference is. */
    @Nullable
    public static JsonObject get(MinecraftServer server, String name) {
        return Assets.load(server).get(FOLDER, name);
    }

    /**
     * A Condition's entries, in the order the file wrote them.
     *
     * <p>Order is kept because a reader comparing this against their own file needs
     * the two to line up. Anything shaped wrongly is skipped rather than throwing:
     * this is read out of somebody else's pack and a malformed entry is their
     * problem to see, not a reason to answer nothing.
     */
    public static List<Entry> entriesOf(JsonObject condition) {
        List<Entry> out = new ArrayList<>();
        for (JsonElement raw : Json.array(condition, "values")) {
            if (!raw.isJsonObject()) {
                continue;
            }
            JsonObject entry = raw.getAsJsonObject();
            // A factor that is not a number is shown at its default rather than
            // dropped, because the entry is still there.
            float factor = Json.floatOf(entry, "factor", 1.0f);
            String value = Json.string(entry, "value", "");
            Map<String, String> tests = new LinkedHashMap<>();
            for (String key : entry.keySet()) {
                if (key.equals("factor") || key.equals("value")) {
                    continue;
                }
                tests.put(key, String.valueOf(entry.get(key)));
            }
            out.add(new Entry(factor, value, tests));
        }
        return out;
    }

    /** The weights added up, which is what each entry's own factor is a share of. */
    public static float totalFactor(List<Entry> entries) {
        float total = 0;
        for (Entry e : entries) {
            total += e.factor();
        }
        return total;
    }
}
