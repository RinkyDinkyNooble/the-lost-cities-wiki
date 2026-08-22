package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.storage.LevelResource;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Which character stands for which block, kept the same between exports.
 *
 * <p><b>Stability is the whole point.</b> Assigning characters afresh each time
 * makes changing one block re-letter the entire pack, and every export becomes a
 * whole-file diff that nobody can review. The ledger remembers, so a changed block
 * moves one entry and leaves the rest alone.
 *
 * <p><b>A key is a cell, not a block.</b> Two positions holding the same block need
 * different characters when one carries a loot table and the other does not, because
 * a palette entry is the pair. So the ledger is keyed by the block together with
 * whatever {@code /lcdev mark} attached to it.
 *
 * <p><b>The pool avoids everything Lost Cities ships.</b> Its own palettes use 88
 * characters between them, including every letter and every digit, and a character
 * this pack claims is taken away from every shipped part that used it. Six ASCII
 * punctuation marks are free, and after those the Greek and Cyrillic ranges are
 * untouched by the mod, which is what its own documentation recommends reaching for.
 */
public final class PaletteLedger {

    /** Air. The mod's own convention, and the one character never assigned. */
    public static final char AIR = ' ';

    private static final String FILE = "palette-ledger.json";

    private final Map<String, Character> assigned = new LinkedHashMap<>();
    private final List<Character> pool = pool();
    private int next;

    private PaletteLedger() {
    }

    /**
     * The characters this may hand out, in order.
     *
     * <p>Six free ASCII first, because a short pack stays readable in a text editor.
     * Then Greek, then Cyrillic. {@code "} and {@code \} are left out even though
     * they are unused: both need escaping inside a JSON string, which is an easy way
     * to break a generator, and the mod's own exporter omits them for that reason.
     */
    private static List<Character> pool() {
        List<Character> out = new ArrayList<>();
        for (char c : new char[]{'\'', ',', '<', '>', '?', ']'}) {
            out.add(c);
        }
        for (char c = 0x391; c <= 0x3A9; c++) {   // Greek capitals
            out.add(c);
        }
        for (char c = 0x3B1; c <= 0x3C9; c++) {   // Greek lowercase
            out.add(c);
        }
        for (char c = 0x410; c <= 0x44F; c++) {   // Cyrillic
            out.add(c);
        }
        return out;
    }

    // ------------------------------------------------------------------- lookup

    /**
     * The character for a cell, assigning one where it is new.
     *
     * @return the character, or {@code 0} when the pool is exhausted
     */
    public char characterFor(String cellKey) {
        Character have = assigned.get(cellKey);
        if (have != null) {
            return have;
        }
        while (next < pool.size() && assigned.containsValue(pool.get(next))) {
            next++;
        }
        if (next >= pool.size()) {
            return 0;
        }
        char c = pool.get(next++);
        assigned.put(cellKey, c);
        return c;
    }

    /**
     * Take a character somebody else already chose for a cell.
     *
     * <p>An import reads a pack that has already lettered itself. Keeping that
     * lettering is what makes an export of what was imported the same file that was
     * imported, and it is also the more useful result on its own: a pack written by
     * hand comes back out with the characters its author picked rather than
     * re-lettered into Greek.
     *
     * <p>It is not from the pool, so it takes no pool character away. A character
     * already standing for a different cell is refused rather than overwritten,
     * because two cells sharing one character is a palette that draws the wrong
     * block, and the caller falls back to the pool.
     *
     * @return true when the ledger now holds this character for this cell
     */
    public boolean reserve(String cellKey, char c) {
        Character have = assigned.get(cellKey);
        if (have != null) {
            return have == c;
        }
        if (c == AIR || assigned.containsValue(c)) {
            return false;
        }
        assigned.put(cellKey, c);
        return true;
    }

    /**
     * A block state as Lost Cities writes one: the id, then its properties.
     *
     * <p>Here rather than in the exporter because the importer has to produce the
     * same text for the same block. A cell key that differs by a space or by
     * property order is a different cell, and the two halves would letter the same
     * world differently.
     */
    public static String describe(BlockState state) {
        String id = String.valueOf(BuiltInRegistries.BLOCK.getKey(state.getBlock()));
        if (state.getValues().isEmpty()) {
            return id;
        }
        StringBuilder out = new StringBuilder(id).append('[');
        boolean first = true;
        for (Map.Entry<Property<?>, Comparable<?>> e : state.getValues().entrySet()) {
            if (!first) {
                out.append(',');
            }
            first = false;
            out.append(e.getKey().getName()).append('=')
                    .append(value(e.getKey(), e.getValue()));
        }
        return out.append(']').toString();
    }

    @SuppressWarnings("unchecked")
    private static <T extends Comparable<T>> String value(Property<?> property,
                                                          Comparable<?> held) {
        return ((Property<T>) property).getName((T) held);
    }

    public int size() {
        return assigned.size();
    }

    public int capacity() {
        return pool.size();
    }

    /** Cell key to character, in assignment order. */
    public Map<String, Character> entries() {
        return assigned;
    }

    // -------------------------------------------------------------- persistence

    public static Path pathOf(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve("lostcitiesdevtool")
                .resolve(FILE).toAbsolutePath().normalize();
    }

    public static PaletteLedger load(MinecraftServer server) throws IOException {
        PaletteLedger ledger = new PaletteLedger();
        Path path = pathOf(server);
        if (!Files.isRegularFile(path)) {
            return ledger;
        }
        try {
            JsonObject root = JsonParser.parseString(
                    Files.readString(path, StandardCharsets.UTF_8)).getAsJsonObject();
            JsonObject map = root.getAsJsonObject("assigned");
            for (String key : map.keySet()) {
                String value = map.get(key).getAsString();
                if (!value.isEmpty()) {
                    ledger.assigned.put(key, value.charAt(0));
                }
            }
        } catch (RuntimeException e) {
            throw new IOException("the palette ledger could not be read: "
                    + e.getMessage());
        }
        return ledger;
    }

    public void save(MinecraftServer server) throws IOException {
        JsonObject root = new JsonObject();
        root.addProperty("_about", "Which character stands for which cell. Kept so "
                + "that changing one block moves one entry rather than re-lettering "
                + "the whole pack. Delete it to start the lettering over.");
        JsonObject map = new JsonObject();
        for (Map.Entry<String, Character> e : assigned.entrySet()) {
            map.addProperty(e.getKey(), String.valueOf(e.getValue()));
        }
        root.add("assigned", map);
        Path path = pathOf(server);
        Files.createDirectories(path.getParent());
        Files.writeString(path,
                new GsonBuilder().setPrettyPrinting().create().toJson(root),
                StandardCharsets.UTF_8);
    }
}
