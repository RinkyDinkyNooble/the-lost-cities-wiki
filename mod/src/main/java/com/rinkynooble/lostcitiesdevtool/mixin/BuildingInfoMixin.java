package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import mcjty.lostcities.worldgen.lost.BuildingInfo;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArg;

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
