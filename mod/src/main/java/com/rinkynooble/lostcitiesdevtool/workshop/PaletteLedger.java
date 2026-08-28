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
import java.text.Normalizer;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

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
 *
 * <p><b>Past those, the rest of the plane.</b> A pack of two detailed buildings can
 * pass a hundred and twenty cells, and stopping there refused to export a build that
 * was in no way unreasonable. The pool continues through every character in the basic
 * multilingual plane that is safe to write into a slice row, which is about forty
 * thousand. Minecraft ships around twenty six thousand block states in total, so the
 * pool is no longer the limit on anything.
 *
 * <p><b>The plane, and not beyond it, because Lost Cities counts in {@code char}.</b>
 * Its palette is a {@code Map<Character, PE>} keyed by {@code getChr().charAt(0)}, and
 * a slice row is read with {@code toCharArray()}. A code point above {@code U+FFFF} is
 * a surrogate pair in Java, so as a palette key only its high surrogate would be read,
 * and inside a row it would count as <em>two</em> cells and shift every block after it
 * along. Both failures are silent, which is what makes the ceiling worth stating.
 */
public final class PaletteLedger {

    /** Air. The mod's own convention, and the one character never assigned. */
    public static final char AIR = ' ';

    private static final String FILE = "palette-ledger.json";

    /** Built once. Forty thousand characters, and the scan that finds them is 4ms. */
    private static final String POOL = pool();

    private final Map<String, Character> assigned = new LinkedHashMap<>();

    /**
     * Every character {@link #assigned} holds, for membership alone.
     *
     * <p>The scan for a free character used to ask the map, and
     * {@code LinkedHashMap.containsValue} is a walk of the whole map. At a pool of a
     * hundred and twenty that cost nothing because it could not run far. At forty
     * thousand the same loop is quadratic in the size of the pack, so the answer is
     * kept in a set instead.
     */
    private final Set<Character> used = new HashSet<>();

    private int next;

    private PaletteLedger() {
    }

    /**
     * The characters this may hand out, in order.
     *
     * <p>Six free ASCII first, because a short pack stays readable in a text editor.
     * Then Greek, then Cyrillic, which is the order the pool has always had and is
     * kept so that a ledger written by an older build keeps growing the way it began.
     * Then everything else in the plane in code point order, which puts the readable
     * remains of Latin Extended next.
     *
     * <p>{@code "} and {@code \} are left out even though they are unused: both need
     * escaping inside a JSON string, which is an easy way to break a generator, and
     * the mod's own exporter omits them for that reason.
     */
    private static String pool() {
        StringBuilder out = new StringBuilder();
        Set<Character> seen = new HashSet<>();
        for (char c : new char[]{'\'', ',', '<', '>', '?', ']'}) {
            take(out, seen, c);
        }
        for (char c = 0x391; c <= 0x3A9; c++) {   // Greek capitals
            take(out, seen, c);
        }
        for (char c = 0x3B1; c <= 0x3C9; c++) {   // Greek lowercase
            take(out, seen, c);
        }
        for (char c = 0x410; c <= 0x44F; c++) {   // Cyrillic
            take(out, seen, c);
        }
        // Latin Extended upward. Below 0x100 is ASCII and Latin-1, which Lost Cities'
        // own palettes already spend, so there is nothing free to pick up down there.
        for (int c = 0x100; c <= 0xFFFF; c++) {
            take(out, seen, (char) c);
        }
        return out.toString();
    }

    private static void take(StringBuilder out, Set<Character> seen, char c) {
        if (seen.contains(c) || !safe(c)) {
            return;
        }
        seen.add(c);
        out.append(c);
    }

    /**
     * Whether a character can stand for a block in a slice row without surprises.
     *
     * <p>Each rejection is something that has a way of going wrong quietly:
     *
     * <ul>
     *   <li><b>Air, {@code "} and {@code \}</b>: reserved, and the two that need JSON
     *       escaping.
     *   <li><b>Surrogates and undefined code points</b>: half a character, and a
     *       character no font has. The Greek capitals run from {@code 0x391} to
     *       {@code 0x3A9} straight through {@code 0x3A2}, which is a reserved hole,
     *       so this is not hypothetical: the pool used to contain it.
     *   <li><b>Anything blank</b>: a row is positional, and a space that is not the
     *       air character is a cell nobody can see.
     *   <li><b>Control, format and private use</b>: invisible, and a format character
     *       can reorder the text around it.
     *   <li><b>Combining marks</b>: they attach to whatever precedes them, so a row
     *       stops showing one glyph per cell.
     *   <li><b>Right to left</b>: a row containing one renders in an order that is not
     *       the order the blocks are in, which makes a pack impossible to hand edit.
     *   <li><b>Anything a normaliser would rewrite</b>: a tool that runs NFC or NFD
     *       over the file would compose or decompose the character, and a decomposed
     *       one is two {@code char}s where the row expects one. This is the rule that
     *       drops the precomposed accented Latin.
     * </ul>
     */
    private static boolean safe(char c) {
        if (c == AIR || c == '"' || c == '\\') {
            return false;
        }
        if (Character.isSurrogate(c) || !Character.isDefined(c)) {
            return false;
        }
        if (Character.isWhitespace(c) || Character.isSpaceChar(c)) {
            return false;
        }
        switch (Character.getType(c)) {
            case Character.CONTROL:
            case Character.FORMAT:
            case Character.PRIVATE_USE:
            case Character.UNASSIGNED:
            case Character.SURROGATE:
            case Character.LINE_SEPARATOR:
            case Character.PARAGRAPH_SEPARATOR:
            case Character.SPACE_SEPARATOR:
            case Character.NON_SPACING_MARK:
            case Character.ENCLOSING_MARK:
            case Character.COMBINING_SPACING_MARK:
                return false;
            default:
                break;
        }
        byte direction = Character.getDirectionality(c);
        if (direction == Character.DIRECTIONALITY_RIGHT_TO_LEFT
                || direction == Character.DIRECTIONALITY_RIGHT_TO_LEFT_ARABIC) {
            return false;
        }
        String s = String.valueOf(c);
        return Normalizer.isNormalized(s, Normalizer.Form.NFC)
                && Normalizer.isNormalized(s, Normalizer.Form.NFD);
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
        while (next < POOL.length() && used.contains(POOL.charAt(next))) {
            next++;
        }
        if (next >= POOL.length()) {
            return 0;
        }
        char c = POOL.charAt(next++);
        put(cellKey, c);
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
        if (c == AIR || used.contains(c)) {
            return false;
        }
        put(cellKey, c);
        return true;
    }

    /** The one place a cell and a character are bound, so {@link #used} cannot drift. */
    private void put(String cellKey, char c) {
        assigned.put(cellKey, c);
        used.add(c);
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

    public int capacity() {
        return POOL.length();
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
                    ledger.put(key, value.charAt(0));
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
