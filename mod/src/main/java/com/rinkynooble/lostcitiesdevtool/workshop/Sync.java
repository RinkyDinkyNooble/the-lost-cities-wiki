package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

/**
 * Making the workshop agree with settings files edited outside the game.
 *
 * <p><b>Values need no syncing.</b> {@link SettingsStore#load} reads the file every
 * time it is asked, so a number changed in an editor is already what the next export
 * compiles. This is not a cache being refreshed.
 *
 * <p>What can disagree is whether the workshop can see the file at all. A settings
 * file names a plot, a plot belongs to a row, and a row lays out a fixed number of
 * plots. Write {@code building/1x1/20.json5} into a row holding eight and nothing is
 * wrong with the file: it simply describes a plot that does not exist, so every
 * command walking the catalogue steps straight past it and an export writes a pack
 * without it. Nothing reports that today, because nothing looks.
 *
 * <p>So this walks the files rather than the plots, which is the only way round that
 * can see one the other does not have, and then grows the rows to cover what it
 * found. It also reads each file for keys the plot has no use for, since a
 * mistyped key is silently ignored everywhere else.
 */
public final class Sync {

    /**
     * Keys that structure a settings file rather than set a value.
     *
     * <p>None of them are fields, so a key check has to know them or it reports the
     * scope containers and the escape hatch as mistakes.
     */
    private static final Set<String> STRUCTURAL =
            Set.of("chunks", "levels", "raw", "marks", "conversions");

    /** Something about one file worth saying out loud. */
    public record Note(String plotId, String what) {
    }

    /**
     * @param files   settings files found on disk
     * @param plots   of those, ones the catalogue already had a plot for
     * @param grown   row id to its new size, for rows that had to grow
     * @param notes   files that need somebody to look at them
     */
    public record Report(int files, int plots, Map<String, Integer> grown,
                         List<Note> notes) {

        public boolean quiet() {
            return grown.isEmpty() && notes.isEmpty();
        }
    }

    private Sync() {
    }

    public static Report run(MinecraftServer server, ServerLevel level)
            throws IOException {
        // root() already is the plots folder. Resolving "plots" onto it looked for
        // a folder inside it and quietly found nothing, which reads as an empty
        // workshop rather than a wrong path.
        Path root = SettingsStore.root(server);
        List<String> ids = new ArrayList<>();
        if (Files.isDirectory(root)) {
            try (Stream<Path> walk = Files.walk(root)) {
                walk.filter(Files::isRegularFile)
                        .filter(p -> p.getFileName().toString().endsWith(".json5"))
                        .forEach(p -> {
                            String rel = root.relativize(p).toString()
                                    .replace('\\', '/');
                            ids.add(rel.substring(0, rel.length() - ".json5".length()));
                        });
            }
        }
        ids.sort(String::compareTo);

        List<Note> notes = new ArrayList<>();
        Map<String, Integer> needed = new LinkedHashMap<>();
        int known = 0;

        for (String id : ids) {
            JsonObject settings;
            try {
                settings = SettingsStore.load(server, id);
            } catch (IOException e) {
                notes.add(new Note(id, "could not be read: " + e.getMessage()));
                continue;
            }

            if (Layout.CORE_ID.equals(id)) {
                known++;
                notes.addAll(strayKeys(id, settings, null));
                continue;
            }

            int slash = id.lastIndexOf('/');
            Catalogue.Row row = slash < 0 ? null
                    : Catalogue.row(id.substring(0, slash));
            if (row == null) {
                notes.add(new Note(id, "names no row in the catalogue, so nothing "
                        + "will ever read it"));
                continue;
            }

            int index;
            try {
                index = Integer.parseInt(id.substring(slash + 1));
            } catch (NumberFormatException e) {
                notes.add(new Note(id, "does not end in a plot number"));
                continue;
            }

            notes.addAll(strayKeys(id, settings, row));
            if (index < Layout.plotsIn(row)) {
                known++;
            } else {
                // Rows are grown to the highest index seen rather than one at a
                // time, so a file for plot 20 in a row of eight brings 8 to 20
                // along with it. The plots between are laid out empty, which is
                // what a row of that length means.
                needed.merge(row.id(), index + 1, Math::max);
            }
        }

        Map<String, Integer> grown = new LinkedHashMap<>();
        for (Map.Entry<String, Integer> e : needed.entrySet()) {
            Catalogue.Row row = Catalogue.row(e.getKey());
            if (row != null && row.kind() == Catalogue.Kind.SINGLE) {
                notes.add(new Note(e.getKey(), "holds one plot however many files "
                        + "name it, because a list where the mod takes a string is "
                        + "a load error rather than a bigger row"));
                continue;
            }
            // The command that grows a row by hand is capped, and this is the
            // same growing reached from a file name instead. A stray
            // `building/1x1/99999.json5` would otherwise lay out a hundred
            // thousand plots and paint every floor, on the server thread, because
            // of a typo.
            if (e.getValue() > Layout.MAX_PLOTS_IN_ROW) {
                notes.add(new Note(e.getKey(), "would have to hold " + e.getValue()
                        + " plots to reach a file naming one, and "
                        + Layout.MAX_PLOTS_IN_ROW + " is the most a row lays out. "
                        + "The row was left alone."));
                continue;
            }
            Layout.grow(e.getKey(), e.getValue());
            grown.put(e.getKey(), e.getValue());
        }
        if (!grown.isEmpty()) {
            // Only when something grew. Repainting is thousands of blocks and
            // there is nothing to repaint when the layout did not move.
            Workshop.build(level);
        }
        return new Report(ids.size(), known, grown, notes);
    }

    /**
     * Keys the plot has no use for.
     *
     * <p>Worth saying because nothing else says it. A mistyped key is not an error
     * anywhere: the export reads the keys it knows and steps over the rest, so
     * {@code floor} where {@code floors} was meant produces a one storey building
     * and no complaint.
     */
    private static List<Note> strayKeys(String id, JsonObject settings,
                                        Catalogue.Row row) {
        List<String> known = new ArrayList<>(STRUCTURAL);
        Settings.fieldsFor(row).forEach(f -> known.add(f.name()));
        List<Note> out = new ArrayList<>();
        for (String key : settings.keySet()) {
            if (!known.contains(key)) {
                out.add(new Note(id, "has a key this plot does not use: " + key));
            }
        }
        return out;
    }
}
