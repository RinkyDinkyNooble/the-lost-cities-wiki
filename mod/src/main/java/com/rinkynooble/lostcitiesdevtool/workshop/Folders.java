package com.rinkynooble.lostcitiesdevtool.workshop;

import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;

import java.nio.file.Path;

/**
 * Where this mod keeps what it writes: one folder beside each world, and one under
 * the game's {@code config} folder.
 *
 * <p>Beside the world for what belongs to one workshop: the plot registry, each
 * plot's settings, the palette ledger and the licences an import copied, so that a
 * world copied or deleted takes them with it. Under {@code config} for what outlives
 * a world: exports, and the copy a wipe takes before destroying anything.
 *
 * <p>Absolute and normalised, because each is printed for someone to click and copy.
 */
public final class Folders {

    /** The folder's name in both places. */
    public static final String NAME = "lostcitiesdevtool";

    private Folders() {
    }

    public static Path world(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve(NAME)
                .toAbsolutePath().normalize();
    }

    public static Path exports() {
        return config().resolve("exports");
    }

    public static Path backups() {
        return config().resolve("backups");
    }

    private static Path config() {
        return Path.of("config", NAME).toAbsolutePath().normalize();
    }
}
