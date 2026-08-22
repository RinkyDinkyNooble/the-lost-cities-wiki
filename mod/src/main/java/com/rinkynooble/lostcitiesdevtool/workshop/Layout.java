package com.rinkynooble.lostcitiesdevtool.workshop;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Where every plot sits, and what colour its floor is.
 *
 * <p>Pure arithmetic over the {@link Catalogue}. Nothing here touches a world, which
 * is what lets the layout be checked without booting anything.
 *
 * <p><b>Everything is chunk aligned.</b> A part is a chunk footprint, so a plot that
 * did not sit on a chunk boundary would make the export read across four chunks to
 * fill one part, and would make force loading a plot mean force loading nine.
 *
 * <p><b>The origin is the front desk.</b> Chunk 0,0 holds the pack's own settings:
 * namespace, profile, world style, output format. Buildings grow east from chunk 2,
 * infrastructure grows west from chunk -2, and both stack their rows northward. The
 * chunks at x -1, 0 and 1 stay clear so the two areas never meet.
 */
public final class Layout {

    /** The floor. The lowest block there is, so "do not build below the plot" is true. */
    public static final int FLOOR_Y = -64;

    /** One chunk of walkway between plots and between rows. */
    private static final int GAP = 1;

    /** The first chunk a row's plots may use, measured out from the origin. */
    private static final int FIRST = 2;

    /** The pack's own settings, at the origin. */
    public static final String CORE_ID = "core";

    /**
     * Floor colours. Sixteen, so a catalogue this size never has to repeat one near
     * itself. They carry no meaning: the only rule is that no two plots you can see
     * at once look alike.
     */
    private static final Block[] COLOURS = {
            Blocks.WHITE_GLAZED_TERRACOTTA, Blocks.ORANGE_GLAZED_TERRACOTTA,
            Blocks.MAGENTA_GLAZED_TERRACOTTA, Blocks.LIGHT_BLUE_GLAZED_TERRACOTTA,
            Blocks.YELLOW_GLAZED_TERRACOTTA, Blocks.LIME_GLAZED_TERRACOTTA,
            Blocks.PINK_GLAZED_TERRACOTTA, Blocks.GRAY_GLAZED_TERRACOTTA,
            Blocks.LIGHT_GRAY_GLAZED_TERRACOTTA, Blocks.CYAN_GLAZED_TERRACOTTA,
            Blocks.PURPLE_GLAZED_TERRACOTTA, Blocks.BLUE_GLAZED_TERRACOTTA,
            Blocks.BROWN_GLAZED_TERRACOTTA, Blocks.GREEN_GLAZED_TERRACOTTA,
            Blocks.RED_GLAZED_TERRACOTTA, Blocks.BLACK_GLAZED_TERRACOTTA,
    };

    /**
     * One plot.
     *
     * @param cx    minimum chunk X, inclusive
     * @param cz    minimum chunk Z, inclusive
     * @param row   the catalogue row, or null for the core settings plot
     * @param index which variation this is within its row
     */
    public record Plot(String id, int cx, int cz, int width, int height,
                       @Nullable Catalogue.Row row, int index, int colour) {

        public int blockMinX() {
            return cx * 16;
        }

        public int blockMinZ() {
            return cz * 16;
        }

        public int blockMaxX() {
            return cx * 16 + width * 16 - 1;
        }

        public int blockMaxZ() {
            return cz * 16 + height * 16 - 1;
        }

        public Block floor() {
            // The front desk is not one of the shapes, so it takes no colour from
            // the pool. Stone bricks read as "not a plot" at a glance.
            return CORE_ID.equals(id)
                    ? Blocks.CHISELED_STONE_BRICKS
                    : COLOURS[Math.floorMod(colour, COLOURS.length)];
        }

        public boolean contains(int blockX, int blockZ) {
            return blockX >= blockMinX() && blockX <= blockMaxX()
                    && blockZ >= blockMinZ() && blockZ <= blockMaxZ();
        }

        /** The walkway corner a plot's chest and marker belong at: south, then west. */
        public int chestX() {
            return blockMinX();
        }

        public int chestZ() {
            return blockMaxZ() + 1;
        }
    }

    /**
     * Rows grown past their catalogue default, by row id.
     *
     * <p>An import brings whatever a pack holds, which is rarely the three plots a
     * row starts with. The catalogue's number is a starting size, not a limit.
     *
     * <p>Held statically and written to the world by {@link Workshop}, because the
     * layout has to come out the same on the next boot: shrinking a row back would
     * orphan everything an import pasted into it.
     */
    private static final Map<String, Integer> GROWN = new HashMap<>();

    private Layout() {
    }

    /** How many plots a row holds, which is its default unless it has been grown. */
    public static int plotsIn(Catalogue.Row row) {
        // A row the codec allows only one of stays at one however much a pack holds.
        // A list where the mod takes a string is a load error, not a bigger row.
        if (row.kind() == Catalogue.Kind.SINGLE) {
            return 1;
        }
        return Math.max(row.plots(), GROWN.getOrDefault(row.id(), 0));
    }

    public static void grow(String rowId, int plots) {
        GROWN.merge(rowId, plots, Math::max);
    }

    public static Map<String, Integer> grown() {
        return Map.copyOf(GROWN);
    }

    public static void setGrown(Map<String, Integer> sizes) {
        GROWN.clear();
        GROWN.putAll(sizes);
    }

    /**
     * Every plot, in a fixed order.
     *
     * <p>The order is what makes the colouring deterministic, so the same catalogue
     * always produces the same world and two people comparing screenshots are
     * looking at the same thing.
     */
    public static List<Plot> plots() {
        List<Plot> out = new ArrayList<>();
        out.add(new Plot(CORE_ID, 0, 0, 1, 1, null, 0, 0));

        for (Catalogue.Area area : Catalogue.Area.values()) {
            // Rows stack northward. `southEdge` is the chunk Z of the row's south
            // side; the row occupies height chunks north of it.
            int southEdge = 0;
            for (Catalogue.Row row : Catalogue.rows()) {
                if (row.area() != area) {
                    continue;
                }
                int cz = southEdge - row.height() + 1;
                for (int i = 0; i < plotsIn(row); i++) {
                    int cx = area == Catalogue.Area.EAST
                            ? FIRST + i * (row.width() + GAP)
                            // Growing west, the plot's minimum corner is its far side.
                            : -FIRST - i * (row.width() + GAP) - (row.width() - 1);
                    out.add(new Plot(row.id() + "/" + i, cx, cz,
                            row.width(), row.height(), row, i, 0));
                }
                southEdge = cz - 1 - GAP;
            }
        }
        return colour(out);
    }

    /**
     * Assign floor colours so no two plots you can see together look alike.
     *
     * <p>Greedy over real adjacency rather than a formula on row and column indices.
     * A formula looks fine until two rows have different plot widths, at which point
     * a plot in one row can sit beside a plot several columns along in the next, and
     * any fixed stride eventually collides. Greedy cannot: it looks at what is
     * actually next to the plot.
     *
     * <p>Deterministic, because the plot order is.
     */
    private static List<Plot> colour(List<Plot> plots) {
        List<Plot> out = new ArrayList<>(plots.size());
        for (Plot plot : plots) {
            boolean[] taken = new boolean[COLOURS.length];
            for (Plot done : out) {
                if (touches(plot, done)) {
                    taken[Math.floorMod(done.colour(), COLOURS.length)] = true;
                }
            }
            int pick = 0;
            while (pick < COLOURS.length && taken[pick]) {
                pick++;
            }
            out.add(new Plot(plot.id(), plot.cx(), plot.cz(), plot.width(),
                    plot.height(), plot.row(), plot.index(),
                    pick == COLOURS.length ? 0 : pick));
        }
        return out;
    }

    /**
     * Do these two plots share a view?
     *
     * <p>**Both** rectangles grow by the walkway before the overlap test, not one.
     * Growing one leaves plots separated by exactly the walkway looking unrelated,
     * which is the commonest arrangement there is: every plot in a row is exactly
     * that far from the next. Getting this wrong makes the colouring believe nothing
     * has a neighbour, and every plot then takes the first colour.
     */
    private static boolean touches(Plot a, Plot b) {
        return a.cx() - GAP <= b.cx() + b.width() - 1 + GAP
                && b.cx() - GAP <= a.cx() + a.width() - 1 + GAP
                && a.cz() - GAP <= b.cz() + b.height() - 1 + GAP
                && b.cz() - GAP <= a.cz() + a.height() - 1 + GAP;
    }

    /** The plot covering this block position, or null for walkway. */
    @Nullable
    public static Plot at(List<Plot> plots, int blockX, int blockZ) {
        for (Plot p : plots) {
            if (p.contains(blockX, blockZ)) {
                return p;
            }
        }
        return null;
    }
}
