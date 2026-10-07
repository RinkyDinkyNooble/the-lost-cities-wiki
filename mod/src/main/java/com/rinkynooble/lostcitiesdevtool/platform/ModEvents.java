package com.rinkynooble.lostcitiesdevtool.platform;

import com.rinkynooble.lostcitiesdevtool.json5.Json5Listener;
import com.rinkynooble.lostcitiesdevtool.json5.Json5Overrides;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;

import java.util.List;

/**
 * The first point in startup where the config file has been read.
 *
 * <p>Lost Cities reads {@code config/lostcities/profiles} from its own constructor,
 * which is earlier than any mod's config, so a shadowed profile is found before there
 * is a setting to consult about reporting it. It is recorded there and reported here,
 * where {@code warnOnJson5Override} can actually turn it off.
 */
@Mod.EventBusSubscriber(modid = LostCitiesDevTool.MOD_ID,
        bus = Mod.EventBusSubscriber.Bus.MOD)
public class ModEvents {

    @SubscribeEvent
    public static void onCommonSetup(FMLCommonSetupEvent event) {
        // Common setup runs after the config file is read, so a user's `false` turns
        // this off here, where the early callers in Json5Listener still see the
        // default.
        if (!Config.warnOnJson5Override()) {
            return;
        }
        List<String> profiles = Json5Overrides.profiles();
        if (!profiles.isEmpty()) {
            LostCitiesDevTool.LOGGER.warn(Json5Listener.describe(profiles));
        }
    }
}
