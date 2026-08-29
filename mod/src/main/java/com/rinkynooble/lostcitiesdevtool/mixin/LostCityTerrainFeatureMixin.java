package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import mcjty.lostcities.worldgen.LostCityTerrainFeature;
import mcjty.lostcities.worldgen.lost.BuildingInfo.StreetType;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArg;

/**
 * Repair 3.2, the half that decides what is actually built.
 *
 * <p>The same expression appears twice. {@code BuildingInfo} rolls a street type
 * when the chunk's info is built, and {@code generateStreet} rolls it again and
 * overwrites the stored value before switching on it. The second roll is the one
 * that reaches {@code generateFullStreetSection}, so patching only the first changes
 * nothing anybody can see.
 *
 * <p>Both are {@code nextInt(0, StreetType.values().length - 2)}. The bound of
 * {@code nextInt(origin, bound)} is exclusive and the enum holds NORMAL, FULL and
 * PARK, so the expression is {@code nextInt(0, 1)} and only NORMAL is ever chosen.
 * PARK has its own branch above, so the subtraction was meant to exclude PARK and
 * removes FULL as well by being one too large.
 *
 * <p>There is exactly one {@code nextInt(int, int)} call in this class, so no slice
 * is needed to identify it.
 */
@Mixin(LostCityTerrainFeature.class)
public abstract class LostCityTerrainFeatureMixin {

    /**
     * The bound that reaches FULL, worked out once.
     *
     * <p>It cannot change at runtime, and {@code Enum.values()} clones its backing
     * array on every call. This is read per street chunk.
     */
    private static final int FULL_STREET_BOUND = StreetType.values().length - 1;

    @ModifyArg(
            method = "generateStreet(Lmcjty/lostcities/worldgen/lost/BuildingInfo;"
                    + "Lmcjty/lostcities/worldgen/ChunkHeightmap;)V",
            remap = false,
            at = @At(value = "INVOKE", remap = false,
                    target = "Ljava/util/Random;nextInt(II)I"),
            index = 1)
    private int lostcitiesdevtool$reachFullStreet(int bound) {
        if (!Config.INSTANCE.fixFullStreetShape.get()) {
            return bound;
        }
        return FULL_STREET_BOUND;
    }
}
