package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import mcjty.lostcities.worldgen.lost.BuildingInfo;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import mcjty.lostcities.worldgen.lost.BuildingInfo.StreetType;

/**
 * Feature 1.3. Names the building and the chunk in the misconfiguration message.
 *
 * <p>The mod throws {@code Misconfiguration! Floor were generated for a building
 * where no part condition matches!} with no indication of which building, and it
 * throws it while a chunk's {@code BuildingInfo} is being constructed. Every chunk
 * that queries that chunk then fails the same way, and those queries chain, so the
 * failed region reaches several chunks past the building at fault. Measured on
 * 7.4.12: three broken buildings, 77 failed chunks, a 13 by 10 chunk area.
 *
 * <p>The coordinates in the mod's own line are therefore where the question was
 * asked, not where the answer went wrong. Here, at the throw, both are known
 * exactly, so no search is needed.
 *
 * <p>The added text is appended to the mod's message rather than replacing it, so
 * the string an author searches for still matches.
 */
@Mixin(BuildingInfo.class)
public abstract class BuildingInfoMixin {

    /**
     * The bound that reaches FULL, worked out once.
     *
     * <p>It cannot change at runtime, and {@code Enum.values()} clones its backing
     * array on every call. This is read per street chunk.
     */
    private static final int FULL_STREET_BOUND = StreetType.values().length - 1;

    /**
     * Repair 3.2. Makes the {@code full} street shape reachable.
     *
     * <p>The street type is chosen with
     * {@code StreetType.values()[random.nextInt(0, values().length - 2)]}. The bound
     * of {@code nextInt(origin, bound)} is exclusive, and the enum holds NORMAL,
     * FULL and PARK, so the expression is {@code nextInt(0, 1)} and only NORMAL can
     * ever come out. PARK is set by its own branch above, so the subtraction was
     * meant to exclude it, and excludes FULL as well by being one too large.
     *
     * <p>Confirmed unreachable in 7.4.12 through 10.0.1: a pack that overrode only
     * the {@code full} shape produced no marked chunk anywhere.
     *
     * <p>This changes what generates. Street layouts gain a shape they have never
     * had, which is the point, and a city style that leaves {@code streetblocks.parts.full}
     * undefined will start using whatever it inherits for that shape.
     *
     * <p>There is exactly one {@code nextInt(int, int)} call in this class, so no
     * slice is needed to identify it.
     */
    @ModifyArg(
            method = "<init>(Lmcjty/lostcities/varia/ChunkCoord;"
                    + "Lmcjty/lostcities/worldgen/IDimensionInfo;)V",
            remap = false,
            at = @At(value = "INVOKE", remap = false,
                    target = "Ljava/util/Random;nextInt(II)I"),
            index = 1)
    private int lostcitiesdevtool$reachFullStreet(int bound) {
        if (!Config.INSTANCE.fixFullStreetShape.get()) {
            return bound;
        }
        // Restore the one the subtraction removed, and keep PARK excluded.
        return FULL_STREET_BOUND;
    }

    @ModifyArg(
            method = "<init>(Lmcjty/lostcities/varia/ChunkCoord;"
                    + "Lmcjty/lostcities/worldgen/IDimensionInfo;)V",
            remap = false,
            at = @At(value = "INVOKE",
                    remap = false,
                    target = "Ljava/lang/RuntimeException;<init>(Ljava/lang/String;)V"),
            index = 0)
    private String lostcitiesdevtool$nameTheBuilding(String message) {
        if (!Config.INSTANCE.detailedFaultReports.get()) {
            return message;
        }
        BuildingInfo self = (BuildingInfo) (Object) this;
        StringBuilder sb = new StringBuilder(message);
        try {
            sb.append("  [building ");
            if (self.getBuilding() != null) {
                sb.append(self.getBuilding().getId());
            } else {
                sb.append("unknown");
            }
            sb.append(" at chunk ").append(self.coord.chunkX())
              .append(',').append(self.coord.chunkZ());
            sb.append(", levels ").append(-self.getNumCellars())
              .append(" to ").append(self.getNumFloors()).append(" inclusive");
            sb.append(". Every chunk that queries this one fails the same way]");
        } catch (Exception e) {
            // The object is mid-construction. Whatever is readable is worth keeping.
            sb.append(" unavailable: ").append(e.getClass().getSimpleName()).append(']');
        }
        return sb.toString();
    }
}
