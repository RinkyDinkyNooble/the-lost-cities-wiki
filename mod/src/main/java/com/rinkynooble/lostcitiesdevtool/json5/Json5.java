package com.rinkynooble.lostcitiesdevtool.json5;

import net.minecraft.resources.FileToIdConverter;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Accepts comments and trailing commas in Lost Cities asset files.
 *
 * <p>This is a subset of JSON5, not the whole of it. Comments and trailing commas
 * are what a hand-written asset file wants, and both are rejected by strict JSON with
 * a message that names an offset rather than a cause. Unquoted keys, single quotes
 * and the rest of JSON5 are deliberately not accepted: they change what a valid file
 * looks like without solving a problem an author actually has, and a file written
 * with them would not load for anyone without this mod.
 *
 * <p><b>Scoped by path.</b> Only resources under {@code lostcities/} are touched. No
 * other mod's files, and none of Minecraft's own, are affected.
 *
 * <p>Comments and trailing commas are replaced with spaces rather than deleted, so
 * every remaining character keeps its original offset and line. A parse error, and
 * the line numbers the asset check reports, still point at the right place in the
 * file the author wrote.
 */
public final class Json5 {

    /** The datapack folder every Lost Cities asset lives under. */
    private static final String PREFIX = "lostcities/";

    /** The namespace and folder a Lost Cities datapack registry is rooted at. */
    private static final String ROOT = "lostcities";

    public static final String EXT_JSON = ".json";
    public static final String EXT_JSON5 = ".json5";

    /**
     * A location no pack will hold, used to read a converter's folder and extension
     * back out of it. See {@link #folderOf}.
     */
    private static final String PROBE = "lcdevprobe";

    private Json5() {
    }

    public static boolean appliesTo(ResourceLocation location) {
        return location.getPath().startsWith(PREFIX)
                && location.getPath().endsWith(EXT_JSON);
    }

    /** True for a resource folder that a Lost Cities datapack registry reads from. */
    public static boolean appliesToFolder(String folder) {
        return ROOT.equals(folder) || folder.startsWith(PREFIX);
    }

    /**
     * The {@code .json} location a {@code .json5} file stands in for.
     *
     * <p>Presenting the file under this name is what makes the extension work without
     * touching {@link FileToIdConverter#fileToId}, which strips a fixed number of
     * characters and would otherwise leave a trailing {@code 5} in the id. A dot is a
     * legal character in a resource path, so that would not throw: the asset would
     * simply register under a name nothing references.
     */
    public static ResourceLocation asJson(ResourceLocation json5) {
        String path = json5.getPath();
        return new ResourceLocation(json5.getNamespace(),
                path.substring(0, path.length() - EXT_JSON5.length()) + EXT_JSON);
    }

    /**
     * The folder a converter reads, or {@code null} if it does not read {@code .json}.
     *
     * <p>The folder is a private field. Rather than shadow it, which binds this mixin
     * to a mapping for a vanilla class, the converter is asked to build the file name
     * for a location that cannot exist and the answer is read back. The result is
     * {@code folder + "/" + PROBE + extension}, so both parts fall out of one public
     * call.
     */
    public static String folderOf(FileToIdConverter converter) {
        String path = converter.idToFile(new ResourceLocation(ROOT, PROBE)).getPath();
        int at = path.lastIndexOf(PROBE);
        if (at <= 0 || !EXT_JSON.equals(path.substring(at + PROBE.length()))) {
            return null;
        }
        return path.substring(0, at - 1);
    }

    /** The name a profile or asset file registers under: everything before the first dot. */
    public static String baseName(String fileName) {
        int dot = fileName.indexOf('.');
        return dot < 0 ? fileName : fileName.substring(0, dot);
    }

    /** A resource that yields the same file with comments and trailing commas blanked. */
    public static Resource wrap(Resource original) {
        return new Resource(original.source(), () -> relax(original.open()));
    }

    private static InputStream relax(InputStream in) throws IOException {
        String text;
        try (InputStream stream = in) {
            text = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
        return new ByteArrayInputStream(
                sanitise(text).getBytes(StandardCharsets.UTF_8));
    }

    /**
     * Blank out comments and trailing commas, preserving every other offset.
     *
     * <p>Both passes track string literals, because a {@code //} inside a block state
     * string or a comma inside a name is content, not syntax.
     */
    public static String sanitise(String text) {
        char[] c = text.toCharArray();
        blankComments(c);
        blankTrailingCommas(c);
        return new String(c);
    }

    private static void blankComments(char[] c) {
        boolean inString = false;
        boolean escaped = false;
        for (int i = 0; i < c.length; i++) {
            char ch = c[i];
            if (inString) {
                if (escaped) {
                    escaped = false;
                } else if (ch == '\\') {
                    escaped = true;
                } else if (ch == '"') {
                    inString = false;
                }
                continue;
            }
            if (ch == '"') {
                inString = true;
                continue;
            }
            if (ch != '/' || i + 1 >= c.length) {
                continue;
            }
            if (c[i + 1] == '/') {
                int j = i;
                while (j < c.length && c[j] != '\n') {
                    c[j++] = ' ';
                }
                i = j - 1;
            } else if (c[i + 1] == '*') {
                int j = i + 2;
                while (j + 1 < c.length && !(c[j] == '*' && c[j + 1] == '/')) {
                    j++;
                }
                int end = Math.min(j + 2, c.length);
                for (int k = i; k < end; k++) {
                    // Newlines stay, so a block comment does not collapse the line
                    // numbering of everything after it.
                    if (c[k] != '\n') {
                        c[k] = ' ';
                    }
                }
                i = end - 1;
            }
        }
    }

    private static void blankTrailingCommas(char[] c) {
        boolean inString = false;
        boolean escaped = false;
        for (int i = 0; i < c.length; i++) {
            char ch = c[i];
            if (inString) {
                if (escaped) {
                    escaped = false;
                } else if (ch == '\\') {
                    escaped = true;
                } else if (ch == '"') {
                    inString = false;
                }
                continue;
            }
            if (ch == '"') {
                inString = true;
                continue;
            }
            if (ch != ',') {
                continue;
            }
            int j = i + 1;
            while (j < c.length && Character.isWhitespace(c[j])) {
                j++;
            }
            if (j < c.length && (c[j] == '}' || c[j] == ']')) {
                c[i] = ' ';
            }
        }
    }
}
