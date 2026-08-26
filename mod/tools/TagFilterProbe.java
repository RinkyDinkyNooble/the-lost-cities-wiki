import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.rinkynooble.lostcitiesdevtool.workshop.TagFilter;

import java.util.List;

/**
 * Which parts of a block's NBT survive, in a plain JVM. Run it with check-tags.py.
 *
 * TagFilter decides what an export keeps out of the NBT a block is carrying. That is
 * string and tree work with no Minecraft in it, so it needs no server and finishes
 * in about a second.
 *
 * The cases below are the ones that decide whether the rules mean what the settings
 * file says they mean. Two matter more than the rest:
 *
 *   * a keep-list must drop everything it does not name, because the whole point of
 *     naming Command is to leave a chest's inventory behind
 *   * a drop-list must keep everything it does not name, because the whole point of
 *     naming LootTableSeed is to lose only that
 *
 * Getting those two the wrong way round would be silent: the pack still loads, and
 * the difference only shows up as a building that generates wrong.
 */
public class TagFilterProbe {

    static int failures;

    record Case(String name, String rules, String tag, String expect) {
    }

    static JsonArray rules(String csv) {
        JsonArray out = new JsonArray();
        if (!csv.isEmpty()) {
            for (String s : csv.split(",", -1)) {
                out.add(s);
            }
        }
        return out;
    }

    static void run(Case c) {
        JsonObject tag = JsonParser.parseString(c.tag()).getAsJsonObject();
        JsonObject got = TagFilter.of(rules(c.rules())).apply(tag);
        String actual = got == null ? "null" : got.toString();
        String want = "null".equals(c.expect()) ? "null"
                : JsonParser.parseString(c.expect()).getAsJsonObject().toString();
        boolean ok = actual.equals(want);
        System.out.printf("  %-4s %-34s %s%n", ok ? "ok" : "FAIL", c.name(), actual);
        if (!ok) {
            failures++;
            System.out.println("       expected " + want);
        }
    }

    public static void main(String[] args) {
        String chest = "{\"Items\":[{\"id\":\"minecraft:stone\"}],"
                + "\"LootTable\":\"minecraft:chests/simple_dungeon\","
                + "\"LootTableSeed\":42,\"CustomName\":\"crate\"}";
        String command = "{\"Command\":\"/say hi\",\"auto\":1,\"powered\":0,"
                + "\"TrackOutput\":1,\"LastOutput\":\"noise\"}";
        String nested = "{\"Base\":{\"Color\":4,\"Extra\":9},\"Other\":1}";

        System.out.println("no rules at all");
        run(new Case("empty list keeps everything", "", command, command));

        System.out.println();
        System.out.println("a keep-list drops what it does not name");
        run(new Case("only Command", "Command", command,
                "{\"Command\":\"/say hi\"}"));
        run(new Case("Command and auto", "Command,auto", command,
                "{\"Command\":\"/say hi\",\"auto\":1}"));
        run(new Case("naming nothing that is there", "Nope", command, "null"));

        System.out.println();
        System.out.println("a drop-list keeps what it does not name");
        run(new Case("drop the inventory", "!Items", chest,
                "{\"LootTable\":\"minecraft:chests/simple_dungeon\","
                        + "\"LootTableSeed\":42,\"CustomName\":\"crate\"}"));
        run(new Case("drop the seed and the inventory", "!Items,!LootTableSeed",
                chest, "{\"LootTable\":\"minecraft:chests/simple_dungeon\","
                        + "\"CustomName\":\"crate\"}"));
        run(new Case("dropping everything there is",
                "!Items,!LootTable,!LootTableSeed,!CustomName", chest, "null"));

        System.out.println();
        System.out.println("nesting, dot separated");
        run(new Case("keep one nested key", "Base.Color", nested,
                "{\"Base\":{\"Color\":4}}"));
        run(new Case("drop one nested key", "!Base.Extra", nested,
                "{\"Base\":{\"Color\":4},\"Other\":1}"));
        run(new Case("keep a whole subtree", "Base", nested,
                "{\"Base\":{\"Color\":4,\"Extra\":9}}"));
        run(new Case("keep a subtree minus one of it", "Base,!Base.Extra", nested,
                "{\"Base\":{\"Color\":4}}"));

        System.out.println();
        System.out.println("the last mention of a path decides");
        run(new Case("dropped then kept", "!Command,Command", command,
                "{\"Command\":\"/say hi\"}"));
        run(new Case("kept then dropped", "Command,!Command", command, "null"));

        System.out.println();
        System.out.println("rubbish in the list is ignored, not fatal");
        run(new Case("empty entries", ",Command,", command,
                "{\"Command\":\"/say hi\"}"));
        run(new Case("a bare bang", "!", command, command));

        System.out.println();
        if (failures > 0) {
            System.out.println("FAILED (" + failures + ")");
            System.exit(1);
        }
        System.out.println("tag filtering keeps and drops exactly what it is told to");
    }
}
