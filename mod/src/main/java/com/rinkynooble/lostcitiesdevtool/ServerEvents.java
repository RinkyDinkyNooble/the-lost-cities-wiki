package com.rinkynooble.lostcitiesdevtool;

import com.rinkynooble.lostcitiesdevtool.command.ExportCommand;
import com.rinkynooble.lostcitiesdevtool.command.ImportCommand;
import com.rinkynooble.lostcitiesdevtool.command.PlotCommand;
import com.rinkynooble.lostcitiesdevtool.command.ReportCommand;
import com.rinkynooble.lostcitiesdevtool.command.WorkshopCommand;
import com.rinkynooble.lostcitiesdevtool.json5.Json5Listener;
import com.rinkynooble.lostcitiesdevtool.json5.Json5Overrides;
import com.rinkynooble.lostcitiesdevtool.validate.ValidationListener;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.event.AddReloadListenerEvent;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.List;

/**
 * Hooks the asset check and the JSON5 override check onto datapack loading, which
 * happens on world load and on every {@code /reload}.
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
        event.addListener(new Json5Listener());
    }

    @SubscribeEvent
    public static void onRegisterCommands(RegisterCommandsEvent event) {
        ReportCommand.register(event.getDispatcher());
        WorkshopCommand.register(event.getDispatcher());
        PlotCommand.register(event.getDispatcher());
        PlotCommand.registerMark(event.getDispatcher());
        ExportCommand.register(event.getDispatcher());
        ImportCommand.register(event.getDispatcher());
    }

    /**
     * Says once, in chat, which files are shadowed.
     *
     * <p>The log carries the same wording, but a shadowed file is the kind of fault an
     * author hits while testing rather than while reading logs, and the symptom is an
     * edit that appears to do nothing.
     *
     * <p>Operators only. On a shared server nobody else can act on it, and the profile
     * half of the list is settled before any player is in a position to change it.
     */
    /**
     * Read back the rows a previous import grew, before anything asks the layout
     * where a plot is.
     *
     * <p>Without this a build after a restart would lay the catalogue out at its
     * default sizes, and every plot an import added past those would be orphaned:
     * still full of blocks, no longer part of the catalogue, and invisible to the
     * export.
     */
    @SubscribeEvent
    public static void onServerStarted(net.minecraftforge.event.server.ServerStartedEvent event) {
        com.rinkynooble.lostcitiesdevtool.workshop.Workshop
                .loadGrownRows(event.getServer());
    }

    @SubscribeEvent
    public static void onPlayerJoin(PlayerEvent.PlayerLoggedInEvent event) {
        if (!Config.on(Config.INSTANCE.warnOnJson5Override, true)) {
            return;
        }
        List<String> overrides = Json5Overrides.all();
        if (overrides.isEmpty() || !(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        if (!player.hasPermissions(2)) {
            return;
        }
        player.sendSystemMessage(Component.literal(Json5Listener.describe(overrides))
                .withStyle(ChatFormatting.GOLD));
    }
}
