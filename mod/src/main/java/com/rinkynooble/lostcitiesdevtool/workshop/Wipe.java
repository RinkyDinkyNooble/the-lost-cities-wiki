package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonObject;
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
     * @param plots  plots holding settings, so plots an export would write out
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
            if (settings.keySet().isEmpty()) {
                continue;
            }
            ids.add(plot.id());
            blocks += solidIn(level, plot, ceiling(settings));
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
            if (settings.keySet().isEmpty()) {
                continue;
            }
            clear(level, plot, ceiling(settings));
            SettingsStore.delete(server, plot.id());
            emptied++;
        }
        // Rows an import grew go back to their catalogue size. Leaving them long
        // would keep painting floors for plots nothing is built on.
        Layout.setGrown(java.util.Map.of());
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
        Exporter.Result result = Exporter.run(server, level, stamp, true, root);
        if (result.failed()) {
            throw new IOException("the backup could not be written: "
                    + result.findings().get(0).message());
        }
        return root;
    }

    /**
     * How far up a plot is worth reading.
     *
     * <p>The same extent an export would read, which is the extent the settings
     * describe. Anything above it was never part of the asset.
     */
    private static int ceiling(JsonObject settings) {
        List<Boundaries.Line> lines = Boundaries.of(settings);
        int top = lines.get(lines.size() - 1).y();
        int height = settings.has("height") ? intOf(settings, "height") : 0;
        return Math.max(top, Boundaries.BASE + height);
    }

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

    private static void clear(ServerLevel level, Layout.Plot plot, int top) {
        BlockState air = Blocks.AIR.defaultBlockState();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int y = Boundaries.BASE; y < top; y++) {
            for (int x = plot.blockMinX(); x <= plot.blockMaxX(); x++) {
                for (int z = plot.blockMinZ(); z <= plot.blockMaxZ(); z++) {
                    pos.set(x, y, z);
                    if (!level.getBlockState(pos).isAir()) {
                        level.setBlock(pos, air, 2);
                    }
                }
            }
        }
    }

    private static int intOf(JsonObject o, String key) {
        try {
            return o.get(key).getAsInt();
        } catch (RuntimeException e) {
            return 0;
        }
    }
}
