package com.rinkynooble.lostcitiesdevtool.command;

import com.mojang.brigadier.CommandDispatcher;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.workshop.Catalogue;
import com.rinkynooble.lostcitiesdevtool.workshop.Layout;
import com.rinkynooble.lostcitiesdevtool.workshop.Workshop;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * {@code /lcdev workshop}: the place a pack is built.
 *
 * <p>{@code go} takes you there, {@code build} lays the catalogue out, {@code rows}
 * lists what the target version declares, and {@code here} says which plot you are
 * standing on.
 *
 * <p>Building needs permission, because it writes tens of thousands of blocks.
 * Looking does not.
 */
public class WorkshopCommand {

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("lcdev")
                .then(Commands.literal("workshop")
                        .then(Commands.literal("go")
                                .executes(WorkshopCommand::go))
                        .then(Commands.literal("build")
                                .requires(s -> s.hasPermission(2))
                                .executes(WorkshopCommand::build))
                        .then(Commands.literal("rows")
                                .executes(WorkshopCommand::rows))
                        .then(Commands.literal("here")
                                .executes(WorkshopCommand::here))));
    }

    // ---------------------------------------------------------------------- go

    private static int go(com.mojang.brigadier.context.CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        ServerLevel workshop = Workshop.level(source.getServer());
        if (workshop == null) {
            Chat.fail(source, "The workshop dimension is not loaded",
                    String.valueOf(Workshop.DIMENSION.location()),
                    "It ships with this mod as a built-in datapack. If it is missing, "
                            + "the mod's own resources did not load");
            return 0;
        }
        ServerPlayer player;
        try {
            player = source.getPlayerOrException();
        } catch (Exception e) {
            Chat.fail(source, "Only a player can be sent to the workshop", null,
                    "Run it in game rather than from the console or RCON");
            return 0;
        }
        // Above the floor, over the front desk at the origin.
        player.teleportTo(workshop, 8.5, Layout.FLOOR_Y + 1.0, 8.5,
                player.getYRot(), player.getXRot());
        Chat.header(source, "Workshop", "version " + Catalogue.version());
        Chat.note(source, "The front desk is the plot you are standing on. "
                + "Buildings are east, infrastructure is west.");
        return 1;
    }

    // ------------------------------------------------------------------- build

    private static int build(com.mojang.brigadier.context.CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        ServerLevel workshop = Workshop.level(source.getServer());
        if (workshop == null) {
            Chat.fail(source, "The workshop dimension is not loaded",
                    String.valueOf(Workshop.DIMENSION.location()), null);
            return 0;
        }
        if (Catalogue.rows().isEmpty()) {
            Chat.fail(source, "The catalogue is empty", "catalogue.json",
                    "The mod's own resource did not load, so there is nothing to lay "
                            + "out");
            return 0;
        }

        long started = System.currentTimeMillis();
        Workshop.Built built = Workshop.build(workshop);
        long took = System.currentTimeMillis() - started;

        Chat.header(source, "Workshop built", "version " + Catalogue.version());
        Chat.kv(source, "rows", String.valueOf(Catalogue.rows().size()));
        Chat.kv(source, "plots", String.valueOf(built.plots()));
        Chat.kv(source, "chunks", String.valueOf(built.chunks()));
        Chat.kv(source, "floor blocks", String.valueOf(built.blocks()));
        Chat.kv(source, "took", took + " ms");
        Chat.path(source, "registry",
                Workshop.registryPath(source.getServer()).toString());
        Chat.note(source, "Re-running repaints rather than duplicating: the layout is "
                + "computed from the catalogue, so it is the same every time.");
        return 1;
    }

    // -------------------------------------------------------------------- rows

    private static int rows(com.mojang.brigadier.context.CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        List<Catalogue.Row> all = Catalogue.rows();
        if (all.isEmpty()) {
            Chat.fail(source, "The catalogue is empty", "catalogue.json", null);
            return 0;
        }

        Chat.header(source, "Catalogue", "version " + Catalogue.version());

        Map<String, Integer> families = new LinkedHashMap<>();
        int plots = 0;
        int dead = 0;
        for (Catalogue.Row r : all) {
            families.merge(r.family(), 1, Integer::sum);
            plots += r.plots();
            if (r.dead() != null) {
                dead++;
            }
        }
        for (Map.Entry<String, Integer> e : families.entrySet()) {
            Chat.kv(source, e.getKey(), e.getValue() + " rows");
        }
        Chat.kv(source, "total", all.size() + " rows, " + plots + " plots");

        // The three classes are the reason two rows that look alike need different
        // settings, so they are worth stating rather than leaving to be discovered.
        long list = all.stream().filter(r -> r.kind() == Catalogue.Kind.PART_LIST).count();
        long single = all.stream().filter(r -> r.kind() == Catalogue.Kind.SINGLE).count();
        long selector = all.stream().filter(r -> r.kind() == Catalogue.Kind.SELECTOR).count();
        Chat.kv(source, "unweighted lists", list + " rows, any number of variations");
        Chat.kv(source, "single only", single + " rows, exactly one variation each");
        Chat.kv(source, "weighted selectors", selector + " rows, each variation needs a factor");
        if (dead > 0) {
            Chat.warn(source, dead + " row" + (dead == 1 ? "" : "s")
                    + " parse and never generate unmodded. Stand on one for the detail.");
        }
        return 1;
    }

    // -------------------------------------------------------------------- here

    private static int here(com.mojang.brigadier.context.CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        BlockPos pos = BlockPos.containing(source.getPosition());
        Layout.Plot plot = Layout.at(Layout.plots(), pos.getX(), pos.getZ());
        if (plot == null) {
            Chat.header(source, "Walkway");
            Chat.note(source, "No plot here. Every plot is chunk aligned with a chunk "
                    + "of walkway around it.");
            return 0;
        }

        Catalogue.Row row = plot.row();
        Chat.header(source, plot.id(), plot.width() + "x" + plot.height() + " chunks");
        Chat.kv(source, "corner", plot.blockMinX() + "," + plot.blockMinZ()
                + " to " + plot.blockMaxX() + "," + plot.blockMaxZ());
        Chat.position(source, "settings corner", plot.chestX(),
                Layout.FLOOR_Y + 1, plot.chestZ());
        if (row == null) {
            Chat.kv(source, "holds", "the pack's own settings");
            Chat.note(source, "Namespace, profile, world style and output format live "
                    + "here. Not a shape.");
            return 1;
        }

        Chat.kv(source, "key", row.key());
        Chat.kv(source, "variation", (plot.index() + 1) + " of " + row.plots());
        switch (row.kind()) {
            case SINGLE -> Chat.kv(source, "variations allowed", "one, and only one. "
                    + "The codec takes a string, so a list is a load error");
            case PART_LIST -> Chat.kv(source, "variations allowed", "any number, "
                    + "picked uniform random. There is no weight");
            case SELECTOR -> Chat.kv(source, "variations allowed", "any number, "
                    + "each weighted by its own factor");
        }
        Chat.kv(source, "compiles into", row.cityStyleScoped()
                ? "a city style, so this plot has to name one"
                : "the world style, which a pack has exactly one of");
        if (row.dead() != null) {
            Chat.warn(source, "This shape never generates unmodded.");
            Chat.prose(source, row.dead());
        }
        return 1;
    }
}
