package com.rinkynooble.lostcitiesdevtool;

import com.rinkynooble.lostcitiesdevtool.command.ReportCommand;
import com.rinkynooble.lostcitiesdevtool.validate.ValidationListener;
import net.minecraftforge.event.AddReloadListenerEvent;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Hooks the asset check onto datapack loading, which happens on world load and on
 * every {@code /reload}.
 *
 * <p>Lost Cities does not re-read its own assets on {@code /reload}, so the check
 * running there reports the files on disk rather than the ones in play. That is still
 * the useful direction: it tells an author whether the edit they just made is sound,
 * before they restart to pick it up.
 */
@Mod.EventBusSubscriber(modid = LostCitiesDevTool.MOD_ID)
public class ServerEvents {

    @SubscribeEvent
    public static void onAddReloadListener(AddReloadListenerEvent event) {
        event.addListener(new ValidationListener());
    }

    @SubscribeEvent
    public static void onRegisterCommands(RegisterCommandsEvent event) {
        ReportCommand.register(event.getDispatcher());
    }
}
