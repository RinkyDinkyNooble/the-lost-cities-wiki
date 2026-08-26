package com.rinkynooble.lostcitiesdevtool.workshop;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * The terms a pack states, as text.
 *
 * <p>Everything here is string work with no Minecraft in it, which is deliberate:
 * shaping a licence for a chat line and folding several of them into one notice are
 * arithmetic, and arithmetic does not need a server to check.
 * {@link Attribution} is the half that reads files.
 *
 * <p><b>The file is spelled {@code license.txt}.</b> That one spelling is a contract
 * with everything outside this mod: it is a resource location under {@code data/},
 * and an uppercase or British name there is not a valid path, so the loader reports
 * {@code Invalid path in datapack ... ignoring} and nothing can ever read it.
 * Everything this mod chooses the spelling of says licence.
 */
public final class Licence {

    /** The file name, in the one spelling a resource location allows. */
    public static final String FILE = "license.txt";

    /** Where a namespace states its terms, under {@code data/<namespace>/}. */
    public static final String PATH = "lostcities/" + FILE;

    /**
     * The most that is read from one.
     *
     * <p>A file from an untrusted pack, read on every import, to show three lines
     * of. There is no reading of megabytes that ends in a better answer.
     */
    public static final int MAX_BYTES = 64 * 1024;

    /**
     * How many lines are shown.
     *
     * <p>Three, because a licence announces itself in its first lines: the name,
     * then the copyright holder. Anything past that is the body.
     */
    public static final int LINES_SHOWN = 3;

    /**
     * The most characters one shown line keeps.
     *
     * <p>A line cap on its own is not enough. One very long line wraps into three in
     * chat and defeats it, which is exactly what a licence written as a single
     * paragraph does. Matches the width the chat box holds at default scale.
     */
    public static final int MAX_LINE = 52;

    /**
     * The first line of a notice this mod wrote, and the thing that identifies one.
     *
     * <p>Read as well as written. A pack compiled out of an imported pack carries a
     * notice, and importing that one and compiling again has to pass the statements
     * through rather than wrapping the wrapper.
     */
    public static final String MARKER =
            "# Licence statements carried over by The Lost Cities DevTool.";

    /** What separates one namespace's statement from the next inside a notice. */
    private static final String RULE = "=====";

    /**
     * A licence cut down to what fits on screen.
     *
     * @param shown     the first lines, stripped and cut to {@link #MAX_LINE}
     * @param more      lines past those, counted rather than elided, so the reader
     *                  can tell a permissive licence from a whole GPL
     * @param truncated whether the read stopped at {@link #MAX_BYTES}, in which case
     *                  {@code more} counts what was read and not what is there
     */
    public record Summary(List<String> shown, int more, boolean truncated) {
    }

    private Licence() {
    }

    /** Where a namespace's licence is looked for first, as a path worth printing. */
    public static String pathIn(String namespace) {
        return "data/" + namespace + "/" + PATH;
    }

    /**
     * The first lines of a licence, and how many are left.
     *
     * <p>Blank lines are skipped and every line is stripped before anything else.
     * Apache and the GPL both open with blank lines and a centred title, so a
     * summary that took the first three lines as written would show two empty ones
     * and a run of spaces.
     */
    public static Summary summarise(String text, boolean truncated) {
        List<String> shown = new ArrayList<>();
        int lines = 0;
        for (String raw : text.split("\r\n|\r|\n", -1)) {
            String line = raw.strip();
            if (line.isEmpty()) {
                continue;
            }
            lines++;
            if (shown.size() < LINES_SHOWN) {
                shown.add(cut(line));
            }
        }
        return new Summary(List.copyOf(shown), Math.max(0, lines - shown.size()),
                truncated);
    }

    private static String cut(String line) {
        return line.length() <= MAX_LINE ? line
                : line.substring(0, MAX_LINE - 3) + "...";
    }

    // ------------------------------------------------------------------- notice

    /**
     * One file carrying every statement a pack has to pass on, or null for none.
     *
     * <p>An exported pack has one namespace and the assets in it may have come from
     * several, so the statements are stacked under headings naming where each came
     * from. Reproduced unchanged: a licence summarised or reworded is no longer the
     * licence.
     *
     * <p><b>Idempotent.</b> Where a statement is itself a notice this wrote, its
     * blocks are passed through instead of being wrapped again. Without that, a pack
     * compiled from an imported pack that was itself compiled from an import would
     * nest one heading inside another and label the first author's terms with the
     * second author's namespace, which is a false statement about somebody's work
     * rather than an untidy file.
     */
    @Nullable
    public static String notice(Map<String, String> byNamespace) {
        Map<String, String> blocks = carriedFrom(byNamespace);
        if (blocks.isEmpty()) {
            return null;
        }
        StringBuilder out = new StringBuilder(MARKER).append('\n');
        out.append("#\n");
        out.append("# Each block below is reproduced unchanged and covers the "
                + "material that came\n");
        out.append("# from the namespace naming it. The terms of this pack itself "
                + "are not stated\n");
        out.append("# here: replacing this file is how to state them.\n");
        for (Map.Entry<String, String> e : blocks.entrySet()) {
            out.append('\n').append(RULE).append(' ').append(e.getKey())
                    .append(' ').append(RULE).append('\n');
            out.append(e.getValue().stripTrailing()).append('\n');
        }
        return out.toString();
    }

    /**
     * Which namespaces a set of statements will end up carried under.
     *
     * <p>Ordinarily one per namespace given. A statement that is itself a notice
     * contributes the namespaces it was carrying instead of its own, which is what
     * makes {@link #notice} idempotent, and it is also the honest count to report:
     * a pack passing three statements through carries three, not one.
     */
    public static Map<String, String> carriedFrom(Map<String, String> byNamespace) {
        Map<String, String> blocks = new TreeMap<>();
        for (Map.Entry<String, String> e : byNamespace.entrySet()) {
            Map<String, String> inner = blocksOf(e.getValue());
            if (inner == null) {
                blocks.put(e.getKey(), e.getValue());
            } else {
                blocks.putAll(inner);
            }
        }
        return blocks;
    }

    /**
     * The statements inside a notice this wrote, or null where the text is not one.
     *
     * <p>Only a text opening with {@link #MARKER} is read this way. Nothing else
     * writes that line, so an ordinary licence that happens to contain a heading
     * shaped like the separator is still carried whole.
     */
    @Nullable
    public static Map<String, String> blocksOf(String text) {
        String[] lines = text.split("\r\n|\r|\n", -1);
        if (lines.length == 0 || !lines[0].strip().equals(MARKER)) {
            return null;
        }
        Map<String, String> out = new LinkedHashMap<>();
        String namespace = null;
        StringBuilder body = new StringBuilder();
        for (String line : lines) {
            String heading = headingOf(line);
            if (heading != null) {
                if (namespace != null) {
                    out.put(namespace, body.toString().stripTrailing());
                }
                namespace = heading;
                body.setLength(0);
                continue;
            }
            if (namespace != null) {
                body.append(line).append('\n');
            }
        }
        if (namespace != null) {
            out.put(namespace, body.toString().stripTrailing());
        }
        return out;
    }

    /** The namespace a separator line names, or null where the line is not one. */
    @Nullable
    private static String headingOf(String line) {
        String t = line.strip();
        if (!t.startsWith(RULE + " ") || !t.endsWith(" " + RULE)) {
            return null;
        }
        String name = t.substring(RULE.length() + 1,
                t.length() - RULE.length() - 1).strip();
        return name.isEmpty() || name.contains(" ") ? null : name;
    }
}
