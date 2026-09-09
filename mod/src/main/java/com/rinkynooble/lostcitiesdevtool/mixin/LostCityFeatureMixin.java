package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import com.rinkynooble.lostcitiesdevtool.diagnostics.FaultReport;
import com.rinkynooble.lostcitiesdevtool.diagnostics.LastFault;
import mcjty.lostcities.worldgen.ErrorLogger;
import mcjty.lostcities.worldgen.IDimensionInfo;
import mcjty.lostcities.worldgen.LostCityFeature;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Features 1.2 and 1.3. Reports a caught generation fault with everything the mod
 * knows at that point.
 *
 * <p>{@code LostCityFeature} catches every fault raised during chunk generation and
 * logs {@code Error generating chunk <x>,<z>: <message>}. Three things make that
 * line hard to act on.
 *
 * <p>The coordinates are the chunk that was being generated, which is often not the
 * chunk at fault. A fault raised while building a chunk's {@code BuildingInfo}
 * spreads to every neighbour that queries it, and three broken buildings produced 77
 * failed chunks over a 13 by 10 chunk area on 7.4.12.
 *
 * <p>The palette message names the part, when the fault is in a palette that failed
 * to define or resolve the character.
 *
 * <p>The JVM stops recording stack traces for a repeatedly thrown exception, so in a
 * long run most lines carry only a message, or {@code null}.
 *
 * <p>Two calls in the catch block are redirected. Neither is suppressed: the stock
 * output is produced exactly as before, and a fuller report is added beside it, so a
 * log from a modded instance still contains what an unmodded one would.
 */
@Mixin(LostCityFeature.class)
public abstract class LostCityFeatureMixin {

    /**
     * On 7.4.12 the try/catch sat directly in {@code place}. 7.5 moved the body into
     * a chunk neighbourhood locking wrapper and left the catch in the lambda that
     * wrapper calls, so both redirects target the lambda instead. The lambda is
     * static, which is why both handlers below are.
     *
     * <p>A lambda's number is assigned by the compiler and is not part of any
     * contract. This one is {@code $0} in 7.5.1, 7.5.2, 7.5.3 and 7.5.4, checked by
     * descriptor rather than by name alone.
     */
    private static final String PLACE =
            "lambda$place$0(Lnet/minecraft/server/level/WorldGenRegion;"
                    + "Lmcjty/lostcities/worldgen/IDimensionInfo;)Z";

    /**
     * The catch block prints the exception and then calls {@code logChunkInfo}, which
     * is not given it. Capture it here so the second redirect can report it.
     */
    @Redirect(
            method = PLACE,
            remap = false,
            at = @At(value = "INVOKE",
                    target = "Ljava/lang/Exception;printStackTrace()V"))
    private static void lostcitiesdevtool$captureFault(Exception fault) {
        LastFault.set(fault);
        fault.printStackTrace();
    }

    /**
     * {@code remap = false} for the same reason as the sphere mixin: the override
     * carries its SRG name in a shipped jar, and {@code ErrorLogger} is Lost Cities'
     * own class, so neither name has a Minecraft mapping to look up.
     */
    @Redirect(
            method = PLACE,
            remap = false,
            at = @At(value = "INVOKE",
                    remap = false,
                    target = "Lmcjty/lostcities/worldgen/ErrorLogger;logChunkInfo("
                            + "IILmcjty/lostcities/worldgen/IDimensionInfo;)V"))
    private static void lostcitiesdevtool$report(int chunkX, int chunkZ, IDimensionInfo provider) {
        Throwable fault = LastFault.take();

        if (!Config.INSTANCE.detailedFaultReports.get()) {
            ErrorLogger.logChunkInfo(chunkX, chunkZ, provider);
            return;
        }
        try {
            ErrorLogger.logChunkInfo(chunkX, chunkZ, provider);
        } catch (Exception ignored) {
            // logChunkInfo rebuilds this chunk's BuildingInfo, which is the call that
            // threw for a condition fault. The mod reports its own failure here and
            // carries on, and so does this.
        }
        try {
            FaultReport.log(chunkX, chunkZ, provider, fault);
        } catch (Exception e) {
            // A diagnostic must never become the fault.
            LostCitiesDevTool.LOGGER.error("DevTool fault report failed: {}", e.toString());
        }
    }
}
