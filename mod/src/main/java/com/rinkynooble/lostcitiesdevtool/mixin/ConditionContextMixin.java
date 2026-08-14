package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import mcjty.lostcities.worldgen.lost.cityassets.ConditionContext;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Repair 3.1. Makes {@code belowpart} test the part below.
 *
 * <p>{@code ConditionContext.parseTest} compiles the {@code belowpart} entry into a
 * predicate that calls {@code getPart()}, which is the current part. That is byte for
 * byte the predicate {@code inpart} compiles to, so the two keys are the same test
 * and neither reports what is underneath. Present in 7.4.12, 7.5.1, 8.4.1, 9.5.1 and
 * 10.0.1, and not declared at all in 8.2.2.
 *
 * <p>Only the read is wrong. The floor loop already tracks the part chosen for the
 * previous level and passes it into the constructor, where it is stored in a field
 * with no accessor. So the value {@code belowpart} needs is present and correct at
 * the point the predicate runs, and redirecting the read is the whole repair.
 *
 * <p>{@code inpart} is left alone. It reads the current part, which is what its name
 * says, and in a building's part list that is always the literal {@code <none>}
 * because the loop has not chosen a part yet. That is inherent to when the question
 * is asked rather than a fault.
 *
 * <p>This changes what generates. A building whose parts are gated on
 * {@code belowpart} currently fails every chunk it stands in, so switching the repair
 * on can only turn a failing building into a working one. A building written to work
 * around the bug, by gating on {@code belowpart} with the value of the current part,
 * would change.
 *
 * <p>The lambda is targeted by name. That is fragile in general and safe here,
 * because this mod declares a Lost Cities dependency narrow enough to pin the shape
 * of the compiled code, and the mixin fails loudly at load rather than silently doing
 * nothing if the name ever moves.
 */
@Mixin(ConditionContext.class)
public abstract class ConditionContextMixin {

    @Redirect(
            method = "lambda$parseTest$7(Ljava/util/Set;"
                    + "Lmcjty/lostcities/worldgen/lost/cityassets/ConditionContext;)Z",
            remap = false,
            at = @At(value = "INVOKE",
                    remap = false,
                    target = "Lmcjty/lostcities/worldgen/lost/cityassets/ConditionContext;"
                            + "getPart()Ljava/lang/String;"))
    private static String lostcitiesdevtool$readBelowPart(ConditionContext context) {
        if (!Config.INSTANCE.fixBelowPart.get()) {
            return context.getPart();
        }
        return ((ConditionContextAccessor) context).lostcitiesdevtool$belowPart();
    }
}
