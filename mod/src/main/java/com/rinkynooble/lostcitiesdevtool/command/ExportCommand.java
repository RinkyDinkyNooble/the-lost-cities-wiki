package com.rinkynooble.lostcitiesdevtool.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.ArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.workshop.Exporter;
import com.rinkynooble.lostcitiesdevtool.workshop.Layout;
import com.rinkynooble.lostcitiesdevtool.workshop.Workshop;
import com.rinkynooble.lostcitiesdevtool.validate.Finding;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.server.level.ServerLevel;

import javax.annotation.Nullable;
import java.io.IOException;
import java.util.EnumSet;
import java.util.Set;

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

    /** A word that may follow the name, at most once, in any order. */
    private enum Flag {
        FORCE("-f"), NOTAGS("notags"), PLOT("plot");

        final String word;

        Flag(String word) {
            this.word = word;
        }
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("lcdev")
                .then(Commands.literal("export")
                        .requires(s -> s.hasPermission(2))
                        .then(flags(Commands.argument("name",
                                        StringArgumentType.word()),
                                EnumSet.allOf(Flag.class),
                                EnumSet.noneOf(Flag.class)))));
    }

    /**
     * Hang every remaining flag off this node, in any order.
     *
     * <p>Three independent flags is six orderings written by hand, and four would be
     * twenty four. Brigadier has no notion of an unordered set, so the tree is built
     * rather than typed: each node can be run as it stands, and carries a child for
     * each flag not yet given.
     */
    private static ArgumentBuilder<CommandSourceStack, ?> flags(
            ArgumentBuilder<CommandSourceStack, ?> node, Set<Flag> left,
            Set<Flag> given) {
        node.executes(ctx -> export(ctx, given));
        for (Flag flag : left) {
            Set<Flag> rest = EnumSet.copyOf(left);
            rest.remove(flag);
            Set<Flag> now = EnumSet.noneOf(Flag.class);
            now.addAll(given);
            now.add(flag);
            node.then(flags(Commands.literal(flag.word), rest, now));
        }
        return node;
    }

    private static int export(CommandContext<CommandSourceStack> ctx,
                              Set<Flag> flags) {
        CommandSourceStack source = ctx.getSource();
        String name = StringArgumentType.getString(ctx, "name");
        ServerLevel workshop = Workshop.level(source.getServer());
        if (workshop == null) {
            Chat.fail(source, "The workshop dimension is not loaded",
                    String.valueOf(Workshop.DIMENSION.location()), null);
            return 0;
        }

        String only = null;
        if (flags.contains(Flag.PLOT)) {
            only = plotUnder(source);
            if (only == null) {
                Chat.fail(source, "You are not standing on a plot", null,
                        "`plot` exports the one you are on. Go to it, or leave the "
                        + "word off to export the whole workshop.");
                return 0;
            }
        }

        long started = System.currentTimeMillis();
        Exporter.Result result;
        try {
            result = Exporter.run(source.getServer(), workshop, name,
                    Exporter.Options.of(flags.contains(Flag.FORCE),
                            flags.contains(Flag.NOTAGS), only));
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
        if (only != null) {
            Chat.kv(source, "plot", only);
        }
        Chat.kv(source, "plots read", String.valueOf(result.plots()));
        Chat.kv(source, "parts", String.valueOf(result.parts()));
        if (result.reused() > 0) {
            // Levels of a building that drew the same blocks and now share one file
            // rather than each getting an identical copy of it.
            Chat.kv(source, "levels sharing a part", String.valueOf(result.reused()));
        }
        Chat.kv(source, "buildings", String.valueOf(result.buildings()));
        if (result.licences() > 0) {
            // Said out loud, because a pack shipping somebody else's terms is a
            // thing the person shipping it should know it does.
            Chat.kv(source, "licences carried", result.licences()
                    + ", in lostcities/license.txt");
        }
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
        } else if (only != null) {
            Chat.note(source, "A fragment: this plot's assets and the palette they "
                    + "resolve through, with no city style and no world style. Copy "
                    + "the files into a pack and reference them from its city "
                    + "style. It will not generate anything on its own.");
        }
        return 1;
    }

    /** The plot the caller is standing on, or null for none. */
    @Nullable
    private static String plotUnder(CommandSourceStack source) {
        var pos = source.getPosition();
        Layout.Plot plot = Layout.at(Layout.plots(), (int) Math.floor(pos.x),
                (int) Math.floor(pos.z));
        return plot == null || plot.row() == null ? null : plot.id();
    }
}
