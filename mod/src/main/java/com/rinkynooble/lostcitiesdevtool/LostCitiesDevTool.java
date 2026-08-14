package com.rinkynooble.lostcitiesdevtool;

import com.mojang.logging.LogUtils;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.config.ModConfig;
import org.slf4j.Logger;

/**
 * Authoring tools for The Lost Cities.
 *
 * <p>The mod adds no content and generates nothing of its own. Features that only
 * affect diagnostics are on by default. Features that change what generates are off
 * by default, so a world made with this mod installed is reproducible without it.
 */
@Mod(LostCitiesDevTool.MOD_ID)
public class LostCitiesDevTool {

    public static final String MOD_ID = "lostcities_devtool";
    public static final Logger LOGGER = LogUtils.getLogger();

    public LostCitiesDevTool() {
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, Config.SPEC);
        LOGGER.info("The Lost Cities - DevTool loaded");
    }
}
