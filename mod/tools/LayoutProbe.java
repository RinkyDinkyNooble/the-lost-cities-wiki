import com.rinkynooble.lostcitiesdevtool.workshop.Catalogue;
import com.rinkynooble.lostcitiesdevtool.workshop.Layout;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Where the plots are, in a plain JVM. Run it with check-layout.py.
 *
 * The layout is arithmetic over the catalogue: which row sits at which chunk, how
 * wide each plot is, and which floor colour each takes so that no two you can see
 * together look alike. None of that needs a world, and since the colours moved to
 * Workshop none of it needs Minecraft either, so this finishes in about a second
 * instead of the ninety a server check costs.
 *
 * The property under test is **stability**. A plot's position is written into the
 * world the moment something is pasted onto it, and it is never written down again.
 * So if growing one row moves another row's plots, everything already built on them
 * is stranded: the blocks stay at the old coordinates while the plot that owns those
 * coordinates becomes a different plot. That is what a workshop full of buildings
 * standing beside their own floors looks like.
 *
 * Growing a row is not rare. An import grows every row the pack it read needs, and
 * a pack with fifteen multi-building footprints grows fifteen rows that were empty a
 * moment ago.
 */
public class LayoutProbe {

    static int failures;

    record Where(int cx, int cz, int width, int height, int colour) {
    }

    static Map<String, Where> snapshot() {
        Map<String, Where> out = new LinkedHashMap<>();
        for (Layout.Plot p : Layout.plots()) {
            out.put(p.id(), new Where(p.cx(), p.cz(), p.width(), p.height(),
                    p.floorColour()));
        }
        return out;
    }

    static void fail(String message) {
        failures++;
        System.out.println("  FAIL " + message);
    }

    /** Every plot that existed before must be exactly where it was. */
    static void mustNotMove(String what, Map<String, Where> before,
                            Map<String, Where> after) {
        List<String> moved = new ArrayList<>();
        List<String> recoloured = new ArrayList<>();
        for (Map.Entry<String, Where> e : before.entrySet()) {
            Where now = after.get(e.getKey());
            if (now == null) {
                moved.add(e.getKey() + " vanished");
                continue;
            }
            Where was = e.getValue();
            if (was.cx() != now.cx() || was.cz() != now.cz()) {
                moved.add(String.format("%s %d,%d -> %d,%d", e.getKey(),
                        was.cx(), was.cz(), now.cx(), now.cz()));
            } else if (was.colour() != now.colour()) {
                recoloured.add(e.getKey());
            }
        }
        System.out.printf("  %-46s moved %d, recoloured %d%n", what, moved.size(),
                recoloured.size());
        for (int i = 0; i < Math.min(4, moved.size()); i++) {
            System.out.println("      " + moved.get(i));
        }
        if (!moved.isEmpty()) {
            fail(what + ": " + moved.size() + " plots that already existed moved, so "
                    + "anything built on them is now standing on a different plot");
        }
        if (!recoloured.isEmpty()) {
            fail(what + ": " + recoloured.size() + " plots kept their position and "
                    + "changed colour, so the floor under a build is repainted");
        }
    }

    public static void main(String[] args) {
        System.out.println("catalogue rows: " + Catalogue.rows().size());

        Layout.setGrown(Map.of());
        Map<String, Where> fresh = snapshot();
        System.out.println("plots in a fresh catalogue: " + fresh.size());

        // A row nothing has grown yet. Every multi-building footprint is declared
        // and almost none are laid out, which is exactly the state an import walks
        // into.
        long emptyRows = Catalogue.rows().stream()
                .filter(r -> Layout.plotsIn(r) == 0).count();
        System.out.println("rows the fresh catalogue lays out no plots for: "
                + emptyRows);
        System.out.println();

        System.out.println("growing one empty row, the way an import does");
        Layout.setGrown(Map.of());
        Map<String, Where> before = snapshot();
        Layout.grow("multibuilding/3x3", 2);
        mustNotMove("after multibuilding/3x3 grew to 2", before, snapshot());

        System.out.println();
        System.out.println("growing a row that already had plots");
        Layout.setGrown(Map.of());
        Map<String, Where> beforeWide = snapshot();
        Layout.grow("building/1x1", 40);
        mustNotMove("after building/1x1 grew to 40", beforeWide, snapshot());

        System.out.println();
        System.out.println("the footprints DeceasedCraft actually ships");
        Layout.setGrown(Map.of());
        Map<String, Where> beforeDc = snapshot();
        for (String id : List.of("multibuilding/1x2", "multibuilding/1x4",
                "multibuilding/2x1", "multibuilding/2x2", "multibuilding/2x3",
                "multibuilding/3x1", "multibuilding/3x2", "multibuilding/3x3",
                "multibuilding/4x1", "multibuilding/4x2", "multibuilding/4x4",
                "multibuilding/5x5", "multibuilding/5x7", "multibuilding/6x2",
                "multibuilding/6x4")) {
            Layout.grow(id, 3);
        }
        mustNotMove("after 15 footprints grew", beforeDc, snapshot());

        System.out.println();
        System.out.println("no two plots may overlap, grown or not");
        List<Layout.Plot> all = Layout.plots();
        int overlaps = 0;
        for (int i = 0; i < all.size(); i++) {
            for (int j = i + 1; j < all.size(); j++) {
                Layout.Plot a = all.get(i);
                Layout.Plot b = all.get(j);
                boolean x = a.blockMinX() <= b.blockMaxX()
                        && b.blockMinX() <= a.blockMaxX();
                boolean z = a.blockMinZ() <= b.blockMaxZ()
                        && b.blockMinZ() <= a.blockMaxZ();
                if (x && z) {
                    if (overlaps < 3) {
                        System.out.println("      " + a.id() + " overlaps " + b.id());
                    }
                    overlaps++;
                }
            }
        }
        System.out.println("  overlapping pairs: " + overlaps);
        if (overlaps > 0) {
            fail(overlaps + " pairs of plots occupy the same blocks");
        }

        // Reserving a band for every row costs coordinates, so say how many.
        // Nothing is painted for a row with no plots, so this is address space
        // rather than world.
        int minZ = Integer.MAX_VALUE;
        int maxZ = Integer.MIN_VALUE;
        int minX = Integer.MAX_VALUE;
        int maxX = Integer.MIN_VALUE;
        for (Layout.Plot p : all) {
            minZ = Math.min(minZ, p.blockMinZ());
            maxZ = Math.max(maxZ, p.blockMaxZ());
            minX = Math.min(minX, p.blockMinX());
            maxX = Math.max(maxX, p.blockMaxX());
        }
        System.out.println();
        System.out.printf("extent with every band reserved: x %d..%d, z %d..%d%n",
                minX, maxX, minZ, maxZ);
        System.out.printf("  %d by %d blocks, %d plots painted%n",
                maxX - minX + 1, maxZ - minZ + 1, all.size());

        cost();

        System.out.println();
        if (failures > 0) {
            System.out.println("FAILED (" + failures + ")");
            System.exit(1);
        }
        System.out.println("layout is stable: growing a row moves nothing that "
                + "already existed");
    }

    /**
     * What one call to Layout.plots() costs, and how it grows.
     *
     * Every plot suggestion calls it. `/lcdev plot set <tab>` reads the plot under
     * the caller to know which keys that row class offers, and a client asks for
     * suggestions on every keystroke, so this runs tens of times while somebody
     * types one argument.
     *
     * The colouring is greedy over real adjacency, which is quadratic: each plot is
     * compared against every plot already placed. That is the right algorithm, since
     * a formula on row and column indices collides once two rows have different plot
     * widths. It does mean the cost is n squared, and the numbers below are here so
     * that stops being a surprise.
     *
     * Measured rather than assumed, and printed whether or not it passes. The
     * default catalogue is well inside anything a person notices; the grown cases
     * say where the ceiling is.
     */
    static void cost() {
        System.out.println();
        System.out.println("what one Layout.plots() costs, called per keystroke");
        Layout.setGrown(Map.of());
        long base = time("default catalogue");

        Map<String, Integer> grown = new LinkedHashMap<>();
        for (Catalogue.Row r : Catalogue.rows()) {
            grown.put(r.id(), 20);
        }
        Layout.setGrown(grown);
        time("every row grown to 20");

        for (Catalogue.Row r : Catalogue.rows()) {
            grown.put(r.id(), 60);
        }
        Layout.setGrown(grown);
        long big = time("every row grown to 60");
        Layout.setGrown(Map.of());

        // The budget check-suggest-speed holds the server-side paths to. The
        // default catalogue is the one a person actually types against, so that is
        // what is asserted; the grown figure is printed to show the shape.
        if (base > 20_000_000L) {
            failures++;
            System.out.println("  FAIL the default catalogue costs " + base / 1_000_000
                    + " ms a keystroke, and 50 is what a person starts to feel");
        }
        System.out.println("  the cost is quadratic in plots, so the grown figure "
                + "above is the shape, not the norm");
        if (big > 200_000_000L) {
            failures++;
            System.out.println("  FAIL even a heavily grown catalogue should not "
                    + "cost " + big / 1_000_000 + " ms a keystroke");
        }
    }

    /** The best of twenty runs, which is the one least polluted by the JIT. */
    static long time(String what) {
        Layout.plots();
        long best = Long.MAX_VALUE;
        int plots = 0;
        for (int i = 0; i < 20; i++) {
            long started = System.nanoTime();
            plots = Layout.plots().size();
            best = Math.min(best, System.nanoTime() - started);
        }
        System.out.printf("  %-30s %6d plots  %7.2f ms%n", what, plots, best / 1e6);
        return best;
    }
}
