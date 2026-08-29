package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonObject;
import com.rinkynooble.lostcitiesdevtool.validate.Finding;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Emptying the workshop, and knowing what that would cost first.
 *
 * <p>An import fills the plots its pack needs and leaves the rest alone, which is
 * what anyone who has built something by hand would want. The cost is that
 * importing a second city on top of a first leaves the first one's plots exactly
 * where they were, so the workshop holds two cities and an export writes both into
 * one pack. Emptying it is therefore a thing somebody has to be able to ask for.
 *
 * <p><b>It cannot be asked for by accident.</b> The command reports and stops unless
 * it is confirmed, and a confirmed wipe writes a full backup pack before it destroys
 * anything. A backup that cannot be written stops the wipe rather than being skipped.
 */
public final class Wipe {

    /**
     * What a wipe would remove.
     *
     * @param plots  plots holding settings or holding blocks, whichever it is
     * @param blocks solid blocks standing in those plots
     */
    public record Survey(int plots, long blocks, List<String> ids) {

        public boolean isEmpty() {
            return plots == 0 && blocks == 0;
        }
    }

    private Wipe() {
    }

    /**
     * Count what is there, touching nothing.
     *
     * <p>Blocks are counted per plot rather than estimated, because the number is
     * the whole point of the prompt: "34 plots" is abstract and "34 plots, 210,000
     * blocks" is a thing somebody recognises as their afternoon.
     */
    public static Survey survey(MinecraftServer server, ServerLevel level)
            throws IOException {
        List<String> ids = new ArrayList<>();
        long blocks = 0;
        for (Layout.Plot plot : Layout.plots()) {
            if (plot.row() == null) {
                continue;
            }
            JsonObject settings = SettingsStore.load(server, plot.id());
            long solid = solidIn(level, plot, Boundaries.topOf(level, plot, settings));
            // Settings or blocks, either on its own. A plot whose settings were
            // deleted while its blocks stayed is exactly the state this has to be
            // able to see, because it is the state a wipe used to leave behind.
            if (settings.keySet().isEmpty() && solid == 0) {
                continue;
            }
            ids.add(plot.id());
            blocks += solid;
        }
        return new Survey(ids.size(), blocks, ids);
    }

    /**
     * Empty every plot, and forget the rows an import grew.
     *
     * <p>The core settings and the palette ledger are deliberately kept. The core
     * plot holds the pack's own identity, its namespace and name, which is the
     * author's rather than any imported city's; the ledger holds which character
     * stands for which block, and keeping it means the next export letters the same
     * blocks the same way instead of producing a whole-file diff.
     *
     * @return how many plots were emptied
     */
    public static int run(MinecraftServer server, ServerLevel level)
            throws IOException {
        int emptied = 0;
        for (Layout.Plot plot : Layout.plots()) {
            if (plot.row() == null) {
                continue;
            }
            JsonObject settings = SettingsStore.load(server, plot.id());
            boolean had = !settings.keySet().isEmpty();
            int removed = clear(level, plot, Boundaries.topOf(level, plot, settings));
            if (!had && removed == 0) {
                continue;
            }
            if (had) {
                SettingsStore.delete(server, plot.id());
            }
            emptied++;
        }
        // Rows an import grew go back to their catalogue size. Leaving them long
        // would keep painting floors for plots nothing is built on.
        Layout.setGrown(java.util.Map.of());
        // The statements imported assets brought with them go with the assets. The
        // backup was written before any of this, so it still carries them.
        Attribution.forget(server);
        Workshop.build(level);
        return emptied;
    }

    /** A backup pack, named for the moment it was taken. */
    public static Path backup(MinecraftServer server, ServerLevel level)
            throws IOException {
        String stamp = java.time.LocalDateTime.now()
                .format(java.time.format.DateTimeFormatter
                        .ofPattern("yyyy-MM-dd-HHmmss"));
        Path root = Exporter.backupsRoot(server).resolve(stamp);
        Files.createDirectories(root.getParent());
        // Whole and tagged whatever the last export was told, because a backup
        // exists to put things back exactly as they were.
        Exporter.Result result = Exporter.run(server, level, stamp,
                Exporter.Options.backupTo(root));
        if (result.failed()) {
            // The first ERROR, not the first finding: `findings` carries the asset
            // check's warnings too, in discovery order. This is the message somebody
            // reads immediately before a wipe, so naming the wrong cause here is the
            // worst place in the mod for it.
            throw new IOException("the backup could not be written: "
                    + Finding.firstError(result.findings(), "no error was recorded"));
        }
        return root;
    }

    /** Solid blocks standing on one plot, from its floor up to {@code top}. */
    private static long solidIn(ServerLevel level, Layout.Plot plot, int top) {
        long count = 0;
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int y = Boundaries.BASE; y < top; y++) {
            for (int x = plot.blockMinX(); x <= plot.blockMaxX(); x++) {
                for (int z = plot.blockMinZ(); z <= plot.blockMaxZ(); z++) {
                    pos.set(x, y, z);
                    if (!level.getBlockState(pos).isAir()) {
                        count++;
                    }
                }
            }
        }
        return count;
    }

    /** @return how many blocks were removed */
    private static int clear(ServerLevel level, Layout.Plot plot, int top) {
        BlockState air = Blocks.AIR.defaultBlockState();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int removed = 0;
        for (int y = Boundaries.BASE; y < top; y++) {
            for (int x = plot.blockMinX(); x <= plot.blockMaxX(); x++) {
                for (int z = plot.blockMinZ(); z <= plot.blockMaxZ(); z++) {
                    pos.set(x, y, z);
                    if (!level.getBlockState(pos).isAir()) {
                        level.setBlock(pos, air, 2);
                        removed++;
                    }
                }
            }
        }
        return removed;
    }
}
