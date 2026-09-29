package com.rinkynooble.lostcitiesdevtool.workshop;

import com.rinkynooble.lostcitiesdevtool.core.Layout;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.LevelChunkSection;

/**
 * The blocks standing on a plot, walked once, with the empty sections stepped over.
 *
 * <p>Three places walked a plot from its floor to its top one position at a time,
 * through the level: counting what a wipe would remove, removing it, and clearing a
 * plot before an import pastes into it. Most of that volume is air, and a chunk
 * keeps a flag per sixteen-block section that says so, so a section holding only
 * air is passed over whole instead of being read a block at a time.
 */
public final class PlotVolume {

    /** One block that is not air. The position is reused; copy it to keep it. */
    @FunctionalInterface
    public interface Visitor {
        void visit(BlockPos.MutableBlockPos pos, BlockState state);
    }

    private PlotVolume() {
    }

    /** Every block that is not air on a plot, from its floor up to {@code top}, exclusive. */
    public static void forEachSolid(ServerLevel level, Layout.Plot plot, int top,
                                    Visitor visitor) {
        int ceiling = Math.min(top, level.getMaxBuildHeight());
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int cx = plot.cx(); cx < plot.cx() + plot.width(); cx++) {
            for (int cz = plot.cz(); cz < plot.cz() + plot.height(); cz++) {
                LevelChunk chunk = level.getChunk(cx, cz);
                int y = Boundaries.BASE;
                while (y < ceiling) {
                    int index = chunk.getSectionIndex(y);
                    int end = Math.min(ceiling, SectionPos.sectionToBlockCoord(
                            chunk.getSectionYFromSectionIndex(index)) + 16);
                    LevelChunkSection section = chunk.getSection(index);
                    if (!section.hasOnlyAir()) {
                        for (int by = y; by < end; by++) {
                            for (int lx = 0; lx < 16; lx++) {
                                for (int lz = 0; lz < 16; lz++) {
                                    BlockState state = section.getBlockState(lx,
                                            by & 15, lz);
                                    if (!state.isAir()) {
                                        pos.set(cx * 16 + lx, by, cz * 16 + lz);
                                        visitor.visit(pos, state);
                                    }
                                }
                            }
                        }
                    }
                    y = end;
                }
            }
        }
    }

    /** How many blocks that are not air stand on a plot below {@code top}. */
    public static long count(ServerLevel level, Layout.Plot plot, int top) {
        long[] count = {0};
        forEachSolid(level, plot, top, (pos, state) -> count[0]++);
        return count[0];
    }

    /**
     * Remove every block on a plot below {@code top}, and say how many there were.
     *
     * <p>Flag 2: clients hear about it, neighbours do not. What is being removed is
     * the whole plot, so nothing next to one block is worth updating.
     */
    public static int clear(ServerLevel level, Layout.Plot plot, int top) {
        BlockState air = Blocks.AIR.defaultBlockState();
        int[] removed = {0};
        forEachSolid(level, plot, top, (pos, state) -> {
            level.setBlock(pos, air, 2);
            removed[0]++;
        });
        return removed[0];
    }
}
