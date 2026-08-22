package com.rinkynooble.lostcitiesdevtool.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.workshop.Importer;
import com.rinkynooble.lostcitiesdevtool.workshop.Workshop;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.server.level.ServerLevel;

import java.io.IOException;
import java.util.Map;

/**
 * {@code /lcdev import <worldstyle>}: a loaded pack, pasted into the workshop.
 *
 * <p>The pack has to be loaded with the world, which is what makes this work at all:
 * the import reads the assets the server already has, so the mod's own built-in
 * content and every datapack in the world are equally importable with nothing to
 * point at and no files to copy.
 *
 * <p>Block conversions run backwards by default, so a placeholder that an export
 * turned into a real block comes back as the placeholder. {@code keep} leaves the
 * real blocks alone.
 */
public class ImportCommand {

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("lcdev")
                .then(Commands.literal("import")
                        .requires(s -> s.hasPermission(2))
                        .executes(ImportCommand::list)
                        .then(Commands.argument("worldstyle", StringArgumentType.string())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(
                                        Importer.worldStyles(c.getSource().getServer()),
                                        b))
                                .executes(ctx -> run(ctx, true))
                                .then(Commands.literal("keep")
                                        .executes(ctx -> run(ctx, false))))));
    }

    private static int list(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        Chat.header(source, "World styles loaded");
        for (String name : Importer.worldStyles(source.getServer())) {
            Chat.kv(source, name, "");
        }
        Chat.note(source, "/lcdev import <name> pastes one into the workshop.");
        return 1;
    }

    private static int run(CommandContext<CommandSourceStack> ctx, boolean reverse) {
        CommandSourceStack source = ctx.getSource();
        String name = StringArgumentType.getString(ctx, "worldstyle");
        ServerLevel workshop = Workshop.level(source.getServer());
        if (workshop == null) {
            Chat.fail(source, "The workshop dimension is not loaded",
                    String.valueOf(Workshop.DIMENSION.location()), null);
            return 0;
        }

        long started = System.currentTimeMillis();
        Importer.Result result;
        try {
            result = Importer.run(source.getServer(), workshop, name, reverse);
        } catch (IOException e) {
            Chat.fail(source, "The import could not run", name,
                    String.valueOf(e.getMessage()));
            return 0;
        } catch (RuntimeException e) {
            // Brigadier turns anything unchecked into "an unexpected error occurred",
            // which tells the person nothing and does not reach the log either. An
            // import walks somebody else's data, so it will meet shapes this code did
            // not expect; saying which one is the difference between a bug report and
            // a shrug.
            Chat.fail(source, "The import hit something it could not read",
                    e.getClass().getSimpleName()
                            + (e.getMessage() == null ? "" : ": " + e.getMessage()),
                    "This is a fault in the import, not in the pack. The stack trace "
                            + "is in the log");
            com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool.LOGGER.error(
                    "import of {} failed", name, e);
            return 0;
        }
        long took = System.currentTimeMillis() - started;

        Chat.header(source, "Imported", result.worldStyle());
        Chat.kv(source, "assets found", String.valueOf(result.assets()));
        Chat.kv(source, "plots filled", String.valueOf(result.plots()));
        Chat.kv(source, "blocks placed", String.valueOf(result.blocks()));
        Chat.kv(source, "conversions", reverse ? "reversed" : "left as written");
        Chat.kv(source, "took", took + " ms");
        if (!result.grown().isEmpty()) {
            int widest = 0;
            for (Map.Entry<String, Integer> e : result.grown().entrySet()) {
                widest = Math.max(widest, e.getValue());
            }
            Chat.kv(source, "rows grown", result.grown().size()
                    + ", the largest to " + widest + " plots");
        }
        if (result.unpinned() > 0) {
            Chat.kv(source, "unpinned buildings", result.unpinned()
                    + ", shown as their alternatives stacked");
            Chat.note(source, "Those pin no floor count: the profile decides how tall "
                    + "they are and the parts are a bag the generator draws from. The "
                    + "plot shows what they can be made of, and pinFloors is false so "
                    + "the export will not invent a count.");
        }
        for (String warning : result.warnings()) {
            Chat.warn(source, warning);
        }
        Chat.note(source, "Every plot filled has settings that would export it back.");
        return 1;
    }
}
