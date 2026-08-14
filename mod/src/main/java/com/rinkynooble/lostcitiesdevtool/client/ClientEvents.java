package com.rinkynooble.lostcitiesdevtool.client;

import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.worldselection.CreateWorldScreen;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Repair 4.1. Keeps the Cities button anchored to the right edge.
 *
 * <p>Lost Cities creates the button at {@code (screen.width - 100, 40, 70, 20)},
 * which is anchored to the right edge and correct at the moment it is built. The
 * position is then never recomputed, so after the window is resized the button keeps
 * the coordinate it was given for the old width and ends up over the middle of the
 * screen, on top of the vanilla buttons.
 *
 * <p>The preview image beside it is drawn every frame from the current width, so it
 * moves correctly. That split is what makes the fault easy to see: the picture goes
 * to the right edge and the button does not follow.
 *
 * <p>Correcting the position each frame is deliberate. It costs one comparison, it
 * covers the case where the screen is rebuilt as well as the case where it is not,
 * and it leaves the button exactly where Lost Cities intended it.
 */
@Mod.EventBusSubscriber(modid = LostCitiesDevTool.MOD_ID, value = Dist.CLIENT)
public class ClientEvents {

    /** The offset Lost Cities builds the button with. */
    private static final int RIGHT_MARGIN = 100;

    @SubscribeEvent
    public static void onScreenRender(ScreenEvent.Render.Pre event) {
        if (!Config.INSTANCE.anchorCitiesButton.get()) {
            return;
        }
        Screen screen = event.getScreen();
        if (!(screen instanceof CreateWorldScreen)) {
            return;
        }
        int wanted = screen.width - RIGHT_MARGIN;
        for (GuiEventListener child : screen.children()) {
            if (!(child instanceof Button button)) {
                continue;
            }
            if (!"Cities".equals(button.getMessage().getString())) {
                continue;
            }
            if (button.getX() != wanted) {
                button.setX(wanted);
            }
            return;
        }
    }
}
