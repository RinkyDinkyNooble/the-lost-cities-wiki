package com.rinkynooble.lostcitiesdevtool.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import com.rinkynooble.lostcitiesdevtool.workshop.Catalogue;
import com.rinkynooble.lostcitiesdevtool.workshop.Layout;
import com.rinkynooble.lostcitiesdevtool.workshop.Sync;
import com.rinkynooble.lostcitiesdevtool.workshop.Versions;
import com.rinkynooble.lostcitiesdevtool.workshop.Wipe;
import com.rinkynooble.lostcitiesdevtool.workshop.Workshop;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.ResourceLocationArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;

import java.io.IOException;
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
                        .requires(s -> s.hasPermission(2))
                        .then(Commands.literal("go")
                                // Level 2 because it moves a player between
                                // dimensions. On any server that is not a creative
                                // build server, a teleport nobody is opped for is an
                                // escape from whatever they were standing next to.
                                .requires(s -> s.hasPermission(2))
                                .executes(WorkshopCommand::go))
                        .then(Commands.literal("leave")
                                .requires(s -> s.hasPermission(2))
                                .executes(WorkshopCommand::leave))
                        .then(Commands.literal("build")
                                .requires(s -> s.hasPermission(2))
                                .executes(WorkshopCommand::build))
                        .then(Commands.literal("rows")
                                .executes(WorkshopCommand::rows))
                        .then(Commands.literal("here")
                                .executes(WorkshopCommand::here))
                        .then(Commands.literal("sync")
                                .executes(WorkshopCommand::sync))
                        .then(Commands.literal("clear")
                                .executes(ctx -> clear(ctx, false, false))
                                .then(Commands.literal("confirm")
                                        .executes(ctx -> clear(ctx, true, false))
                                        .then(Commands.literal("anyway")
                                                .executes(ctx -> clear(ctx, true, true)))))
                        .then(Commands.literal("grow")
                                .requires(s -> s.hasPermission(2))
                                .then(Commands.argument("row",
                                                ResourceLocationArgument.id())
                                        .suggests((c, b) -> SharedSuggestionProvider
                                                .suggest(Catalogue.rows().stream()
                                                        .map(Catalogue.Row::id)
                                                        .toList(), b))
                                        .then(Commands.argument("plots",
                                                        IntegerArgumentType.integer(1, Layout.MAX_PLOTS_IN_ROW))
                                                .executes(WorkshopCommand::grow))))));
    }

    // ------------------------------------------------------------------- clear

    /**
     * Empty every plot, once somebody has said so twice.
     *
     * <p>An import leaves alone the plots its pack does not need, so importing a
     * second city on top of a first keeps the first one's plots and an export then
     * writes both into one pack. This is how you start again.
     *
     * <p>Bare, it reports and changes nothing. Confirmed, it writes a backup pack
     * first and stops if that backup cannot be written, because the alternative is
     * destroying work with nothing to restore from. {@code anyway} is the way past
     * that, and it is two words deep for a reason.
     */
    private static int clear(CommandContext<CommandSourceStack> ctx,
                             boolean confirmed, boolean skipBackup) {
        CommandSourceStack source = ctx.getSource();
        ServerLevel workshop = CommandSupport.workshop(source);
        if (workshop == null) {
            return 0;
        }

        Wipe.Survey survey;
        try {
            survey = Wipe.survey(source.getServer(), workshop);
        } catch (IOException e) {
            Chat.fail(source, "The plots could not be read", null, e.getMessage());
            return 0;
        }

        if (survey.isEmpty()) {
            Chat.header(source, "Workshop", "already empty");
            Chat.note(source, "No plot holds settings or blocks, so there is "
                    + "nothing to clear.");
            return 1;
        }

        if (!confirmed) {
            Chat.header(source, "This would empty the workshop");
            Chat.kv(source, "plots", String.valueOf(survey.plots()));
            Chat.kv(source, "blocks", String.valueOf(survey.blocks()));
            Chat.prose(source, "A backup pack is written first, so nothing is lost "
                    + "that an import could not put back.");
            Chat.note(source, "The pack's own settings and the palette ledger are "
                    + "kept. Rows an import grew go back to their catalogue size.");
            Chat.note(source, "Run /lcdev workshop clear confirm to go ahead.");
            return 1;
        }

        String saved = null;
        if (!skipBackup) {
            try {
                saved = String.valueOf(Wipe.backup(source.getServer(), workshop));
            } catch (IOException e) {
                Chat.fail(source, "Nothing was cleared", "the backup failed",
                        e.getMessage());
                Chat.note(source, "Every block is still where it was. Fix what the "
                        + "export objected to, or run /lcdev workshop clear confirm "
                        + "anyway to clear without a backup.");
                return 0;
            }
        }

        int emptied;
        try {
            emptied = Wipe.run(source.getServer(), workshop);
        } catch (IOException e) {
            Chat.fail(source, "The workshop could not be cleared", null,
                    e.getMessage());
            return 0;
        }

        Chat.header(source, "Cleared", emptied + (emptied == 1 ? " plot" : " plots"));
        if (saved != null) {
            Chat.path(source, "backup", saved);
            Chat.note(source, "/lcdev import puts it back, once it is installed as a "
                    + "datapack.");
        } else {
            Chat.warn(source, "No backup was taken. That was the `anyway`.");
        }
        return 1;
    }

    // -------------------------------------------------------------------- sync

    /**
     * Make the catalogue agree with the settings files on disk.
     *
     * <p>Values need no syncing: every command reads the file when it is asked, so
     * a number changed in an editor is already in effect. What this is for is a
     * file describing a plot the catalogue does not lay out, which nothing else
     * looks for and which an export therefore writes a pack without.
     */
    private static int sync(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        ServerLevel workshop = CommandSupport.workshop(source);
        if (workshop == null) {
            return 0;
        }
        Sync.Report report;
        try {
            report = Sync.run(source.getServer(), workshop);
        } catch (IOException e) {
            Chat.fail(source, "The settings files could not be read", null,
                    String.valueOf(e.getMessage()));
            return 0;
        }

        Chat.header(source, "Synced", report.files()
                + (report.files() == 1 ? " file" : " files"));
        Chat.kv(source, "plots the catalogue already had",
                String.valueOf(report.plots()));
        for (Map.Entry<String, Integer> e : report.grown().entrySet()) {
            Chat.kv(source, "grew " + e.getKey(), e.getValue() + " plots");
        }
        for (Sync.Note note : report.notes()) {
            Chat.warn(source, note.plotId() + " " + note.what());
        }
        if (report.quiet()) {
            Chat.note(source, "Nothing needed changing. Values are read from the "
                    + "file every time, so an edit is in effect without this.");
        }
        return 1;
    }

    // -------------------------------------------------------------------- grow

    /**
     * Say no to a row that would paint an unreasonable amount of floor.
     *
     * <p>{@code MAX_PLOTS_IN_ROW} bounds the count and says nothing about the size
     * of each, which was enough while nothing exceeded 10 by 10. A 64 by 64 row at
     * the count limit is two million chunks, laid out and painted on the server
     * thread before the command answers.
     *
     * @return true when it refused, and it has already said so
     */
    private static boolean refuseArea(CommandSourceStack source, int width,
                                      int height, int want) {
        int allowed = Layout.plotsAllowed(width, height);
        if (want <= allowed) {
            return false;
        }
        Chat.fail(source, want + " plots of " + width + "x" + height + " is "
                        + ((long) want * width * height) + " chunks of floor",
                "the limit is " + Layout.MAX_CHUNKS_IN_ROW + " chunks a row",
                "At this footprint that is " + allowed
                        + (allowed == 1 ? " plot" : " plots"));
        return true;
    }

    /**
     * Lay out more plots in one row, or lay out a row that has none.
     *
     * <p>A row's number in the catalogue is where it starts, not what it holds. Every
     * multi-building footprint up to the <b>default</b> area size of 10 exists as a
     * row, and the large ones are declared with no plots because painting them all
     * would be thousands of chunks of floor for shapes most packs never use.
     *
     * <p>Past that default there is no row until somebody asks for one, by importing
     * a pack that holds the footprint or by naming it here. Naming it here is the
     * only way to build one by hand, which is what this exists for.
     *
     * <p>Rows only ever get longer. Shrinking one would move every plot after it and
     * orphan whatever was built there.
     */
    private static int grow(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        // A row id has a slash in it, which a quotable string argument will not
        // take unquoted. A resource location will: every row id is a legal path.
        String id = ResourceLocationArgument.getId(ctx, "row").getPath();
        int want = IntegerArgumentType.getInteger(ctx, "plots");
        boolean added = false;
        Catalogue.Row row = Catalogue.row(id);
        if (row == null) {
            // A multi-building footprint the generated catalogue does not have is
            // made rather than refused. The catalogue stops at the default
            // `multisettings.areasize` of 10, not at what a pack may declare, and
            // somebody widening the area and building a 11x11 by hand should not
            // have to import a pack that already contains one to get a plot for it.
            //
            // Measured before it is made, not after. A row registered and then
            // refused for its area would leave a band behind for a command that
            // answered no, and bands are never taken back.
            int[] size = Catalogue.multiSize(id);
            if (size != null && !refuseArea(source, size[0], size[1], want)) {
                String made = Catalogue.registerMulti(id);
                row = made == null ? null : Catalogue.row(made);
                added = row != null;
            } else if (size != null) {
                return 0;
            }
        }
        if (row == null) {
            Chat.fail(source, "No row named " + id, "catalogue.json",
                    "/lcdev workshop rows lists every one. A multibuilding/<w>x<h> "
                            + "up to " + Catalogue.MAX_MULTI + " is made on demand");
            return 0;
        }
        if (row.kind() == Catalogue.Kind.SINGLE) {
            Chat.fail(source, row.id() + " holds one plot and cannot grow",
                    row.family() + " " + row.key(),
                    "Its codec takes a single name. A list there is not a longer row: "
                            + "Lost Cities drops it and uses its default part");
            return 0;
        }
        // Only for a row that already existed. One that was just added was measured
        // before it was made, and asking twice would leave a reader unsure which of
        // the two is the one that fires.
        if (!added && refuseArea(source, row.width(), row.height(), want)) {
            return 0;
        }

        ServerLevel workshop = CommandSupport.workshop(source);
        if (workshop == null) {
            return 0;
        }

        int before = Layout.plotsIn(row);
        Layout.grow(row.id(), want);
        int after = Layout.plotsIn(row);
        Workshop.Built built = Workshop.build(workshop);

        Chat.header(source, "Grown", row.id());
        if (added) {
            Chat.kv(source, "row", "added, " + row.width() + "x" + row.height()
                    + " chunks");
            Chat.note(source, "The catalogue had no row this size. It was appended "
                    + "after the others, so nothing already laid out moved, and it "
                    + "is saved with the world. A footprint wider than the world "
                    + "style's multisettings.areasize throws during generation, so "
                    + "raise that to at least "
                    + Math.max(row.width(), row.height()) + " in the pack that "
                    + "uses it.");
        }
        Chat.kv(source, "plots", before + " to " + after);
        if (after == before) {
            Chat.note(source, "Already at least that long. Rows only get longer, "
                    + "because shrinking one would move every plot after it.");
        }
        Chat.kv(source, "catalogue", built.plots() + " plots, "
                + built.chunks() + " chunks");
        return 1;
    }

    // ---------------------------------------------------------------------- go

    private static int go(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        ServerLevel workshop = CommandSupport.workshop(source);
        if (workshop == null) {
            return 0;
        }
        ServerPlayer player = CommandSupport.player(source,
                "Only a player can be sent to the workshop");
        if (player == null) {
            return 0;
        }
        // Only from outside. Running `go` while already in the workshop would
        // otherwise overwrite the way out with a workshop position, and the player
        // who ran it twice could not get back to where they started.
        if (!player.level().dimension().equals(Workshop.DIMENSION)) {
            remember(player);
        }
        // Above the floor, over the front desk at the origin.
        player.teleportTo(workshop, 8.5, Layout.FLOOR_Y + 1.0, 8.5,
                player.getYRot(), player.getXRot());
        Chat.header(source, "Workshop", "catalogue for Lost Cities "
                + Versions.catalogue());
        if (Versions.mismatch() != null) {
            Chat.warn(source, Versions.mismatch());
        }
        Chat.note(source, "The front desk is the plot you are standing on. "
                + "Buildings are east, infrastructure is west.");
        Chat.note(source, "`/lcdev workshop leave` puts you back where you ran this.");
        return 1;
    }

    // ------------------------------------------------------------------- leave

    /**
     * Where {@code go} was run from, kept on the player.
     *
     * <p>Forge's persistent data is written into the player's own NBT, so this
     * survives a logout. It is deliberately not the vanilla respawn point: that is a
     * bed which may have been broken since, and teleporting into where a bed used to
     * be is a way to suffocate somebody. The fallback is the world spawn, which is
     * the one position a server always has.
     */
    private static final String RETURN = "lostcitiesdevtool:return";

    private static void remember(ServerPlayer player) {
        CompoundTag spot = new CompoundTag();
        spot.putString("dimension", player.level().dimension().location().toString());
        spot.putDouble("x", player.getX());
        spot.putDouble("y", player.getY());
        spot.putDouble("z", player.getZ());
        spot.putFloat("yaw", player.getYRot());
        spot.putFloat("pitch", player.getXRot());
        player.getPersistentData().put(RETURN, spot);
    }

    /**
     * The level {@code spot} names, or null when it names nothing usable.
     *
     * <p>Null covers a dimension that has since been removed from the pack, and a
     * stored position that somehow points back at the workshop. Sending somebody
     * from the workshop to the workshop is not leaving.
     */
    private static ServerLevel storedLevel(MinecraftServer server, CompoundTag spot) {
        if (!spot.contains("dimension")) {
            return null;
        }
        ResourceLocation id = ResourceLocation.tryParse(spot.getString("dimension"));
        if (id == null) {
            return null;
        }
        ResourceKey<Level> key = ResourceKey.create(Registries.DIMENSION, id);
        if (key.equals(Workshop.DIMENSION)) {
            return null;
        }
        return server.getLevel(key);
    }

    private static int leave(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        ServerPlayer player = CommandSupport.player(source,
                "Only a player can be sent out of the workshop");
        if (player == null) {
            return 0;
        }
        if (!player.level().dimension().equals(Workshop.DIMENSION)) {
            Chat.fail(source, "You are not in the workshop",
                    player.level().dimension().location().toString(),
                    "There is nothing to leave. `/lcdev workshop go` is the way in");
            return 0;
        }

        MinecraftServer server = source.getServer();
        CompoundTag spot = player.getPersistentData().getCompound(RETURN);
        ServerLevel target = storedLevel(server, spot);
        double x;
        double y;
        double z;
        float yaw;
        float pitch;
        String how;
        if (target != null) {
            x = spot.getDouble("x");
            y = spot.getDouble("y");
            z = spot.getDouble("z");
            yaw = spot.getFloat("yaw");
            pitch = spot.getFloat("pitch");
            how = "where you ran `workshop go`";
        } else {
            target = server.overworld();
            BlockPos spawn = target.getSharedSpawnPos();
            x = spawn.getX() + 0.5;
            y = spawn.getY();
            z = spawn.getZ() + 0.5;
            yaw = player.getYRot();
            pitch = player.getXRot();
            // Three ways to end up here, and they are not the same thing to be told.
            // A stored dimension that is the workshop cannot come from `go`, which
            // only records from outside, so it means the tag was written by
            // something else.
            how = spot.isEmpty()
                    ? "world spawn, because nothing recorded how you got in"
                    : spot.contains("dimension")
                            ? "world spawn, because " + spot.getString("dimension")
                                    + " is not a dimension you can be sent to"
                            : "world spawn, because what was recorded is incomplete";
        }

        player.teleportTo(target, x, y, z, yaw, pitch);
        // Cleared whichever way it went. A return point that outlives the trip it
        // was written for sends the next `leave` somewhere the player has not been
        // for a week.
        player.getPersistentData().remove(RETURN);

        BlockPos to = BlockPos.containing(x, y, z);
        String dimension = target.dimension().location().toString();
        Chat.header(source, "Left the workshop");
        Chat.position(source, "sent to",
                dimension + "  " + to.getX() + " " + to.getY() + " " + to.getZ(),
                dimension, to.getX(), to.getY(), to.getZ());
        Chat.note(source, "Back to " + how + ".");
        return 1;
    }

    // ------------------------------------------------------------------- build

    private static int build(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        ServerLevel workshop = CommandSupport.workshop(source);
        if (workshop == null) {
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

        Chat.header(source, "Workshop built", "catalogue for Lost Cities "
                + Versions.catalogue());
        if (Versions.mismatch() != null) {
            Chat.warn(source, Versions.mismatch());
        }
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

    private static int rows(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        List<Catalogue.Row> all = Catalogue.rows();
        if (all.isEmpty()) {
            Chat.fail(source, "The catalogue is empty", "catalogue.json", null);
            return 0;
        }

        Chat.header(source, "Catalogue", "for Lost Cities "
                + Versions.catalogue());
        if (Versions.mismatch() != null) {
            Chat.warn(source, Versions.mismatch());
        }

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

        // Every row that is laid out, as somewhere to click. Walking a catalogue
        // this size to find the fountains is a chore, and the coordinates are
        // arithmetic nobody should be doing by hand.
        Map<String, Layout.Plot> first = new LinkedHashMap<>();
        for (Layout.Plot plot : Layout.plots()) {
            if (plot.row() != null) {
                first.putIfAbsent(plot.row().id(), plot);
            }
        }
        String dimension = String.valueOf(Workshop.DIMENSION.location());
        String family = null;
        for (Catalogue.Row r : all) {
            Layout.Plot plot = first.get(r.id());
            if (plot == null) {
                continue;
            }
            if (!r.family().equals(family)) {
                family = r.family();
                Chat.prose(source, family);
            }
            Chat.position(source, "  " + r.id(),
                    Layout.plotsIn(r) + (Layout.plotsIn(r) == 1 ? " plot" : " plots"),
                    dimension, plot.blockMinX() + 8, Layout.FLOOR_Y + 1,
                    plot.blockMinZ() + 8);
        }
        int empty = (int) all.stream().filter(r -> Layout.plotsIn(r) == 0).count();
        if (empty > 0) {
            Chat.note(source, empty + " more rows are declared and not laid out, "
                    + "mostly the larger multibuilding footprints. "
                    + "/lcdev workshop grow <row> <plots> lays one out.");
        }
        return 1;
    }

    // -------------------------------------------------------------------- here

    private static int here(CommandContext<CommandSourceStack> ctx) {
        CommandSourceStack source = ctx.getSource();
        if (!CommandSupport.inWorkshop(source)) {
            CommandSupport.notInWorkshop(source);
            return 0;
        }
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
        // Of the plots laid out, not of the catalogue's starting count: a grown row
        // said "5 of 3", and a row registered for a footprint said "1 of 0".
        Chat.kv(source, "variation", (plot.index() + 1) + " of " + Layout.plotsIn(row));
        switch (row.kind()) {
            case SINGLE -> Chat.kv(source, "variations allowed", "one, and only one. "
                    + "The codec takes a string, and a list is dropped for the default");
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
