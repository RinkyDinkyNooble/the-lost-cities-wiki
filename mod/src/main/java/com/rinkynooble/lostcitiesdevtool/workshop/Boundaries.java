package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

import java.util.ArrayList;
import java.util.List;

/**
 * Where one level stops and the next begins, drawn on the walkway around a plot.
 *
 * <p>Stacking the top variations above the floors saves a great deal of room, and it
 * costs the one thing a build normally gives you for free: seeing where the compiler
 * thinks the boundaries are. The split comes from the settings, and nothing in the
 * world shows it. This draws it, on request, and rubs it out again.
 *
 * <p><b>On the walkway, never inside the plot.</b> A preview that overwrote what
 * somebody had built would be worse than no preview.
 */
public final class Boundaries {

    /** The first buildable block, one above the plot floor. */
    public static final int BASE = Layout.FLOOR_Y + 1;

    /** The stride between levels. Not the height of a part, which is free. */
    public static final int STRIDE = 6;

    /**
     * The shortest level of a building that draws anything.
     *
     * <p>Measured: a part of one slice used as a level of a building places no
     * blocks at all and the building's filler occupies the space instead. So a top
     * shorter than this is raised rather than honoured, and everything that reasons
     * about where a level ends has to agree about that, or the preview draws its
     * lines somewhere the compiler will not cut.
     *
     * <p><b>Levels of a building only.</b> A part that is not stacked into one is
     * fine at a single slice, and the mod's own street parts all are: a road is one
     * layer of blocks and every street shape it ships is written that way. Raising
     * those would rewrite somebody's road on the way through.
     */
    public static final int MIN_HEIGHT = 2;

    /** One boundary line: the height it sits at, and what it separates. */
    public record Line(int y, String label, Kind kind) {
    }

    public enum Kind { CELLAR, GROUND, FLOOR, TOP }

    private Boundaries() {
    }

    /**
     * The lines for a plot, read upward from its floor.
     *
     * <p>Cellars sit above the plot floor like everything else, deepest first, then
     * the ground floor, then the upper floors, then the top variations one after
     * another. Every level below the tops is a stride of 6 apart; each top carries
     * its own declared height, which is legal only because nothing is placed above a
     * top.
     */
    public static List<Line> of(JsonObject settings) {
        int cellars = Math.max(0, intOf(settings, "cellars", 0));
        int floors = Math.max(0, intOf(settings, "floors", 1));
        List<Integer> tops = intsOf(settings, "tops");

        List<Line> out = new ArrayList<>();
        int y = BASE;
        for (int c = cellars; c >= 1; c--) {
            out.add(new Line(y, "cellar " + (-c), Kind.CELLAR));
            y += STRIDE;
        }
        out.add(new Line(y, "ground", Kind.GROUND));
        y += STRIDE;
        for (int f = 1; f <= floors; f++) {
            out.add(new Line(y, "floor " + f, Kind.FLOOR));
            y += STRIDE;
        }
        for (int t = 0; t < tops.size(); t++) {
            out.add(new Line(y, "top " + (t + 1) + ", " + tops.get(t) + " tall",
                    Kind.TOP));
            y += Math.max(MIN_HEIGHT, tops.get(t));
        }
        // The line above the last thing, so the top of the build is visible too.
        out.add(new Line(y, tops.isEmpty() ? "above the top floor" : "above the tops",
                Kind.TOP));
        return out;
    }

    /**
     * The highest block standing on a plot, or one below the floor for none.
     *
     * <p>Read from the world, because only the world knows. Answered from the
     * chunk's surface heightmap, so a plot costs one lookup a column rather than a
     * read of every block in it.
     */
    public static int highestIn(ServerLevel level, Layout.Plot plot) {
        int highest = BASE - 1;
        for (int x = plot.blockMinX(); x <= plot.blockMaxX(); x++) {
            for (int z = plot.blockMinZ(); z <= plot.blockMaxZ(); z++) {
                highest = Math.max(highest,
                        level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z) - 1);
            }
        }
        return Math.min(highest, level.getMaxBuildHeight() - 1);
    }

    /**
     * How far up a plot is worth reading or clearing, exclusive.
     *
     * <p>Whichever is higher: what is standing there, or what the settings describe.
     *
     * <p><b>Both halves, always.</b> Trusting the settings alone is what left the
     * tops of buildings floating over cleared plots, because nothing makes what is
     * actually built agree with what the settings claim. Trusting the world alone
     * would read nothing on a plot whose asset is declared and not yet built.
     *
     * <p>This lived in three places and was wrong in all three the same way, which
     * is why it is one place now.
     */
    public static int topOf(ServerLevel level, Layout.Plot plot,
                            JsonObject settings) {
        int top = highestIn(level, plot) + 1;
        if (settings.keySet().isEmpty()) {
            return top;
        }
        List<Line> lines = of(settings);
        int height = intOf(settings, "height", 0);
        return Math.max(top, Math.max(lines.get(lines.size() - 1).y(),
                BASE + height));
    }

    /** Draw them. Returns how many blocks were placed. */
    public static int show(ServerLevel level, Layout.Plot plot, JsonObject settings) {
        List<Line> lines = of(settings);
        hide(level, plot, highest(lines) + STRIDE);
        int placed = 0;
        for (Line line : lines) {
            if (line.y() > level.getMaxBuildHeight() - 1) {
                continue;
            }
            BlockState state = switch (line.kind()) {
                case GROUND -> Blocks.RED_STAINED_GLASS.defaultBlockState();
                case CELLAR -> Blocks.BROWN_STAINED_GLASS.defaultBlockState();
                case TOP -> Blocks.ORANGE_STAINED_GLASS.defaultBlockState();
                case FLOOR -> Blocks.WHITE_STAINED_GLASS.defaultBlockState();
            };
            for (BlockPos pos : ring(plot, line.y())) {
                level.setBlock(pos, state, 2);
                placed++;
            }
        }
        return placed;
    }

    /** Rub them out. The ring is walkway, so anything on it is ours. */
    public static int hide(ServerLevel level, Layout.Plot plot, int upTo) {
        BlockState air = Blocks.AIR.defaultBlockState();
        int cleared = 0;
        int ceiling = Math.min(upTo, level.getMaxBuildHeight() - 1);
        for (int y = BASE; y <= ceiling; y++) {
            for (BlockPos pos : ring(plot, y)) {
                if (!level.getBlockState(pos).isAir()) {
                    level.setBlock(pos, air, 2);
                    cleared++;
                }
            }
        }
        return cleared;
    }

    public static int highest(List<Line> lines) {
        int max = BASE;
        for (Line l : lines) {
            max = Math.max(max, l.y());
        }
        return max;
    }

    /** The walkway ring one block outside the plot, at one height. */
    private static List<BlockPos> ring(Layout.Plot plot, int y) {
        List<BlockPos> out = new ArrayList<>();
        int x0 = plot.blockMinX() - 1;
        int x1 = plot.blockMaxX() + 1;
        int z0 = plot.blockMinZ() - 1;
        int z1 = plot.blockMaxZ() + 1;
        for (int x = x0; x <= x1; x++) {
            out.add(new BlockPos(x, y, z0));
            out.add(new BlockPos(x, y, z1));
        }
        for (int z = z0 + 1; z <= z1 - 1; z++) {
            out.add(new BlockPos(x0, y, z));
            out.add(new BlockPos(x1, y, z));
        }
        return out;
    }

    private static int intOf(JsonObject o, String key, int fallback) {
        try {
            return o.has(key) ? o.get(key).getAsInt() : fallback;
        } catch (RuntimeException e) {
            return fallback;
        }
    }

    private static List<Integer> intsOf(JsonObject o, String key) {
        List<Integer> out = new ArrayList<>();
        if (o.has(key) && o.get(key).isJsonArray()) {
            JsonArray a = o.getAsJsonArray(key);
            for (int i = 0; i < a.size(); i++) {
                try {
                    out.add(a.get(i).getAsInt());
                } catch (RuntimeException ignored) {
                    // A malformed entry is the file's problem, not a reason to draw
                    // nothing. The export will refuse it with a proper message.
                }
            }
        }
        return out;
    }
}
