package com.rinkynooble.lostcitiesdevtool;

import net.minecraftforge.common.ForgeConfigSpec;
import org.apache.commons.lang3.tuple.Pair;

/**
 * One toggle per feature, in two groups.
 *
 * <p>{@code diagnostics} only changes what is reported, so every toggle in it
 * defaults to on. {@code repairs} changes what generates, so every toggle in it
 * defaults to off and has to be chosen deliberately.
 */
public class Config {

    public static final ForgeConfigSpec SPEC;
    public static final Config INSTANCE;

    // -- diagnostics, on by default -------------------------------------------

    /** Feature 1.1. Wraps the sphere feature in the catch the terrain feature has. */
    public final ForgeConfigSpec.BooleanValue catchSphereFeatureErrors;

    static {
        Pair<Config, ForgeConfigSpec> pair =
                new ForgeConfigSpec.Builder().configure(Config::new);
        INSTANCE = pair.getLeft();
        SPEC = pair.getRight();
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

        builder.pop();

        builder.comment(
                "Each of these changes what generates. All default to false.",
                "Turn one on only if you want the change, and expect a world generated",
                "with it to differ from the same seed without it.")
                .push("repairs");
        builder.pop();
    }
}
