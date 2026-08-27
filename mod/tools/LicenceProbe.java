import com.rinkynooble.lostcitiesdevtool.workshop.Licence;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Shaping a licence for a chat line, and folding several into one notice, in a plain
 * JVM. Run it with check-licence-text.py.
 *
 * Licence holds no Minecraft type, so this needs no server and finishes in about a
 * second. Three things here would be silent if they broke:
 *
 *   * Apache and the GPL open with blank lines and a centred title. A summary that
 *     took the first three lines as written would show two empty ones and a run of
 *     spaces, and the reader would learn nothing about what they had just imported.
 *
 *   * A licence written as one very long line defeats a line count on its own: it
 *     wraps into three in chat and the cap does nothing.
 *
 *   * Carrying a notice has to be idempotent. A pack compiled out of an imported
 *     pack that was itself compiled from an import would otherwise nest one heading
 *     inside another, and label the first author's terms with the second author's
 *     namespace. That is a false statement about somebody's work rather than an
 *     untidy file, and it accumulates every round trip.
 */
public class LicenceProbe {

    static int failures;

    static void check(String name, Object got, Object want) {
        boolean ok = String.valueOf(got).equals(String.valueOf(want));
        System.out.printf("  %-4s %-44s %s%n", ok ? "ok" : "FAIL", name, got);
        if (!ok) {
            failures++;
            System.out.println("       expected " + want);
        }
    }

    static final String MIT = "MIT License\n\n"
            + "Copyright (c) 2024 Someone\n\n"
            + "Permission is hereby granted, free of charge, to any person "
            + "obtaining a copy\n"
            + "of this software and associated documentation files.\n";

    // What Apache actually ships: blank lines, then a centred title.
    static final String APACHE = "\n\n"
            + "                                 Apache License\n"
            + "                           Version 2.0, January 2004\n"
            + "                        http://www.apache.org/licenses/\n"
            + "\n"
            + "   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION\n";

    static void summaries() {
        System.out.println("summarising");

        Licence.Summary mit = Licence.summarise(MIT, false);
        check("MIT names itself first", mit.shown().get(0), "MIT License");
        check("blank line between is skipped", mit.shown().get(1),
                "Copyright (c) 2024 Someone");
        check("three lines, no more", mit.shown().size(), 3);
        check("the rest is counted", mit.more(), 1);

        Licence.Summary apache = Licence.summarise(APACHE, false);
        check("leading blanks are skipped", apache.shown().get(0), "Apache License");
        check("centring whitespace is stripped", apache.shown().get(1),
                "Version 2.0, January 2004");
        check("apache remainder", apache.more(), 1);

        // A licence as one paragraph. The line count is satisfied and the width cap
        // is the only thing standing between the reader and a wall of text.
        String wall = "a".repeat(400);
        Licence.Summary one = Licence.summarise(wall, false);
        check("one long line is one line", one.shown().size(), 1);
        check("and is cut to the chat width", one.shown().get(0).length(),
                Licence.MAX_LINE);
        check("cut lines say so", one.shown().get(0).endsWith("..."), true);
        check("nothing left to count", one.more(), 0);

        check("an empty file shows nothing",
                Licence.summarise("", false).shown().size(), 0);
        check("whitespace only shows nothing",
                Licence.summarise("   \n\n  \n", false).shown().size(), 0);
        check("a short file has no remainder",
                Licence.summarise("Public domain.\n", false).more(), 0);
        check("truncation is carried through",
                Licence.summarise(MIT, true).truncated(), true);
    }

    static void notices() {
        System.out.println("\nnotices");

        check("nothing to carry writes nothing",
                Licence.notice(new LinkedHashMap<>()), null);

        Map<String, String> one = new LinkedHashMap<>();
        one.put("deceasedcraft", MIT);
        String notice = Licence.notice(one);
        check("a notice identifies itself", notice.startsWith(Licence.MARKER), true);
        check("and names where the terms came from",
                notice.contains("===== deceasedcraft ====="), true);
        check("reproducing them unchanged",
                notice.contains("Copyright (c) 2024 Someone"), true);

        Map<String, String> two = new LinkedHashMap<>();
        two.put("zeta", "Zeta terms.\n");
        two.put("alpha", "Alpha terms.\n");
        String both = Licence.notice(two);
        check("two namespaces, both carried", Licence.blocksOf(both).size(), 2);
        check("in a fixed order whatever order they arrived in",
                Licence.blocksOf(both).keySet().toString(), "[alpha, zeta]");

        check("an ordinary licence is not a notice", Licence.blocksOf(MIT), null);
        check("a notice reads back the terms it carried",
                Licence.blocksOf(notice).get("deceasedcraft").contains("MIT License"),
                true);

        // The one that matters. Import a pack that carries a notice, compile it
        // again, and the statements have to pass through under the namespaces they
        // belong to rather than under the namespace of the pack that carried them.
        Map<String, String> again = new LinkedHashMap<>();
        again.put("mypack", both);
        String second = Licence.notice(again);
        check("carrying a notice does not wrap it",
                second.contains("===== mypack ====="), false);
        check("the original namespaces survive",
                Licence.blocksOf(second).keySet().toString(), "[alpha, zeta]");
        check("and a third round changes nothing",
                Licence.notice(Map.of("other", second)), second);

        // A pack of its own alongside one it carried.
        Map<String, String> mixed = new LinkedHashMap<>();
        mixed.put("mypack", both);
        mixed.put("plain", "Plain terms.\n");
        check("a carried notice merges with a plain one",
                Licence.blocksOf(Licence.notice(mixed)).keySet().toString(),
                "[alpha, plain, zeta]");
    }

    /**
     * blocksOf, on text this mod did not write.
     *
     * Every other case here feeds it a notice built by notice(), which is the half
     * that cannot be malformed. The half that can is a license.txt out of somebody
     * else's pack, and both of the faults below were reachable from one and from
     * nothing else: a crash that ended the export in a stack trace, and a silent
     * drop of the statement the whole feature exists to carry.
     */
    static void hostile() {
        System.out.println("\ntext this mod did not write");

        // The two rules overlap, so the name would run from index 6 to index 5.
        String overlapping = Licence.MARKER + "\n===== =====\n";
        try {
            check("an overlapping rule line is not a heading",
                    Licence.blocksOf(overlapping).isEmpty(), true);
        } catch (RuntimeException e) {
            failures++;
            System.out.println("  FAIL blocksOf threw on an overlapping rule: " + e);
        }

        // Marker line, no heading. Parsing to nothing must not read as a notice
        // carrying nothing, or the terms are dropped rather than carried.
        Map<String, String> headless = new LinkedHashMap<>();
        headless.put("victim", Licence.MARKER + "\nReserved, Someone 2024.\n");
        check("a marker with no heading is carried whole",
                Licence.carriedFrom(headless).keySet().toString(), "[victim]");
        String notice = Licence.notice(headless);
        check("and reaches the pack rather than vanishing",
                notice != null && notice.contains("Reserved, Someone 2024."), true);

        // Shapes that are near misses rather than headings.
        for (String line : new String[]{"=====", "======", "===== ", " =====",
                                        "===== two words =====", "=====  ====="}) {
            try {
                Licence.blocksOf(Licence.MARKER + "\n" + line + "\n");
            } catch (RuntimeException e) {
                failures++;
                System.out.println("  FAIL blocksOf threw on " + line + ": " + e);
            }
        }
        System.out.println("  ok   near-miss rule lines parse without throwing");

        check("a truncated notice still reads", Licence.blocksOf(
                Licence.MARKER + "\n===== alpha =====\nAlpha te")
                .get("alpha"), "Alpha te");
    }

    public static void main(String[] args) {
        summaries();
        notices();
        hostile();
        System.out.println();
        if (failures > 0) {
            System.out.println(failures + " failed");
            System.exit(1);
        }
    }
}
