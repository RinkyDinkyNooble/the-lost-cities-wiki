package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.platform.Config;
import com.rinkynooble.lostcitiesdevtool.platform.LostCitiesDevTool;
import com.rinkynooble.lostcitiesdevtool.client.ProfileListAccess;
import com.rinkynooble.lostcitiesdevtool.client.Profiles;
import mcjty.lostcities.gui.LostCitySetup;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.ArrayList;
import java.util.List;

/**
 * Repair 4.4. Stops the Customize button crashing the game.
 *
 * <p>{@code reset()} sets the profile list to null, and it is called when a player
 * leaves a world. {@code toggleProfile()} rebuilds the list lazily when it finds it
 * null, but {@code customize()} does not, and its first act is to add an entry to
 * that list.
 *
 * <p>So the crash reproduces reliably: play a world, quit to the title screen, start
 * creating a new world, open the Cities screen and press Customize.
 *
 * <pre>
 * java.lang.NullPointerException: Cannot invoke "java.util.List.add(Object)"
 *     because "this.profiles" is null
 *   at mcjty.lostcities.gui.LostCitySetup.customize(LostCitySetup.java:95)
 * </pre>
 *
 * <p>The repair rebuilds the list the way {@code toggleProfile} does, from the public
 * entries of {@code ProfileSetup.STANDARD_PROFILES} and in its order, and only when
 * it is null. Nothing happens on the normal path. The order matters because
 * {@code toggleProfile} sorts only a list it built itself: one built here unsorted
 * was stepped through in hash order from then on.
 *
 * <p>It also hands the live list to the backward cycle, through
 * {@link ProfileListAccess}, so that one steps through exactly what the forward
 * cycle does.
 *
 * <p>Client only, and it changes no generation, so it defaults to on.
 */
@Mixin(LostCitySetup.class)
public abstract class LostCitySetupMixin implements ProfileListAccess {

    @Shadow(remap = false)
    private List<String> profiles;

    @Inject(method = "customize()V", remap = false, at = @At("HEAD"))
    private void lostcitiesdevtool$ensureProfiles(CallbackInfo ci) {
        if (!Config.INSTANCE.fixCustomizeCrash.get() || profiles != null) {
            return;
        }
        // A list customize can add to, which the one Profiles returns may not be.
        profiles = new ArrayList<>(Profiles.selectable());
        LostCitiesDevTool.LOGGER.info(
                "Rebuilt the profile list before Customize, which would otherwise "
                        + "have thrown. {} public profiles.", profiles.size());
    }

    @Override
    public List<String> lostcitiesdevtool$profiles() {
        return profiles;
    }
}
