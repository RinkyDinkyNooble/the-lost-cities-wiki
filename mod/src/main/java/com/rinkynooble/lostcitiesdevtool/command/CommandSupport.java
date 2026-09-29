package com.rinkynooble.lostcitiesdevtool.command;

import com.rinkynooble.lostcitiesdevtool.platform.LostCitiesDevTool;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.core.Layout;
import com.rinkynooble.lostcitiesdevtool.workshop.Workshop;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import javax.annotation.Nullable;

/**
 * What the workshop commands all have to establish before they can do anything.
 *
 * <p>Each of these was written out at every command that needed it, seven times for
 * the loaded check and six for the plot under the caller, and the copies drifted:
 * none of the plot lookups asked which dimension the caller was in.
 */
final class CommandSupport {

    private CommandSupport() {
    }

    /** The workshop dimension, or null with the failure already reported. */
    @Nullable
    static ServerLevel workshop(CommandSourceStack source) {
        ServerLevel level = Workshop.level(source.getServer());
        if (level == null) {
            Chat.fail(source, "The workshop dimension is not loaded",
                    String.valueOf(Workshop.DIMENSION.location()),
                    "It ships with this mod as a built-in datapack. If it is missing, "
                            + "the mod's own resources did not load");
        }
        return level;
    }

    /** Whether the caller stands in the workshop, as opposed to any other level. */
    static boolean inWorkshop(CommandSourceStack source) {
        return source.getLevel().dimension().equals(Workshop.DIMENSION);
    }

    /**
     * The plot under the caller, or null with the reason already reported.
     *
     * <p><b>Only inside the workshop.</b> A plot is a place in that dimension, and
     * the same x and z anywhere else is somebody's world. Asked from the overworld,
     * {@code plot hide} cleared a ring of blocks from the floor of the world to the
     * build limit, {@code plot show} built glass into it, and {@code plot set} wrote
     * to whichever plot shared the coordinates. The console stands at the overworld
     * spawn, which is usually over the front desk's.
     *
     * @param fix what to do about standing on walkway, which differs by command
     */
    @Nullable
    static Layout.Plot plotUnder(CommandSourceStack source, String fix) {
        if (!inWorkshop(source)) {
            notInWorkshop(source);
            return null;
        }
        BlockPos pos = BlockPos.containing(source.getPosition());
        Layout.Plot plot = Layout.at(Layout.plots(), pos.getX(), pos.getZ());
        if (plot == null) {
            Chat.fail(source, "You are not standing on a plot",
                    pos.getX() + "," + pos.getZ(), fix);
        }
        return plot;
    }

    /** The same, with nothing reported, for tab completion. */
    @Nullable
    static Layout.Plot plotUnderQuietly(CommandSourceStack source) {
        if (!inWorkshop(source)) {
            return null;
        }
        BlockPos pos = BlockPos.containing(source.getPosition());
        return Layout.at(Layout.plots(), pos.getX(), pos.getZ());
    }

    /** The refusal every plot command gives outside the workshop. */
    static void notInWorkshop(CommandSourceStack source) {
        Chat.fail(source, "You are not in the workshop",
                String.valueOf(source.getLevel().dimension().location()),
                "Plots exist only in the workshop dimension. /lcdev workshop go "
                        + "takes you there");
    }

    /** The player running this, or null with the reason already reported. */
    @Nullable
    static ServerPlayer player(CommandSourceStack source, String why) {
        ServerPlayer player = source.getPlayer();
        if (player == null) {
            Chat.fail(source, why, null,
                    "Run it in game rather than from the console or RCON");
        }
        return player;
    }

    /** The body of a command, which may throw. */
    @FunctionalInterface
    interface Body {
        int run() throws Exception;
    }

    /**
     * Runs a command body and reports what went wrong if it throws.
     *
     * <p>Vanilla catches a command's exception, answers "An unexpected error
     * occurred" and puts the message in hover text that a console, an RCON client
     * and a log line all discard. For a tool whose whole purpose is to say what
     * failed, that is the one answer it must never give.
     */
    static int guarded(CommandSourceStack source, String what, Body body) {
        try {
            return body.run();
        } catch (Exception e) {
            LostCitiesDevTool.LOGGER.error("lcdev: {} failed", what, e);
            Chat.fail(source, "The " + what + " failed",
                    e.getClass().getSimpleName()
                            + (e.getMessage() == null ? "" : ": " + e.getMessage()),
                    "The full trace is in the log");
            return 0;
        }
    }
}
