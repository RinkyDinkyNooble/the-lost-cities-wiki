package com.rinkynooble.lostcitiesdevtool.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.workshop.Exporter;
import com.rinkynooble.lostcitiesdevtool.workshop.Workshop;
import com.rinkynooble.lostcitiesdevtool.validate.Finding;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.server.level.ServerLevel;

import java.io.IOException;

/**
 * {@code /lcdev export <name>}: turn the workshop into a datapack.
 *
 * <p>Refuses to overwrite an export of the same name without {@code -f}, because
 * losing a pack to a repeated command is a bad way to learn the command repeats.
 *
 * <p>Nothing is written unless the whole pack passes the checks the mod runs on a
 * datapack at load time. A pack that would fail in a world fails here, where the
 * message can still name the file.
 */
public class ExportCommand {

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("lcdev")
                .then(Commands.literal("export")
                        .requires(s -> s.hasPermission(2))
                        .then(Commands.argument("name", StringArgumentType.word())
                                .executes(ctx -> export(ctx, false, false))
                                // Both orders, because there is no reason to make
                                // somebody remember which flag comes first.
                                .then(Commands.literal("-f")
                                        .executes(ctx -> export(ctx, true, false))
                                        .then(Commands.literal("notags").executes(
                                                ctx -> export(ctx, true, true))))
                                .then(Commands.literal("notags")
                                        .executes(ctx -> export(ctx, false, true))
                                        .then(Commands.literal("-f").executes(
                                                ctx -> export(ctx, true, true)))))));
    }

    private static int export(CommandContext<CommandSourceStack> ctx, boolean force,
                              boolean noTags) {
        CommandSourceStack source = ctx.getSource();
        String name = StringArgumentType.getString(ctx, "name");
        ServerLevel workshop = Workshop.level(source.getServer());
        if (workshop == null) {
            Chat.fail(source, "The workshop dimension is not loaded",
                    String.valueOf(Workshop.DIMENSION.location()), null);
            return 0;
        }

        long started = System.currentTimeMillis();
        Exporter.Result result;
        try {
            result = Exporter.run(source.getServer(), workshop, name, force, noTags);
        } catch (IOException e) {
            Chat.fail(source, "The export could not run", name,
                    String.valueOf(e.getMessage()));
            return 0;
        }
        long took = System.currentTimeMillis() - started;

        if (result.failed()) {
            Chat.fail(source, "Nothing was written: the pack would not load",
                    result.findings().size() + " problem(s)",
                    "Each one below names the asset it is in");
            for (Finding f : result.findings()) {
                if (f.severity() == Finding.Severity.ERROR) {
                    Chat.fail(source, f.message(), f.location(), f.fix());
                }
            }
            return 0;
        }

        Chat.header(source, "Exported", name);
        Chat.kv(source, "plots read", String.valueOf(result.plots()));
        Chat.kv(source, "parts", String.valueOf(result.parts()));
        if (result.reused() > 0) {
            // Levels of a building that drew the same blocks and now share one file
            // rather than each getting an identical copy of it.
            Chat.kv(source, "levels sharing a part", String.valueOf(result.reused()));
        }
        Chat.kv(source, "buildings", String.valueOf(result.buildings()));
        Chat.kv(source, "took", took + " ms");
        Chat.path(source, "written to", result.root().toString());

        for (Finding f : result.findings()) {
            Chat.warn(source, f.message());
            Chat.note(source, f.location() + "  " + f.fix());
        }
        for (String warning : result.warnings()) {
            Chat.warn(source, warning);
        }
        if (result.plots() == 0) {
            Chat.note(source, "No plot had settings, so the pack is empty. "
                    + "/lcdev plot set on a plot is what puts it in.");
        }
        return 1;
    }
}
