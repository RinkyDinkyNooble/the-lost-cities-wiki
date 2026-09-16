package com.rinkynooble.lostcitiesdevtool.workshop;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.LevelResource;

import javax.annotation.Nullable;
import java.io.IOException;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * The workshop dimension: entering it, laying the catalogue out in it, and knowing
 * afterwards which plot is which.
 *
 * <p>A dimension of its own rather than a corner of the player's world. The
 * catalogue is large, it wants a fixed floor at the bottom of the world, and nothing
 * about it should be able to disturb a world somebody is playing. Lost Cities ships
 * its own dimension for its own reasons, so the shape is familiar.
 *
 * <p>Flat, one layer of bedrock at y {@value Layout#FLOOR_Y}, plains, no structures
 * and no mob spawning. The bedrock is the floor: build above it, and there is
 * nothing below it to dig into.
 */
public final class Workshop {

    public static final ResourceKey<Level> DIMENSION = ResourceKey.create(
            Registries.DIMENSION, new ResourceLocation("lostcitiesdevtool:workshop"));

    /** The registry lives with the world, because a plot belongs to a world. */
    private static final String DIR = "lostcitiesdevtool";
    private static final String FILE = "plots.json";

    private Workshop() {
    }

    @Nullable
    public static ServerLevel level(MinecraftServer server) {
        return server.getLevel(DIMENSION);
    }

    // ------------------------------------------------------------------ building

    /** What one build did, so the caller can report it without counting again. */
    public record Built(int plots, int chunks, long blocks) {
    }

    /**
     * Lay the floors out.
     *
     * <p>Only the floor. A plot's marker says where a thing goes and how big it is;
     * what goes on it is the author's business, and later phases fill it from a pack.
     * Re-running is safe and idempotent: the same catalogue produces the same plots
     * in the same colours, so this repaints rather than duplicating.
     */
    /**
     * The floor colours, in the order {@link Layout} assigns them.
     *
     * <p>Here rather than in {@code Layout} because this is what paints. Keeping
     * Minecraft's types out of the layout is what lets the geometry be exercised
     * without booting a server.
     */
    private static final Block[] COLOURS = {
            Blocks.WHITE_GLAZED_TERRACOTTA, Blocks.ORANGE_GLAZED_TERRACOTTA,
            Blocks.MAGENTA_GLAZED_TERRACOTTA, Blocks.LIGHT_BLUE_GLAZED_TERRACOTTA,
            Blocks.YELLOW_GLAZED_TERRACOTTA, Blocks.LIME_GLAZED_TERRACOTTA,
            Blocks.PINK_GLAZED_TERRACOTTA, Blocks.GRAY_GLAZED_TERRACOTTA,
            Blocks.LIGHT_GRAY_GLAZED_TERRACOTTA, Blocks.CYAN_GLAZED_TERRACOTTA,
            Blocks.PURPLE_GLAZED_TERRACOTTA, Blocks.BLUE_GLAZED_TERRACOTTA,
            Blocks.BROWN_GLAZED_TERRACOTTA, Blocks.GREEN_GLAZED_TERRACOTTA,
            Blocks.RED_GLAZED_TERRACOTTA, Blocks.BLACK_GLAZED_TERRACOTTA,
    };

    static {
        // Layout hands out colour indices and this holds the blocks they mean, so
        // the two counts have to agree and nothing else would notice if they did
        // not. One short and two touching plots quietly paint the same colour; one
        // long and the extra is never reachable, which puts the adjacency search
        // back to reusing a colour a neighbour already has.
        if (COLOURS.length != Layout.COLOUR_COUNT) {
            throw new IllegalStateException("Workshop has " + COLOURS.length
                    + " floor colours and Layout hands out " + Layout.COLOUR_COUNT);
        }
    }

    /** What a plot's floor is made of. The front desk is not one of the shapes. */
    public static Block floorOf(Layout.Plot plot) {
        int colour = plot.floorColour();
        return colour < 0 ? Blocks.CHISELED_STONE_BRICKS
                : COLOURS[Math.floorMod(colour, COLOURS.length)];
    }

    public static Built build(ServerLevel level) {
        List<Layout.Plot> plots = Layout.plots();
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        int chunks = 0;
        long blocks = 0;

        for (Layout.Plot plot : plots) {
            BlockState floor = floorOf(plot).defaultBlockState();
            for (int x = plot.blockMinX(); x <= plot.blockMaxX(); x++) {
                for (int z = plot.blockMinZ(); z <= plot.blockMaxZ(); z++) {
                    pos.set(x, Layout.FLOOR_Y, z);
                    // Flag 2: send to clients, do not trigger neighbour updates. The
                    // floor is inert and there are tens of thousands of them.
                    level.setBlock(pos, floor, 2);
                    blocks++;
                }
            }
            chunks += plot.width() * plot.height();
        }
        save(level.getServer(), plots);
        return new Built(plots.size(), chunks, blocks);
    }

    // ------------------------------------------------------------------ registry

    /**
     * Write the plot registry beside the world.
     *
     * <p>A file rather than {@code SavedData}, for the same reason the settings will
     * be files: it can be read, diffed and fixed without the game running. Nothing
     * reads it back yet, because the layout is computed from the catalogue and is
     * the same every time; it exists so a person, or a later phase, can see what the
     * build decided.
     */
    public static void save(MinecraftServer server, List<Layout.Plot> plots) {
        JsonObject root = new JsonObject();
        root.addProperty("_about", "Written by /lcdev workshop build. The layout is "
                + "computed from the catalogue, so this is a record of what was "
                + "built rather than the source of it.");
        // Two versions, because they are two facts and conflating them put a
        // Lost Cities version on screen that was not the one running.
        root.addProperty("version", Catalogue.version());
        root.addProperty("catalogueForLostCities", Catalogue.version());
        if (Versions.running() != null) {
            root.addProperty("runningLostCities", Versions.running());
        }
        root.addProperty("floorY", Layout.FLOOR_Y);

        JsonArray array = new JsonArray();
        for (Layout.Plot p : plots) {
            JsonObject o = new JsonObject();
            o.addProperty("id", p.id());
            o.addProperty("chunkX", p.cx());
            o.addProperty("chunkZ", p.cz());
            o.addProperty("width", p.width());
            o.addProperty("height", p.height());
            o.addProperty("floor", String.valueOf(
                    net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(
                            floorOf(p))));
            if (p.row() != null) {
                o.addProperty("row", p.row().id());
                o.addProperty("family", p.row().family());
                o.addProperty("key", p.row().key());
                o.addProperty("class", p.row().kind().name().toLowerCase());
                o.addProperty("owner", p.row().owner());
                if (p.row().dead() != null) {
                    o.addProperty("dead", p.row().dead());
                }
            }
            array.add(o);
        }
        root.add("plots", array);

        // The sizes an import grew, so the next build lays the same catalogue out.
        JsonObject grown = new JsonObject();
        Layout.grown().forEach(grown::addProperty);
        root.add("grownRows", grown);

        // The footprints an import had to make room for, in the order it made room.
        // A list rather than an object because the order is the load-bearing part:
        // these rows are appended to the catalogue, and reordering them moves every
        // band after the one that moved.
        com.google.gson.JsonArray extra = new com.google.gson.JsonArray();
        Catalogue.extraMultis().forEach(extra::add);
        root.add("extraRows", extra);

        Path dir = server.getWorldPath(LevelResource.ROOT).resolve(DIR);
        try {
            Files.createDirectories(dir);
            try (Writer w = Files.newBufferedWriter(dir.resolve(FILE),
                    StandardCharsets.UTF_8)) {
                new GsonBuilder().setPrettyPrinting().create().toJson(root, w);
            }
        } catch (IOException e) {
            // The world is already built. Failing to write the record is worth
            // saying, not worth undoing the build over.
            LostCitiesDevTool.LOGGER.error("could not write the plot registry: {}",
                    e.toString());
        }
    }

    /** Absolute and normalised, because it is printed for someone to click and copy. */
    /**
     * Read back the row sizes a previous import grew.
     *
     * <p>Called before anything asks the layout where a plot is. Without it a build
     * after a restart would lay the catalogue out at its default sizes and orphan
     * every plot an import added.
     */
    public static void loadGrownRows(MinecraftServer server) {
        // Cleared first, on every path. The sizes are held statically and a single
        // player session starts a fresh server per world, so a world opened after
        // one with grown rows would otherwise inherit them and lay out plots its
        // own registry has never heard of.
        Layout.setGrown(java.util.Map.of());
        Catalogue.setExtraMultis(java.util.List.of());
        Path path = registryPath(server);
        if (!Files.isRegularFile(path)) {
            return;
        }
        try {
            JsonObject root = com.google.gson.JsonParser.parseString(
                    Files.readString(path, StandardCharsets.UTF_8)).getAsJsonObject();
            // Before the sizes, because a grown row may be one of these: a row that
            // does not exist yet cannot be grown, and the count would be dropped.
            if (root.has("extraRows") && root.get("extraRows").isJsonArray()) {
                java.util.List<String> extra = new java.util.ArrayList<>();
                for (com.google.gson.JsonElement e
                        : root.getAsJsonArray("extraRows")) {
                    extra.add(e.getAsString());
                }
                Catalogue.setExtraMultis(extra);
            }
            if (!root.has("grownRows")) {
                return;
            }
            java.util.Map<String, Integer> sizes = new java.util.HashMap<>();
            JsonObject grown = root.getAsJsonObject("grownRows");
            for (String key : grown.keySet()) {
                sizes.put(key, grown.get(key).getAsInt());
            }
            Layout.setGrown(sizes);
        } catch (Exception e) {
            LostCitiesDevTool.LOGGER.warn("could not read the grown rows: {}",
                    e.toString());
        }
    }

    public static Path registryPath(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve(DIR).resolve(FILE)
                .toAbsolutePath().normalize();
    }
}
