package com.rinkynooble.lostcitiesdevtool.platform;

import net.minecraftforge.common.ForgeConfigSpec;
import org.apache.commons.lang3.tuple.Pair;

/**
 * One toggle per feature, in two groups.
 *
 * <p>{@code diagnostics} only changes what is reported, so every toggle in it
 * defaults to on. {@code repairs} changes what generates, so every toggle in it
 * defaults to off and has to be chosen deliberately.
 *
 * <p>Read through the static getters only. The fields are Forge's config type, so
 * keeping them private keeps that type in {@code platform/}: a port to another
 * loader rewrites this class and leaves every caller alone.
 */
public class Config {

    public static final ForgeConfigSpec SPEC;
    private static final Config INSTANCE;

    // -- diagnostics, on by default -------------------------------------------

    /** Feature 1.1. Wraps the sphere feature in the catch the terrain feature has. */
    private final ForgeConfigSpec.BooleanValue catchSphereFeatureErrors;

    /** Features 1.2 and 1.3. A fuller report beside each caught generation fault. */
    private final ForgeConfigSpec.BooleanValue detailedFaultReports;

    /** Feature 1.4. Check every asset file when datapacks load. */
    private final ForgeConfigSpec.BooleanValue validateOnLoad;

    /** Feature 2.1. Comments and trailing commas in Lost Cities asset files. */
    private final ForgeConfigSpec.BooleanValue acceptCommentsAndTrailingCommas;

    /** Feature 2.2. A Lost Cities asset or profile may be named .json5. */
    private final ForgeConfigSpec.BooleanValue acceptJson5Extension;

    /** Feature 2.2. Report a .json that a .json5 of the same name is shadowing. */
    private final ForgeConfigSpec.BooleanValue warnOnJson5Override;

    // -- repairs, off by default ----------------------------------------------

    /** Repair 3.1. Makes belowpart test the part below rather than the current one. */
    private final ForgeConfigSpec.BooleanValue fixBelowPart;

    /** Repair 3.2. Makes the 'full' street shape reachable. */
    private final ForgeConfigSpec.BooleanValue fixFullStreetShape;

    /** Repair 4.1. Keeps the Cities button anchored after a resize. Client only. */
    private final ForgeConfigSpec.BooleanValue anchorCitiesButton;

    /** Repair 4.4. Stops the Customize button crashing after leaving a world. */
    private final ForgeConfigSpec.BooleanValue fixCustomizeCrash;

    /** Feature 4.2. Right-click the profile button to cycle backwards. Client only. */
    private final ForgeConfigSpec.BooleanValue rightClickCyclesProfilesBack;

    static {
        Pair<Config, ForgeConfigSpec> pair =
                new ForgeConfigSpec.Builder().configure(Config::new);
        INSTANCE = pair.getLeft();
        SPEC = pair.getRight();
    }

    /**
     * A toggle's value, or its default if the file has not been read yet.
     *
     * <p>Lost Cities reads {@code config/lostcities/profiles} from its own
     * constructor, which runs before any mod's config is loaded, and asking a
     * {@code ConfigValue} for its value before then throws. The default makes that
     * early pass behave as a fresh install does.
     */
    private static boolean read(ForgeConfigSpec.BooleanValue value) {
        return SPEC.isLoaded() ? value.get() : value.getDefault();
    }

    public static boolean catchSphereFeatureErrors() {
        return read(INSTANCE.catchSphereFeatureErrors);
    }

    public static boolean detailedFaultReports() {
        return read(INSTANCE.detailedFaultReports);
    }

    public static boolean validateOnLoad() {
        return read(INSTANCE.validateOnLoad);
    }

    public static boolean acceptCommentsAndTrailingCommas() {
        return read(INSTANCE.acceptCommentsAndTrailingCommas);
    }

    public static boolean acceptJson5Extension() {
        return read(INSTANCE.acceptJson5Extension);
    }

    public static boolean warnOnJson5Override() {
        return read(INSTANCE.warnOnJson5Override);
    }

    public static boolean fixBelowPart() {
        return read(INSTANCE.fixBelowPart);
    }

    public static boolean fixFullStreetShape() {
        return read(INSTANCE.fixFullStreetShape);
    }

    public static boolean anchorCitiesButton() {
        return read(INSTANCE.anchorCitiesButton);
    }

    public static boolean fixCustomizeCrash() {
        return read(INSTANCE.fixCustomizeCrash);
    }

    public static boolean rightClickCyclesProfilesBack() {
        return read(INSTANCE.rightClickCyclesProfilesBack);
    }

    private Config(ForgeConfigSpec.Builder builder) {
        builder.comment(
                "The Lost Cities - DevTool",
                "",
                "Settings under 'diagnostics' only change what is reported and are safe",
                "to leave on. Settings under 'repairs' change what generates, so a world",
                "made with one enabled will not come out the same without it.");

        builder.comment(
                "Reporting only. Nothing here alters block placement.")
                .push("diagnostics");

        catchSphereFeatureErrors = builder
                .comment("Catch generation faults raised through LostCitySphereFeature.",
                        "",
                        "That class has no try/catch of its own, while LostCityFeature wraps",
                        "the same work in one. So on landscapeType spheres, cavernspheres or",
                        "space, a fault that would normally be logged per chunk escapes to",
                        "vanilla's feature placer instead. Measured on 7.4.12 with a single",
                        "broken building: 35 faults caught and none escaping on landscapeType",
                        "default, against 18 caught and 21 escaping on spheres, where the",
                        "server then shut down.",
                        "",
                        "With this on, those faults are logged in the same shape the terrain",
                        "feature uses and generation continues to the next chunk.")
                .define("catchSphereFeatureErrors", true);

        detailedFaultReports = builder
                .comment("Add a fuller report beside each caught generation fault.",
                        "",
                        "The mod logs 'Error generating chunk x,z: message'. Those",
                        "coordinates are the chunk being generated, which is often not the",
                        "chunk at fault, because a fault raised while building a chunk's",
                        "info spreads to every neighbour that queries it. The palette",
                        "message names the part rather than the palette that failed to",
                        "define the character. And the JVM stops recording stack traces for",
                        "a repeatedly thrown exception, so most lines in a long run carry",
                        "only a message.",
                        "",
                        "This adds a second line naming the profile, world style, city",
                        "style, building, floor and cellar counts, the whole cause chain,",
                        "and for a missing palette character its code point and where to",
                        "look for it. Nothing the mod logs is suppressed.")
                .define("detailedFaultReports", true);

        validateOnLoad = builder
                .comment("Check every Lost Cities asset file when datapacks load.",
                        "",
                        "The mod discovers these faults during generation instead, one chunk",
                        "at a time, often thousands of times over and with the coordinates of",
                        "a chunk that only asked about the one at fault. Everything checked",
                        "here is decidable from a single file, so it is reported once, at",
                        "load, with a file name and a line number.",
                        "",
                        "Checked: level coverage against the declared floor and cellar",
                        "bounds, inpart and belowpart in a building's parts, a range that",
                        "does not parse or carries a third number, loot and mob holding an ID",
                        "rather than a Condition name, a char longer than one code unit or",
                        "starting above U+FFFF, a weighted list that misses or overruns its",
                        "128 slots, a slices layer that is not xsize by zsize characters, a",
                        "level test written with the wrong type, a Condition entry with a",
                        "negative factor, factors totalling nothing or a key nothing reads,",
                        "and a monorail part written as a list, which Lost Cities replaces",
                        "with its own default part.",
                        "",
                        "Also on /reload, where it reads the files on disk: a Condition whose",
                        "factor or value cannot be read stops the server starting, and this",
                        "says so before the restart does.",
                        "",
                        "Reports only. Nothing is prevented from loading.")
                .define("validateOnLoad", true);

        acceptCommentsAndTrailingCommas = builder
                .comment("Accept comments and trailing commas in Lost Cities asset files.",
                        "",
                        "Both are rejected by strict JSON with a message that names an",
                        "offset rather than a cause, and both are what a hand-written asset",
                        "file wants. This is a subset of JSON5: unquoted keys and single",
                        "quotes are not accepted, because they change what a valid file looks",
                        "like without solving a problem an author has.",
                        "",
                        "Scoped by path. Only files under data/<namespace>/lostcities/ are",
                        "affected. No other mod's files, and none of Minecraft's own, are",
                        "touched.",
                        "",
                        "A file written with comments will not load for anyone who does not",
                        "have this mod. Keep that in mind before shipping a pack that uses",
                        "them.")
                .define("acceptCommentsAndTrailingCommas", true);

        acceptJson5Extension = builder
                .comment("Let a Lost Cities asset or profile be named .json5.",
                        "",
                        "Nothing in Minecraft or in Lost Cities reads a .json5 file.",
                        "Datapack assets are listed with a filter on '.json' and their id",
                        "is then derived by stripping exactly five characters, so a .json5",
                        "is either invisible or registered under a mangled name. Profiles",
                        "are filtered on '.json' too, by File.listFiles.",
                        "",
                        "With this on, a .json5 is presented to both loaders under its",
                        ".json name, and is always read with comments and trailing commas",
                        "allowed whatever the setting above says. The point of the",
                        "extension is that an editor recognises it: VS Code and IntelliJ",
                        "both treat .json5 as commentable, so a hand-written asset stops",
                        "being underlined in red.",
                        "",
                        "Where both names exist the .json5 wins. Lost Cities rewrites every",
                        "profile it ships as .json on each launch, so the opposite rule",
                        "would make overriding a shipped profile impossible.",
                        "",
                        "Scoped the same way as the setting above: data/<namespace>/",
                        "lostcities/ and config/lostcities/profiles, nothing else.",
                        "",
                        "The profiles folder is read before this file is, so a change here",
                        "reaches profiles at the next launch. Datapack assets pick it up on",
                        "the next world load or /reload.")
                .define("acceptJson5Extension", true);

        warnOnJson5Override = builder
                .comment("Report a .json that a .json5 of the same name is shadowing.",
                        "",
                        "Both files register the same asset under the same name, and only",
                        "the .json5 is read. In an editor they sit next to each other",
                        "looking interchangeable, so an edit to the wrong one changes",
                        "nothing and gives no sign of why.",
                        "",
                        "Reported in the log at load, and once in chat to any operator",
                        "joining, because a log line scrolls past and this one is worth",
                        "seeing. An override is not an error and nothing is prevented.",
                        "",
                        "Set to false if you keep both on purpose.")
                .define("warnOnJson5Override", true);

        builder.pop();

        builder.comment(
                "fixBelowPart and fixFullStreetShape change what generates, so both",
                "default to false. Turn one on only if you want the change, and expect",
                "a world generated with it to differ from the same seed without it.",
                "The three client repairs change no generation and default to true.")
                .push("repairs");

        fixBelowPart = builder
                .comment("Make 'belowpart' test the part below, as its name says.",
                        "",
                        "The predicate the mod compiles for belowpart reads the CURRENT",
                        "part, which is byte for byte what inpart compiles to, so the two",
                        "keys are the same test today. The value belowpart needs is already",
                        "passed in and stored, in a field with no accessor, so only the read",
                        "is wrong.",
                        "",
                        "A building gated on belowpart currently fails every chunk it stands",
                        "in, and takes its neighbours with it, so switching this on can only",
                        "turn a failing building into a working one. A building written to",
                        "exploit the broken behaviour, by gating on belowpart with the value",
                        "of the current part, would change.",
                        "",
                        "inpart is left alone. It reads the current part, which is what its",
                        "name says. In a building's parts list that is always <none>,",
                        "because the loop has not chosen a part yet.")
                .define("fixBelowPart", false);

        fixFullStreetShape = builder
                .comment("Make the 'full' street shape reachable.",
                        "",
                        "The street type is picked with nextInt(0, values().length - 2).",
                        "The bound is exclusive and the enum holds NORMAL, FULL and PARK, so",
                        "the expression is nextInt(0, 1) and only NORMAL is ever chosen. PARK",
                        "has its own branch above, so the subtraction was meant to exclude",
                        "PARK and excludes FULL as well by being one too large.",
                        "",
                        "Confirmed unreachable in 7.4.12 through 10.0.1: a pack overriding",
                        "only the full shape produced no marked chunk anywhere.",
                        "",
                        "This changes street layouts. A city style that does not define",
                        "streetblocks.parts.full will start using whatever it inherits for",
                        "that shape.")
                .define("fixFullStreetShape", false);

        anchorCitiesButton = builder
                .comment("Keep the Cities button anchored to the right edge on resize.",
                        "",
                        "The button is built at width - 100, correct for the width it was",
                        "built with, and never recomputed. After a resize it keeps the old",
                        "coordinate and lands over the middle of the screen, on top of the",
                        "vanilla buttons. The preview image beside it is drawn from the",
                        "current width every frame, so the picture moves and the button does",
                        "not.",
                        "",
                        "Client only, and it changes nothing about generation, so unlike the",
                        "other repairs this one defaults to on.")
                .define("anchorCitiesButton", true);

        fixCustomizeCrash = builder
                .comment("Stop the Customize button crashing the game.",
                        "",
                        "Leaving a world clears the profile list. toggleProfile rebuilds it",
                        "when it finds it null, and customize does not, so pressing Customize",
                        "after having played a world throws a NullPointerException and the",
                        "game closes to a crash report.",
                        "",
                        "Reproduce it by playing a world, quitting to the title screen, then",
                        "creating a new world and pressing Customize on the Cities screen.",
                        "",
                        "The repair rebuilds the list the same way toggleProfile does, and",
                        "only when it is null. Client only, changes no generation, on by",
                        "default.")
                .define("fixCustomizeCrash", true);

        rightClickCyclesProfilesBack = builder
                .comment("Right-click the profile button to cycle backwards.",
                        "",
                        "Left-click cycles forward and wraps around, so stepping back",
                        "one profile means clicking through the whole list. The button",
                        "is a plain vanilla Button, whose click handler accepts the left",
                        "button only, so a right-click on it currently does nothing at",
                        "all.",
                        "",
                        "The order is the one the forward cycle uses: 'default' first,",
                        "then by code point on the profile name, with the disabled state",
                        "between the last entry and the first. Going back from disabled",
                        "reaches the last profile.",
                        "",
                        "Client only, changes no generation, on by default.")
                .define("rightClickCyclesProfilesBack", true);

        builder.pop();
    }
}
