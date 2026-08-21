package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.rinkynooble.lostcitiesdevtool.json5.Json5;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;

import javax.annotation.Nullable;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * A plot's settings, on disk, one file each.
 *
 * <p><b>The file is the truth.</b> Not an item, not a book, not saved data inside the
 * region files. A file can be read without the game running, diffed, kept in version
 * control, fixed in a text editor when something goes wrong, and cannot be dropped in
 * lava. What the game offers on top is a way to edit it without leaving.
 *
 * <p>Written as JSON5 with the schema's own help text as comments, so the file
 * explains itself to whoever opens it next. Read back through the same sanitiser the
 * mod already uses for Lost Cities assets, which blanks comments and trailing commas
 * while keeping every other character at its original offset, so a parse error still
 * points at the right line.
 *
 * <p><b>Keys are quoted.</b> This mod's JSON5 is deliberately a narrow subset,
 * comments and trailing commas and nothing else, so a file written with it is still
 * ordinary JSON to every other tool. Emitting unquoted keys would have made these
 * files readable only by this mod, which is the opposite of the reason they are
 * files at all.
 */
public final class SettingsStore {

    private static final String DIR = "lostcitiesdevtool";
    private static final String PLOTS = "plots";

    private SettingsStore() {
    }

    public static Path root(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve(DIR).resolve(PLOTS)
                .toAbsolutePath().normalize();
    }

    /** One file per plot. The plot id's slashes become folders, which is tidy. */
    public static Path pathOf(MinecraftServer server, String plotId) {
        Path p = root(server);
        for (String part : plotId.split("/")) {
            p = p.resolve(part);
        }
        return p.getParent().resolve(p.getFileName() + ".json5");
    }

    public static boolean exists(MinecraftServer server, String plotId) {
        return Files.isRegularFile(pathOf(server, plotId));
    }

    /**
     * Load a plot's settings, or an empty object where there is no file.
     *
     * @throws IOException with a message worth showing, when the file exists and
     *                     cannot be read or parsed
     */
    public static JsonObject load(MinecraftServer server, String plotId)
            throws IOException {
        Path path = pathOf(server, plotId);
        if (!Files.isRegularFile(path)) {
            return new JsonObject();
        }
        String text = Files.readString(path, StandardCharsets.UTF_8);
        try {
            JsonElement parsed = JsonParser.parseString(Json5.sanitise(text));
            if (!parsed.isJsonObject()) {
                throw new IOException("the file holds "
                        + (parsed.isJsonArray() ? "a list" : "a value")
                        + " where an object was expected");
            }
            return parsed.getAsJsonObject();
        } catch (RuntimeException e) {
            throw new IOException(e.getMessage() == null
                    ? e.getClass().getSimpleName() : e.getMessage());
        }
    }

    public static void save(MinecraftServer server, String plotId,
                            @Nullable Catalogue.Row row, JsonObject values)
            throws IOException {
        Path path = pathOf(server, plotId);
        Files.createDirectories(path.getParent());
        Files.writeString(path, render(plotId, row, values), StandardCharsets.UTF_8);
    }

    /** Delete the file rather than leaving an empty one behind. */
    public static boolean delete(MinecraftServer server, String plotId)
            throws IOException {
        return Files.deleteIfExists(pathOf(server, plotId));
    }

    // ------------------------------------------------------------------ writing

    /**
     * JSON5, with the schema's help above each key it recognises.
     *
     * <p>The comments are the point. A settings file somebody opens six months later
     * should say what its keys mean without them going to look, and the same text is
     * what tab completion shows, so the two cannot drift.
     */
    static String render(String plotId, @Nullable Catalogue.Row row,
                         JsonObject values) {
        StringBuilder out = new StringBuilder();
        out.append("// ").append(plotId).append('\n');
        if (row == null) {
            out.append("// The pack's own settings. Namespace, profile, world style, "
                    + "output format.\n");
        } else {
            out.append("// ").append(describe(row)).append('\n');
            if (row.dead() != null) {
                out.append("//\n// WARNING: ").append(wrap(row.dead(), "// "))
                        .append('\n');
            }
        }
        out.append("//\n// Written by /lcdev plot set. Safe to edit by hand: this "
                + "file is the truth,\n// and the game reads it back.\n");
        out.append("{\n");

        List<Settings.Field> fields = Settings.fieldsFor(row);
        boolean first = true;
        for (Settings.Field f : fields) {
            if (!values.has(f.name())) {
                continue;
            }
            if (!first) {
                out.append('\n');
            }
            first = false;
            out.append(wrap(f.help(), "  // ")).append('\n');
            out.append("  \"").append(f.name()).append("\": ")
                    .append(compact(values.get(f.name()))).append(",\n");
        }

        // Anything the schema does not know: the raw escape hatch, the scope
        // containers, and marks. Written verbatim so an unsupported key never blocks
        // anyone and never gets quietly dropped.
        for (String key : values.keySet()) {
            if (Settings.field(row, key) != null) {
                continue;
            }
            if (!first) {
                out.append('\n');
            }
            first = false;
            out.append(wrap(explain(key), "  // ")).append('\n');
            out.append("  \"").append(key).append("\": ")
                    .append(pretty(values.get(key), "  ")).append(",\n");
        }
        out.append("}\n");
        return out.toString();
    }

    private static String describe(Catalogue.Row row) {
        String what = switch (row.kind()) {
            case SINGLE -> "one variation only, because the codec takes a string";
            case PART_LIST -> "any number of variations, picked uniform random";
            case SELECTOR -> "any number of variations, each weighted by its factor";
        };
        return row.family() + " " + row.key() + ": " + what + ". Compiles into "
                + (row.cityStyleScoped() ? "a city style." : "the world style.");
    }

    private static String explain(String key) {
        return switch (key) {
            case "raw" -> "Merged into the output verbatim. The escape hatch for "
                    + "anything the schema here does not cover yet.";
            case "chunks" -> "Per chunk overrides, keyed by offset from the plot's "
                    + "own corner. Only what differs from above.";
            case "levels" -> "Per level overrides. Only what differs from above.";
            case "marks" -> "Palette keys attached to a block position, keyed x,y,z. "
                    + "Written by /lcdev mark.";
            default -> "Not a key this version's schema knows. Kept as written.";
        };
    }

    /** One line per value, because a settings file is read more than it is edited. */
    private static String compact(JsonElement e) {
        return new GsonBuilder().create().toJson(e);
    }

    private static String pretty(JsonElement e, String indent) {
        String text = new GsonBuilder().setPrettyPrinting().create().toJson(e);
        return text.replace("\n", "\n" + indent);
    }

    /** Hard wrap, because chat and editors both cope badly with a very long line. */
    private static String wrap(String text, String prefix) {
        StringBuilder out = new StringBuilder(prefix);
        int column = prefix.length();
        for (String word : text.split(" ")) {
            if (column + word.length() > 78) {
                out.append('\n').append(prefix);
                column = prefix.length();
            }
            out.append(word).append(' ');
            column += word.length() + 1;
        }
        return out.toString().stripTrailing();
    }
}
