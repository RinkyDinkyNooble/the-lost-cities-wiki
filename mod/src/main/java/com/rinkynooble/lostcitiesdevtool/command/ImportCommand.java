package com.rinkynooble.lostcitiesdevtool.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.context.CommandContext;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.workshop.Importer;
import com.rinkynooble.lostcitiesdevtool.workshop.Workshop;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.ResourceLocationArgument;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;

import java.io.IOException;
import java.util.List;
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
                        .then(Commands.argument("worldstyle",
                                ResourceLocationArgument.id())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(
                                        Importer.worldStyles(c.getSource().getServer()),
                                        b))
                                .executes(ctx -> run(ctx, true, false))
                                .then(Commands.literal("run")
                                        .executes(ctx -> run(ctx, true, true))
                                        .then(Commands.literal("keep")
                                                .executes(ctx -> run(ctx, false, true))))
                                .then(Commands.literal("keep")
                                        .executes(ctx -> run(ctx, false, false))
                                        .then(Commands.literal("run")
                                                .executes(ctx -> run(ctx, false, true)))))));
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

    /**
     * The world style the typed name meant.
     *
     * <p>A resource location argument rather than a string, because a string
     * argument stops at the colon: {@code lostcities:standard} was a parse error
     * unless it was quoted, which is not a thing anybody should have to know.
     *
     * <p>The cost is that a bare name arrives here as {@code minecraft:} something,
     * since that is the namespace a resource location defaults to. So a name with
     * no namespace of its own is matched against what is loaded: the mod's own
     * {@code lostcities:} first, which is the rule the format itself uses for a bare
     * reference, then any single pack that has it.
     */
    private static String resolve(CommandSourceStack source, ResourceLocation typed) {
        List<String> loaded = Importer.worldStyles(source.getServer());
        String asked = typed.toString();
        if (loaded.contains(asked)) {
            return asked;
        }
        if ("minecraft".equals(typed.getNamespace())) {
            String bare = typed.getPath();
            String lostcities = "lostcities:" + bare;
            if (loaded.contains(lostcities)) {
                return lostcities;
            }
            List<String> matches = loaded.stream()
                    .filter(n -> n.endsWith(":" + bare)).toList();
            if (matches.size() == 1) {
                return matches.get(0);
            }
            if (matches.size() > 1) {
                Chat.warn(source, bare + " is in " + matches.size() + " packs: "
                        + String.join(", ", matches) + ". Name the one you mean.");
            }
        }
        return asked;
    }

    private static int run(CommandContext<CommandSourceStack> ctx, boolean reverse,
                           boolean autoRun) {
        CommandSourceStack source = ctx.getSource();
        String name = resolve(source, ResourceLocationArgument
                .getId(ctx, "worldstyle"));
        ServerLevel workshop = Workshop.level(source.getServer());
        if (workshop == null) {
            Chat.fail(source, "The workshop dimension is not loaded",
                    String.valueOf(Workshop.DIMENSION.location()), null);
            return 0;
        }

        long started = System.currentTimeMillis();
        Importer.Result result;
        try {
            result = Importer.run(source.getServer(), workshop, name, reverse, autoRun);
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
        if (result.leftover() > 0) {
            Chat.warn(source, result.leftover() + " plots this import did not touch "
                    + "already hold something, and an export writes them out too.");
            Chat.note(source, "That is usually a city imported earlier. "
                    + "/lcdev workshop clear empties the workshop, and takes a "
                    + "backup before it does.");
        }
        Chat.note(source, "Every plot filled has settings that would export it back.");
        return 1;
    }
}
