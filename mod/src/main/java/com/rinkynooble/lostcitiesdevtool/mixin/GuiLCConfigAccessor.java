package com.rinkynooble.lostcitiesdevtool.mixin;

import mcjty.lostcities.gui.GuiLCConfig;
import net.minecraft.client.gui.components.Button;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;
import org.spongepowered.asm.mixin.gen.Invoker;

/**
 * Reaches the two members feature 4.2 needs on the Cities screen.
 *
 * <p>The profile button is private and there is no getter, and the method that
 * rewrites every button's label after a change is private too. Both are read only
 * here: nothing about the screen is altered, and with the feature switched off
 * neither is called.
 *
 * <p>{@code remap = false} throughout. This is a Lost Cities class, so its names are
 * already the ones in the jar.
 */
@Mixin(value = GuiLCConfig.class, remap = false)
public interface GuiLCConfigAccessor {

    @Accessor("profileButton")
    Button lostcitiesdevtool$profileButton();

    /** Rewrites the button labels from the current setup, as the left click does. */
    @Invoker("updateValues")
    void lostcitiesdevtool$updateValues();
}
