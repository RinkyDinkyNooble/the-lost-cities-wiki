import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.rinkynooble.lostcitiesdevtool.validate.AssetValidator;
import com.rinkynooble.lostcitiesdevtool.validate.Finding;

import java.util.ArrayList;
import java.util.List;

/**
 * Every AssetValidator rule, in a plain JVM. Run it with check-validator.py.
 *
 * The validator is the one part of this mod that runs over files somebody else
 * wrote, and it imports nothing but Gson, so it needs no server, no Minecraft and
 * no world. That makes this the only check here that finishes in a fraction of a
 * second rather than in a minute and a half, which is worth keeping.
 *
 * Two halves. The rule cases say what the validator should report about an asset,
 * including the ones where it should report nothing, because a false alarm from a
 * checker costs more than a miss. The malformed cases say only that it must not
 * throw: it runs as a datapack load listener, and a value of the wrong JSON type is
 * what hand editing produces all day. Asking Gson for the wrong type throws, the
 * listener catches it, and the file comes back as "could not check" with every one
 * of its real faults unreported. The checker giving up on exactly the files most
 * likely to be broken is the failure this half exists to prevent.
 */
public class ValidatorProbe {

    record Case(String name, String kind, String json, String expect) {
    }

    /** expect "" means: this asset is fine, report nothing. */
    static final List<Case> CASES = List.of(

            // ------------------------------------------------------- buildings
            new Case("building with no filler", "buildings", """
                    {"parts": [{"part": "p"}]}""", "no 'filler'"),

            new Case("building with no parts", "buildings", """
                    {"filler": "#"}""", "no 'parts'"),

            new Case("building with empty parts", "buildings", """
                    {"filler": "#", "parts": []}""", "no 'parts'"),

            new Case("inpart never matches", "buildings", """
                    {"filler": "#", "parts": [{"part": "p", "inpart": "x"}]}""",
                    "never matches"),

            new Case("belowpart never matches", "buildings", """
                    {"filler": "#", "parts": [{"part": "p", "belowpart": "x"}]}""",
                    "never matches"),

            new Case("range with one number", "buildings", """
                    {"filler": "#", "parts": [{"part": "p", "range": "9"}]}""",
                    "range"),

            new Case("range with three numbers", "buildings", """
                    {"filler": "#", "minfloors": 0, "maxfloors": 2,
                     "parts": [{"part": "p", "range": "0,2,9"},
                               {"part": "q"}]}""",
                    "range"),

            new Case("plain building is fine", "buildings", """
                    {"filler": "#", "parts": [{"part": "p"}]}""", ""),

            new Case("bag of floors with a roof is fine", "buildings", """
                    {"filler": "#", "parts": [{"part": "a", "top": false},
                                              {"part": "b", "top": true}]}""", ""),

            // -------------------------------------------------------- palettes
            new Case("palette entry with no char", "palettes", """
                    {"palette": [{"block": "minecraft:stone"}]}""", "no 'char'"),

            new Case("block id with @meta", "palettes", """
                    {"palette": [{"char": "#", "block": "minecraft:stone@2"}]}""",
                    "not a block id"),

            new Case("block id with a capital", "palettes", """
                    {"palette": [{"char": "#", "block": "minecraft:Stone"}]}""",
                    "not a block id"),

            new Case("block state is fine", "palettes", """
                    {"palette": [{"char": "#",
                      "block": "minecraft:oak_stairs[facing=east,half=top]"}]}""", ""),

            new Case("loot with a slash", "palettes", """
                    {"palette": [{"char": "#", "block": "minecraft:chest",
                      "loot": "minecraft:chests/simple_dungeon"}]}""", "loot"),

            new Case("weighted list under 128", "palettes", """
                    {"palette": [{"char": "#", "blocks": [
                      {"random": 10, "block": "minecraft:stone"}]}]}""",
                    "must reach 128"),

            new Case("weighted list reaching 128 is fine", "palettes", """
                    {"palette": [{"char": "#", "blocks": [
                      {"random": 28, "block": "minecraft:stone"},
                      {"random": 100, "block": "minecraft:dirt"}]}]}""", ""),

            new Case("entry after 128 is unreachable", "palettes", """
                    {"palette": [{"char": "#", "blocks": [
                      {"random": 200, "block": "minecraft:stone"},
                      {"random": 10, "block": "minecraft:dirt"}]}]}""",
                    "unreachable"),

            // ----------------------------------------------------------- parts
            new Case("metadata instead of meta", "parts", """
                    {"xsize": 2, "zsize": 2, "metadata": {},
                     "slices": [["ab", "cd"], ["ab", "cd"]]}""", "'meta'"),

            new Case("row shorter than xsize", "parts", """
                    {"xsize": 4, "zsize": 2,
                     "slices": [["ab", "cd"], ["ab", "cd"]]}""", "expected 8"),

            new Case("square part is fine", "parts", """
                    {"xsize": 2, "zsize": 2,
                     "slices": [["ab", "cd"], ["ab", "cd"]]}""", ""),

            // ------------------------------------------------- inline palettes
            new Case("inline palette as a bare list", "parts", """
                    {"xsize": 2, "zsize": 2, "palette": [{"char": "#"}],
                     "slices": [["ab", "cd"], ["ab", "cd"]]}""", "takes an object"),

            new Case("inline palette as an object is fine", "parts", """
                    {"xsize": 2, "zsize": 2,
                     "palette": {"palette": [{"char": "#",
                                              "block": "minecraft:stone"}]},
                     "slices": [["ab", "cd"], ["ab", "cd"]]}""", ""),

            // ----------------------------------------------------- worldstyles
            new Case("monorail as a list", "worldstyles", """
                    {"parts": {"monorails": {"both": ["a"]}}}""",
                    "takes one part name"),

            new Case("monorail as a string is fine", "worldstyles", """
                    {"parts": {"monorails": {"both": "a"}}}""", ""),

            new Case("highway as a list is fine", "worldstyles", """
                    {"parts": {"highways": {"open": ["a", "b"]}}}""", ""),

            // Conditions. Nothing checked these until the audit found that
            // `Conditions.entriesOf` substitutes a default for an unreadable factor
            // and leans on a report that did not exist, so `/lcdev condition` printed
            // a share worked out from a number nobody wrote.
            new Case("condition with no values", "conditions", """
                    {}""", "needs a 'values' list"),
            new Case("condition values is not a list", "conditions", """
                    {"values": "nope"}""", "needs a 'values' list"),
            new Case("condition with empty values", "conditions", """
                    {"values": []}""", "chooses nothing"),
            new Case("condition entry is not an object", "conditions", """
                    {"values": ["nope"]}""", "not an object"),
            new Case("condition factor is not a number", "conditions", """
                    {"values": [{"factor": "high", "value": "x"}]}""",
                    "no readable 'factor'"),
            new Case("condition factor is missing", "conditions", """
                    {"values": [{"value": "x"}]}""", "no readable 'factor'"),
            new Case("condition value is missing", "conditions", """
                    {"values": [{"factor": 1}]}""", "no readable 'value'"),
            new Case("condition factor is negative", "conditions", """
                    {"values": [{"factor": -2, "value": "x"}]}""", "negative factor"),
            new Case("condition factors total zero", "conditions", """
                    {"values": [{"factor": 0, "value": "x"}]}""",
                    "no entry can be chosen"),
            new Case("condition entry has a key nothing reads", "conditions", """
                    {"values": [{"factor": 1, "value": "x", "inpartt": "y"}]}""",
                    "key nothing reads"),
            new Case("a good condition is silent", "conditions", """
                    {"values": [{"factor": 8, "value": "lostcities:chests/a",
                     "range": "4,100"}, {"factor": 20, "value": "b",
                     "inpart": "rail_dungeon1"}]}""", "")
    );

    /**
     * Assets that are wrong in a way the schema does not describe.
     *
     * The validator's whole contract is that it reports and steps aside: a
     * datapack load must never fail because of it. A value of the wrong JSON type
     * is exactly what a person editing by hand produces, so every one of these has
     * to come back with a finding or with silence, and never with a throw.
     */
    static final List<Case> MALFORMED = List.of(
            new Case("range is a number", "buildings", """
                    {"filler": "#", "parts": [{"part": "p", "range": 9}]}""", "?"),
            new Case("range is an object", "buildings", """
                    {"filler": "#", "parts": [{"part": "p", "range": {}}]}""", "?"),
            new Case("parts holds a string", "buildings", """
                    {"filler": "#", "parts": ["p"]}""", "?"),
            new Case("parts is an object", "buildings", """
                    {"filler": "#", "parts": {"part": "p"}}""", "?"),
            new Case("filler is a number", "buildings", """
                    {"filler": 5, "parts": [{"part": "p"}]}""", "?"),
            new Case("part ref is a number", "buildings", """
                    {"filler": "#", "parts": [{"part": 5}]}""", "?"),
            new Case("floor is a string", "buildings", """
                    {"filler": "#", "parts": [{"part": "p", "floor": "one"}]}""", "?"),
            new Case("top is a number", "buildings", """
                    {"filler": "#", "parts": [{"part": "p", "top": 1}]}""", "?"),

            new Case("palette is a string", "palettes", """
                    {"palette": "nope"}""", "?"),
            new Case("palette holds a string", "palettes", """
                    {"palette": ["nope"]}""", "?"),
            new Case("char is a number", "palettes", """
                    {"palette": [{"char": 5, "block": "minecraft:stone"}]}""", "?"),
            new Case("block is an object", "palettes", """
                    {"palette": [{"char": "#", "block": {}}]}""", "?"),
            new Case("blocks holds a string", "palettes", """
                    {"palette": [{"char": "#", "blocks": ["minecraft:stone"]}]}""", "?"),
            new Case("blocks is an object", "palettes", """
                    {"palette": [{"char": "#", "blocks": {}}]}""", "?"),
            new Case("random is a string", "palettes", """
                    {"palette": [{"char": "#", "blocks": [
                      {"random": "many", "block": "minecraft:stone"}]}]}""", "?"),
            new Case("loot is a number", "palettes", """
                    {"palette": [{"char": "#", "loot": 5}]}""", "?"),

            new Case("xsize is a string", "parts", """
                    {"xsize": "two", "zsize": 2,
                     "slices": [["ab", "cd"]]}""", "?"),
            new Case("slices is a string", "parts", """
                    {"xsize": 2, "zsize": 2, "slices": "abcd"}""", "?"),
            new Case("slices holds a string", "parts", """
                    {"xsize": 2, "zsize": 2, "slices": ["abcd"]}""", "?"),
            new Case("a layer holds a number", "parts", """
                    {"xsize": 2, "zsize": 2, "slices": [[12, 34]]}""", "?"),
            new Case("meta is a string", "parts", """
                    {"xsize": 2, "zsize": 2, "meta": "x",
                     "slices": [["ab", "cd"]]}""", "?"),

            new Case("worldstyle parts is a string", "worldstyles", """
                    {"parts": "nope"}""", "?"),
            new Case("monorails is a string", "worldstyles", """
                    {"parts": {"monorails": "nope"}}""", "?"),
            new Case("empty object of every kind", "buildings", """
                    {}""", "?")
    );

    /** Every kind, so a bare empty object cannot throw in any of them. */
    static final List<String> KINDS =
            List.of("buildings", "palettes", "parts", "worldstyles", "citystyles",
                    "conditions");

    public static void main(String[] args) {
        int failed = 0;
        for (Case c : CASES) {
            List<Finding> found;
            try {
                JsonObject json = JsonParser.parseString(c.json()).getAsJsonObject();
                found = AssetValidator.validate("probe.json", c.kind(), json,
                        c.json());
            } catch (RuntimeException e) {
                System.out.printf("  THREW  %-38s %s%n", c.name(), e);
                failed++;
                continue;
            }

            List<String> messages = new ArrayList<>();
            for (Finding f : found) {
                messages.add(f.severity() + " " + f.message());
            }
            boolean ok;
            if (c.expect().isEmpty()) {
                ok = found.isEmpty();
            } else {
                ok = messages.stream().anyMatch(m -> m.contains(c.expect()));
            }
            if (ok) {
                System.out.printf("  ok     %-38s %s%n", c.name(),
                        found.isEmpty() ? "(silent)" : messages.get(0));
            } else {
                failed++;
                System.out.printf("  FAIL   %-38s expected %s%n", c.name(),
                        c.expect().isEmpty() ? "silence" : "'" + c.expect() + "'");
                for (String m : messages) {
                    System.out.println("           got " + m);
                }
                if (messages.isEmpty()) {
                    System.out.println("           got nothing");
                }
            }
        }
        System.out.println();
        System.out.println("malformed input: a finding or silence, never a throw");
        int threw = 0;
        for (Case c : MALFORMED) {
            try {
                JsonObject json = JsonParser.parseString(c.json()).getAsJsonObject();
                List<Finding> found = AssetValidator.validate("probe.json", c.kind(),
                        json, c.json());
                System.out.printf("  ok     %-38s %s%n", c.name(),
                        found.isEmpty() ? "(silent)"
                                : found.get(0).severity() + " " + found.get(0).message());
            } catch (RuntimeException e) {
                threw++;
                System.out.printf("  THREW  %-38s %s%n", c.name(), e);
            }
        }
        for (String kind : KINDS) {
            try {
                AssetValidator.validate("probe.json", kind,
                        JsonParser.parseString("{}").getAsJsonObject(), "{}");
            } catch (RuntimeException e) {
                threw++;
                System.out.printf("  THREW  empty %-32s %s%n", kind, e);
            }
        }

        failed += firstErrorCases();

        System.out.printf("%n%d rule cases, %d failed. %d malformed cases, %d threw%n",
                CASES.size(), failed, MALFORMED.size() + KINDS.size(), threw);
        System.exit(failed == 0 && threw == 0 ? 0 : 1);
    }

    /**
     * Which finding is quoted as the reason a list of findings is a failure.
     *
     * <p>The wipe backup used to quote the first entry, and a list carries warnings
     * and errors in the order they were discovered. So a pack that warned before it
     * errored had the warning named as the reason its backup failed, in the message
     * read immediately before a wipe.
     *
     * <p>The first case below is the one that was wrong. The others are the cases
     * that were always right and have to stay so.
     */
    static int firstErrorCases() {
        System.out.println();
        int bad = 0;
        Finding warn = Finding.warn("a.json", 1, "a warning", "");
        Finding err = Finding.error("b.json", 2, "the real error", "");
        Finding err2 = Finding.error("c.json", 3, "a later error", "");

        bad += expect("warning before the error", "the real error",
                Finding.firstError(List.of(warn, err), "none"));
        bad += expect("error alone", "the real error",
                Finding.firstError(List.of(err), "none"));
        bad += expect("error before a second error", "the real error",
                Finding.firstError(List.of(err, err2), "none"));
        bad += expect("warnings only", "none",
                Finding.firstError(List.of(warn), "none"));
        bad += expect("empty list", "none",
                Finding.firstError(List.of(), "none"));
        bad += expect("null list", "none", Finding.firstError(null, "none"));
        return bad;
    }

    private static int expect(String name, String want, String got) {
        if (want.equals(got)) {
            System.out.printf("  ok     firstError %-27s %s%n", name, got);
            return 0;
        }
        System.out.printf("  FAIL   firstError %-27s wanted '%s', got '%s'%n",
                name, want, got);
        return 1;
    }
}
