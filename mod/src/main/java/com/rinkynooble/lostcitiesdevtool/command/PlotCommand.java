package com.rinkynooble.lostcitiesdevtool.command;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.workshop.Boundaries;
import com.rinkynooble.lostcitiesdevtool.workshop.Catalogue;
import com.rinkynooble.lostcitiesdevtool.workshop.Layout;
import com.rinkynooble.lostcitiesdevtool.workshop.Settings;
import com.rinkynooble.lostcitiesdevtool.workshop.SettingsStore;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;

import javax.annotation.Nullable;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * {@code /lcdev plot}: the settings of whatever plot you are standing on.
 *
 * <p>Editing happens through commands rather than a book or an item, because tab
 * completion is the part that removes the work. Nobody should have to remember that
 * the key is {@code preferslonely} and not {@code prefersLonely}, or that a street
 * has no weight while a park does. The command knows, because the schema does.
 *
 * <p>Every one of these writes a file, and the file is what the exporter reads. The
 * command is a convenience over it, never the other way round.
 */
public class PlotCommand {

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("lcdev")
                .then(Commands.literal("plot")
                        .then(Commands.literal("get")
                                .executes(ctx -> get(ctx, null))
                                .then(Commands.argument("key", StringArgumentType.word())
                                        .suggests(PlotCommand::suggestKeys)
                                        .executes(ctx -> get(ctx,
                                                StringArgumentType.getString(ctx, "key")))))
                        .then(Commands.literal("set")
                                .requires(s -> s.hasPermission(2))
                                .then(Commands.argument("key", StringArgumentType.word())
                                        .suggests(PlotCommand::suggestKeys)
                                        .then(Commands.argument("value",
                                                        StringArgumentType.greedyString())
                                                .suggests(PlotCommand::suggestValues)
                                                .executes(ctx -> set(ctx, null, null)))))
                        // The other two scopes. Each stores only what differs from the
                        // one above it, so a multi-chunk plot says its floor count
                        // once and every chunk in it agrees.
                        .then(Commands.literal("setchunk")
                                .requires(s -> s.hasPermission(2))
                                .then(Commands.argument("dx", IntegerArgumentType.integer(0))
                                        .then(Commands.argument("dz", IntegerArgumentType.integer(0))
                                                .then(Commands.argument("key", StringArgumentType.word())
                                                        .suggests(PlotCommand::suggestKeys)
                                                        .then(Commands.argument("value",
                                                                        StringArgumentType.greedyString())
                                                                .suggests(PlotCommand::suggestValues)
                                                                .executes(ctx -> set(ctx,
                                                                        IntegerArgumentType.getInteger(ctx, "dx")
                                                                                + "," + IntegerArgumentType.getInteger(ctx, "dz"),
                                                                        null)))))))
                        .then(Commands.literal("setlevel")
                                .requires(s -> s.hasPermission(2))
                                .then(Commands.argument("level", IntegerArgumentType.integer(-32, 128))
                                        .then(Commands.argument("key", StringArgumentType.word())
                                                .suggests(PlotCommand::suggestKeys)
                                                .then(Commands.argument("value",
                                                                StringArgumentType.greedyString())
                                                        .suggests(PlotCommand::suggestValues)
                                                        .executes(ctx -> set(ctx, null,
                                                                String.valueOf(IntegerArgumentType
                                                                        .getInteger(ctx, "level"))))))))
                        .then(Commands.literal("clear")
                                .requires(s -> s.hasPermission(2))
                                .then(Commands.argument("key", StringArgumentType.word())
                                        .suggests(PlotCommand::suggestKeys)
                                        .executes(PlotCommand::clear)))
                        .then(Commands.literal("keys")
                                .executes(PlotCommand::keys))
                        // Stacking the tops saves room and hides where the compiler
                        // will cut. This draws the cuts on the walkway, never inside
                        // the plot, and rubs them out again.
                        .then(Commands.literal("show")
                                .requires(s -> s.hasPermission(2))
                                .executes(PlotCommand::show))
                        .then(Commands.literal("hide")
                                .requires(s -> s.hasPermission(2))
                                .executes(PlotCommand::hide))
                        .then(Commands.literal("file")
                                .executes(PlotCommand::file))
                        .then(Commands.literal("resolve")
                                .then(Commands.argument("dx", IntegerArgumentType.integer(0))
                                        .then(Commands.argument("dz", IntegerArgumentType.integer(0))
                                                .then(Commands.argument("level",
                                                                IntegerArgumentType.integer(-32, 128))
                                                        .executes(PlotCommand::resolve)))))));
    }

    /** Palette keys that attach to one block rather than to a whole part. */
    private static final List<String> MARK_KEYS =
            List.of("damaged", "torch", "variant", "loot", "mob", "frompalette");

    // ------------------------------------------------------------------ context

    /** The plot under the caller, reported as a failure when there is none. */
    @Nullable
    private static Layout.Plot plotAt(CommandSourceStack source) {
        BlockPos pos = BlockPos.containing(source.getPosition());
        Layout.Plot plot = Layout.at(Layout.plots(), pos.getX(), pos.getZ());
        if (plot == null) {
            Chat.fail(source, "You are not standing on a plot",
                    pos.getX() + "," + pos.getZ(),
                    "Every plot is chunk aligned with a chunk of walkway around it. "
                            + "/lcdev workshop here says what is under you");
        }
        return plot;
    }

    @Nullable
    private static Catalogue.Row rowOf(@Nullable Layout.Plot plot) {
        return plot == null ? null : plot.row();
    }

    // -------------------------------------------------------------------- mark

    /**
     * {@code /lcdev mark <key> <value>}: attach a palette key to the block you are
     * looking at.
     *
     * <p>Stored against the plot, at a position **relative to the plot's own
     * corner**, so a mark survives the catalogue growing and the plot moving. The
     * export reads these when it builds the palette; nothing consumes them yet.
     */
    public static void registerMark(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("lcdev")
                .then(Commands.literal("mark")
                        .requires(s -> s.hasPermission(2))
                        .then(Commands.argument("key", StringArgumentType.word())
                                .suggests((c, b) -> SharedSuggestionProvider.suggest(
                                        MARK_KEYS, b))
                                .then(Commands.argument("value",
                                                StringArgumentType.greedyString())
                                        .executes(PlotCommand::mark)))));
    }

    private static int mark(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        net.minecraft.server.level.ServerPlayer player;
        try {
            player = source.getPlayerOrException();
        } catch (Exception e) {
            Chat.fail(source, "Marking needs a player, because it marks what you are "
                    + "looking at", null, "Run it in game");
            return 0;
        }
        net.minecraft.world.phys.HitResult hit = player.pick(6.0, 0.0f, false);
        if (!(hit instanceof net.minecraft.world.phys.BlockHitResult block)) {
            Chat.fail(source, "Nothing in reach", null,
                    "Look at the block you want to mark, within six blocks");
            return 0;
        }
        BlockPos pos = block.getBlockPos();
        Layout.Plot plot = Layout.at(Layout.plots(), pos.getX(), pos.getZ());
        if (plot == null) {
            Chat.fail(source, "That block is not on a plot",
                    pos.getX() + "," + pos.getY() + "," + pos.getZ(),
                    "A mark belongs to a plot, so it has to sit on one");
            return 0;
        }

        String key = StringArgumentType.getString(ctx, "key");
        String value = StringArgumentType.getString(ctx, "value").trim();
        if (!MARK_KEYS.contains(key)) {
            Chat.fail(source, "Not a key that attaches to a block", key,
                    "These do: " + String.join(", ", MARK_KEYS));
            return 0;
        }

        JsonObject values;
        try {
            values = SettingsStore.load(source.getServer(), plot.id());
        } catch (IOException e) {
            return unreadable(source, plot, e);
        }
        // Relative to the plot corner and to the first buildable block, so the mark
        // means the same thing wherever the plot ends up.
        String at = (pos.getX() - plot.blockMinX()) + ","
                + (pos.getY() - Boundaries.BASE) + ","
                + (pos.getZ() - plot.blockMinZ());
        child(child(values, "marks"), at).addProperty(key, value);
        try {
            SettingsStore.save(source.getServer(), plot.id(), plot.row(), values);
        } catch (IOException e) {
            Chat.fail(source, "Could not write the settings file", null,
                    String.valueOf(e.getMessage()));
            return 0;
        }
        Chat.header(source, plot.id(), "mark");
        Chat.kv(source, "block", String.valueOf(
                net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(
                        player.level().getBlockState(pos).getBlock())));
        Chat.kv(source, "at", at + "  relative to the plot corner");
        Chat.kv(source, key, value);
        return 1;
    }

    // ---------------------------------------------------------- boundary preview

    private static int show(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        JsonObject values;
        try {
            values = SettingsStore.load(source.getServer(), plot.id());
        } catch (IOException e) {
            return unreadable(source, plot, e);
        }
        List<Boundaries.Line> lines = Boundaries.of(values);
        int placed = Boundaries.show(source.getLevel(), plot, values);

        Chat.header(source, plot.id(), "boundaries");
        for (Boundaries.Line line : lines) {
            Chat.kv(source, "y " + line.y(), line.label());
        }
        Chat.kv(source, "markers placed", String.valueOf(placed));
        Chat.note(source, "Drawn on the walkway, never inside the plot. "
                + "/lcdev plot hide clears them.");
        return 1;
    }

    private static int hide(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        int cleared = Boundaries.hide(source.getLevel(), plot,
                source.getLevel().getMaxBuildHeight() - 1);
        Chat.header(source, plot.id());
        Chat.kv(source, "markers cleared", String.valueOf(cleared));
        return 1;
    }

    // -------------------------------------------------------------- suggestions

    private static java.util.concurrent.CompletableFuture<com.mojang.brigadier.suggestion.Suggestions>
    suggestKeys(CommandContext<CommandSourceStack> ctx,
                com.mojang.brigadier.suggestion.SuggestionsBuilder builder) {
        BlockPos pos = BlockPos.containing(ctx.getSource().getPosition());
        Layout.Plot plot = Layout.at(Layout.plots(), pos.getX(), pos.getZ());
        List<String> names = new ArrayList<>();
        for (Settings.Field f : Settings.fieldsFor(rowOf(plot))) {
            names.add(f.name());
        }
        return SharedSuggestionProvider.suggest(names, builder);
    }

    private static java.util.concurrent.CompletableFuture<com.mojang.brigadier.suggestion.Suggestions>
    suggestValues(CommandContext<CommandSourceStack> ctx,
                  com.mojang.brigadier.suggestion.SuggestionsBuilder builder) {
        BlockPos pos = BlockPos.containing(ctx.getSource().getPosition());
        Layout.Plot plot = Layout.at(Layout.plots(), pos.getX(), pos.getZ());
        Settings.Field field = Settings.field(rowOf(plot),
                StringArgumentType.getString(ctx, "key"));
        return SharedSuggestionProvider.suggest(
                field == null ? List.of() : Settings.suggestions(field), builder);
    }

    // -------------------------------------------------------------------- read

    private static int get(CommandContext<CommandSourceStack> ctx, @Nullable String key) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        JsonObject values;
        try {
            values = SettingsStore.load(source.getServer(), plot.id());
        } catch (IOException e) {
            return unreadable(source, plot, e);
        }

        if (key != null) {
            Settings.Field field = Settings.field(plot.row(), key);
            JsonElement set = values.get(key);
            Chat.header(source, key, plot.id());
            if (field == null) {
                Chat.warn(source, "Not a key this plot has.");
                Chat.note(source, "/lcdev plot keys lists the ones it does.");
            } else {
                Chat.prose(source, field.help());
            }
            Chat.kv(source, "value", set == null ? "unset" : set.toString());
            if (set == null && field != null) {
                Chat.kv(source, "the export will use",
                        field.fallback() == null ? "nothing, and will ask you"
                                : field.fallback());
            }
            return 1;
        }

        Chat.header(source, plot.id(), "settings");
        JsonObject own = Settings.shallow(values);
        if (own.keySet().isEmpty()) {
            Chat.note(source, "Nothing set. /lcdev plot keys lists what this plot "
                    + "accepts.");
        }
        for (String name : own.keySet()) {
            Chat.kv(source, name, own.get(name).toString(),
                    describeField(plot.row(), name));
        }
        if (values.has("chunks")) {
            Chat.kv(source, "chunk overrides",
                    String.valueOf(values.getAsJsonObject("chunks").size()));
        }
        if (values.has("levels")) {
            Chat.kv(source, "level overrides",
                    String.valueOf(values.getAsJsonObject("levels").size()));
        }
        return 1;
    }

    @Nullable
    private static net.minecraft.network.chat.Component describeField(
            @Nullable Catalogue.Row row, String name) {
        Settings.Field f = Settings.field(row, name);
        return f == null ? null : net.minecraft.network.chat.Component.literal(f.help());
    }

    private static int keys(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        List<Settings.Field> fields = Settings.fieldsFor(plot.row());
        Chat.header(source, plot.id(), fields.size() + " keys");
        for (Settings.Field f : fields) {
            Chat.kv(source, f.name(),
                    f.type().name().toLowerCase() + (f.fallback() == null ? ""
                            : ", default " + f.fallback()),
                    net.minecraft.network.chat.Component.literal(f.help()));
        }
        Chat.note(source, "Anything else goes under `raw` and is merged verbatim.");
        return 1;
    }

    private static int file(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        Chat.header(source, plot.id());
        Chat.path(source, "settings",
                SettingsStore.pathOf(source.getServer(), plot.id()).toString());
        Chat.kv(source, "written", SettingsStore.exists(source.getServer(), plot.id())
                ? "yes" : "not yet, nothing has been set");
        return 1;
    }

    private static int resolve(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        int dx = IntegerArgumentType.getInteger(ctx, "dx");
        int dz = IntegerArgumentType.getInteger(ctx, "dz");
        int level = IntegerArgumentType.getInteger(ctx, "level");
        JsonObject values;
        try {
            values = SettingsStore.load(source.getServer(), plot.id());
        } catch (IOException e) {
            return unreadable(source, plot, e);
        }
        JsonObject merged = Settings.resolve(values, dx, dz, level);
        Chat.header(source, plot.id(), "chunk " + dx + "," + dz + " level " + level);
        if (merged.keySet().isEmpty()) {
            Chat.note(source, "Nothing applies here.");
        }
        for (String name : merged.keySet()) {
            Chat.kv(source, name, merged.get(name).toString());
        }
        Chat.note(source, "Most specific wins: plot, then its levels, then the chunk, "
                + "then that chunk's levels.");
        return 1;
    }

    // ------------------------------------------------------------------- write

    private static int set(CommandContext<CommandSourceStack> ctx,
                           @Nullable String chunkKey, @Nullable String levelKey) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        String key = StringArgumentType.getString(ctx, "key");
        String raw = StringArgumentType.getString(ctx, "value");

        Settings.Field field = Settings.field(plot.row(), key);
        if (field == null) {
            Chat.fail(source, "Not a key this plot has", key,
                    "/lcdev plot keys lists them. Anything the schema does not cover "
                            + "goes under `raw`, by editing the file");
            return 0;
        }
        if (chunkKey != null && !withinPlot(plot, chunkKey)) {
            Chat.fail(source, "That chunk is not part of this plot", chunkKey,
                    "The offsets run from 0 to " + (plot.width() - 1) + " by "
                            + (plot.height() - 1));
            return 0;
        }

        JsonElement value;
        try {
            value = Settings.parse(field, raw);
        } catch (IllegalArgumentException e) {
            Chat.fail(source, "That is not a valid value for " + key, raw,
                    "It wants " + e.getMessage());
            return 0;
        }

        JsonObject values;
        try {
            values = SettingsStore.load(source.getServer(), plot.id());
        } catch (IOException e) {
            return unreadable(source, plot, e);
        }

        JsonObject target = values;
        String where = "the plot";
        if (chunkKey != null) {
            target = child(child(values, "chunks"), chunkKey);
            where = "chunk " + chunkKey;
        } else if (levelKey != null) {
            target = child(child(values, "levels"), levelKey);
            where = "level " + levelKey;
        }
        target.add(key, value);

        try {
            SettingsStore.save(source.getServer(), plot.id(), plot.row(), values);
        } catch (IOException e) {
            Chat.fail(source, "Could not write the settings file",
                    SettingsStore.pathOf(source.getServer(), plot.id()).toString(),
                    String.valueOf(e.getMessage()));
            return 0;
        }
        Chat.header(source, plot.id(), where);
        Chat.kv(source, key, value.toString());
        return 1;
    }

    private static int clear(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        Layout.Plot plot = plotAt(source);
        if (plot == null) {
            return 0;
        }
        String key = StringArgumentType.getString(ctx, "key");
        JsonObject values;
        try {
            values = SettingsStore.load(source.getServer(), plot.id());
        } catch (IOException e) {
            return unreadable(source, plot, e);
        }
        if (!values.has(key)) {
            Chat.header(source, plot.id());
            Chat.note(source, key + " was not set at plot scope. Nothing changed.");
            return 0;
        }
        values.remove(key);
        try {
            // An empty file is worse than none: it looks like a decision.
            if (values.keySet().isEmpty()) {
                SettingsStore.delete(source.getServer(), plot.id());
            } else {
                SettingsStore.save(source.getServer(), plot.id(), plot.row(), values);
            }
        } catch (IOException e) {
            Chat.fail(source, "Could not write the settings file", null,
                    String.valueOf(e.getMessage()));
            return 0;
        }
        Chat.header(source, plot.id());
        Chat.kv(source, key, "cleared");
        return 1;
    }

    // ---------------------------------------------------------------- internals

    private static boolean withinPlot(Layout.Plot plot, String chunkKey) {
        String[] parts = chunkKey.split(",");
        try {
            int dx = Integer.parseInt(parts[0]);
            int dz = Integer.parseInt(parts[1]);
            return dx >= 0 && dx < plot.width() && dz >= 0 && dz < plot.height();
        } catch (RuntimeException e) {
            return false;
        }
    }

    private static JsonObject child(JsonObject parent, String key) {
        if (!parent.has(key) || !parent.get(key).isJsonObject()) {
            parent.add(key, new JsonObject());
        }
        return parent.getAsJsonObject(key);
    }

    private static int unreadable(CommandSourceStack source, Layout.Plot plot,
                                  IOException e) {
        Chat.fail(source, "The settings file could not be read",
                SettingsStore.pathOf(source.getServer(), plot.id()).toString(),
                String.valueOf(e.getMessage()));
        return 0;
    }
}
