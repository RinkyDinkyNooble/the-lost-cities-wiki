package com.rinkynooble.lostcitiesdevtool.mixin;

import mcjty.lostcities.worldgen.lost.cityassets.ConditionContext;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/**
 * Reaches the {@code belowPart} field, which the class stores and never reads.
 *
 * <p>{@code ConditionContext} is handed the part below the current level in its
 * constructor and keeps it in a private field. There is no accessor for that field
 * anywhere in the mod, which is the reason {@code belowpart} does not work: the
 * predicate compiled for it has nothing to read, so it reads the current part
 * instead.
 */
@Mixin(ConditionContext.class)
public interface ConditionContextAccessor {

    @Accessor(value = "belowPart", remap = false)
    String lostcitiesdevtool$belowPart();
}
