package com.rinkynooble.lostcitiesdevtool.command;

import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.suggestion.Suggestions;
import com.mojang.brigadier.suggestion.SuggestionsBuilder;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.ResourceLocationArgument;
import net.minecraft.resources.ResourceLocation;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import mcjty.lostcities.setup.Registration;
import mcjty.lostcities.varia.ChunkCoord;
import mcjty.lostcities.worldgen.IDimensionInfo;
import mcjty.lostcities.worldgen.lost.BuildingInfo;
import mcjty.lostcities.worldgen.lost.cityassets.BuildingPart;
import mcjty.lostcities.worldgen.lost.cityassets.CompiledPalette;
import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Set;

/**
 * {@code /lcdev report}, {@code /lcdev char <character>} and
 * {@code /lcdev block <block id>}.
 *
 * <p>Three separate subcommands rather than optional arguments on one. A
 * {@code greedyString} argument sitting beside a literal swallows it, so
 * {@code report block minecraft:gold_block} was read as a request for the character
 * {@code b}.
 *
 * <p>Answers what the generator decided for the chunk the caller is standing in, and
 * what a palette character resolves to there.
 *
 * <p>The mod ships {@code /lostcities debug}, which covers some of the same ground
 * and writes only to the server console, so on a dedicated server the person asking
 * cannot read the answer. This writes to the caller. It also reports the part chosen
 * for each level and the merged palette, neither of which the mod exposes.
 */
public class ReportCommand {

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("lcdev")
                .then(Commands.literal("report")
                        .executes(ctx -> report(ctx, null)))
                .then(Commands.literal("char")
                        .then(Commands.argument("character", StringArgumentType.greedyString())
                                .executes(ctx -> report(ctx,
                                        StringArgumentType.getString(ctx, "character")))))
                .then(Commands.literal("block")
                        .then(Commands.argument("id", StringArgumentType.greedyString())
                                .executes(ctx -> whichCharacters(ctx,
                                        StringArgumentType.getString(ctx, "id")))))
                // The asset comes before the character, not after, so the greedy
                // argument is the last node of every branch. A greedy argument with
                // anything after it swallows what follows, which is how 'report block
                // minecraft:gold_block' once became a request for the character 'b'.
                .then(Commands.literal("in")
                        .then(Commands.argument("asset", ResourceLocationArgument.id())
                                .suggests(ReportCommand::suggestAssets)
                                .then(Commands.literal("char")
                                        .then(Commands.argument("character",
                                                StringArgumentType.greedyString())
                                                .executes(ctx -> charInAsset(ctx,
                                                        StringArgumentType.getString(
                                                                ctx, "character")))))
                                .then(Commands.literal("block")
                                        .then(Commands.argument("id",
                                                StringArgumentType.greedyString())
                                                .executes(ctx -> blockInAsset(ctx,
                                                        StringArgumentType.getString(
                                                                ctx, "id"))))))));
    }

    private static CompletableFuture<Suggestions> suggestAssets(
            CommandContext<CommandSourceStack> ctx, SuggestionsBuilder builder) {
        return SharedSuggestionProvider.suggest(
                PaletteLookup.ids(ctx.getSource().getLevel()), builder);
    }

    private static int report(CommandContext<CommandSourceStack> ctx, String character) {
        CommandSourceStack source = ctx.getSource();
        ServerLevel level = source.getLevel();
        ChunkPos pos = new ChunkPos(net.minecraft.core.BlockPos.containing(source.getPosition()));

        IDimensionInfo provider = Registration.LOSTCITY_FEATURE.get()
                .getDimensionInfo((WorldGenLevel) level);
        if (provider == null) {
            source.sendFailure(Component.literal(
                    "No Lost Cities profile is attached to " + level.dimension().location()
                            + ". Check dimensionsWithProfiles under [profiles] in "
                            + "config/lostcities/common.toml"));
            return 0;
        }

        head(source, "chunk " + pos.x + "," + pos.z
                + "   block " + (pos.x * 16) + "," + (pos.z * 16));
        line(source, "profile", provider.getProfile().getName());
        // The description is the only field an author controls that survives
        // into the running world, which makes it the way to tell two profile
        // files of the same name apart when one is shadowing the other.
        String description = provider.getProfile().getDescription();
        if (description != null && !description.isEmpty()) {
            line(source, "profile description", description);
        }
        line(source, "world style", provider.getWorldStyle().getName());

        BuildingInfo info;
        try {
            info = BuildingInfo.getBuildingInfo(
                    new ChunkCoord(provider.getType(), pos.x, pos.z), provider);
        } catch (Exception e) {
            // The same fault a chunk would hit. Saying so is the answer to the question.
            source.sendFailure(Component.literal(
                    "This chunk cannot be described: " + e.getClass().getSimpleName()
                            + ": " + e.getMessage()));
            source.sendFailure(Component.literal(
                    "That is a fault in the chunk's selection stage, so it also fails "
                            + "every chunk that queries this one."));
            return 0;
        }

        line(source, "is city", String.valueOf(info.isCity));
        line(source, "city level", String.valueOf(info.cityLevel));
        line(source, "ground level", String.valueOf(info.groundLevel));
        if (info.getCityStyle() != null) {
            line(source, "city style", info.getCityStyle().getName());
        }

        describeInfrastructure(source, info);

        if (!info.hasBuilding) {
            line(source, "building", "none, this is a street or open chunk");
            line(source, "street type", String.valueOf(info.streetType));
            describeCharacter(source, info, character);
            return 1;
        }

        line(source, "building", String.valueOf(info.getBuilding().getId()));
        line(source, "floors", info.getNumFloors() + ", cellars " + info.getNumCellars()
                + "   levels " + (-info.getNumCellars()) + " to " + info.getNumFloors()
                + " inclusive");
        if (info.ruinHeight >= 0) {
            line(source, "ruined from", String.valueOf(info.ruinHeight));
        }

        // The part chosen per level is the piece no existing command reports, and it
        // is what a coverage question actually needs answering.
        for (int levelIndex = -info.getNumCellars();
             levelIndex <= info.getNumFloors(); levelIndex++) {
            BuildingPart part = info.getFloor(levelIndex);
            BuildingPart overlay = info.getFloorPart2(levelIndex);
            String text = part == null ? "NOTHING MATCHED" : String.valueOf(part.getId());
            if (overlay != null) {
                text = text + "  +  " + overlay.getId() + " (parts2)";
            }
            line(source, "level " + levelIndex, text);
        }

        describeCharacter(source, info, character);
        return 1;
    }

    /**
     * Highways, railways and bridges sit on top of a chunk that was already
     * classified.
     *
     * <p>A chunk carrying a highway still reports whatever street type it was given
     * beforehand, which reads as a contradiction unless the highway is named too.
     * The two are decided at different stages and neither overwrites the other.
     */
    private static void describeInfrastructure(CommandSourceStack source, BuildingInfo info) {
        if (info.highwayXLevel >= 0) {
            line(source, "highway X", "level " + info.highwayXLevel
                    + ", running east to west over this chunk");
        }
        if (info.highwayZLevel >= 0) {
            line(source, "highway Z", "level " + info.highwayZLevel
                    + ", running north to south over this chunk");
        }
        if (info.xRailCorridor || info.zRailCorridor) {
            line(source, "rail corridor",
                    (info.xRailCorridor ? "X " : "") + (info.zRailCorridor ? "Z" : ""));
        }
        if (info.xBridge || info.zBridge) {
            line(source, "bridge",
                    (info.xBridge ? "X " : "") + (info.zBridge ? "Z" : ""));
        }
    }

    /**
     * What a character resolves to in this chunk's merged palette.
     *
     * <p>A palette is merged from the style, then the building, then the part, and
     * the result is not written anywhere an author can read. This is the only way to
     * see what a character actually became.
     */
    private static void describeCharacter(CommandSourceStack source, BuildingInfo info,
                                          String character) {
        if (character == null || character.isEmpty()) {
            return;
        }
        Character parsed = parseCharacter(source, character);
        if (parsed == null) {
            return;
        }
        char c = parsed;
        boolean byCodePoint = character.trim().regionMatches(true, 0, "U+", 0, 2);
        if (!byCodePoint && character.trim().length() > 1) {
            line(source, "note", "only the first character is used, as the mod does");
        }

        head(source, String.format("character '%c'  U+%04X", c, (int) c));

        CompiledPalette palette = info.getCompiledPalette();
        if (palette == null) {
            line(source, "here", "this chunk has no compiled palette");
        } else if (!palette.isDefined(c)) {
            line(source, "here", "NOTHING. Generation would fail this chunk with "
                    + "'Could not find entry'");
        } else {
            Set<BlockState> all;
            try {
                all = palette.getAll(c);
            } catch (Exception e) {
                all = Set.of();
            }
            line(source, "here", all == null || all.isEmpty()
                    ? String.valueOf(palette.get(c))
                    : describeBlocks(all));
        }

        // The chunk is only ever one answer, and where no city generated it is not an
        // answer at all. Every definition follows, by name, so the character can be
        // traced while editing rather than only while standing on the result.
        safely(source, () -> whereDefined(source, c));
    }

    /**
     * The reverse lookup: which characters produce this block here.
     *
     * <p>Reading a palette forwards answers "what is this character". Standing in
     * front of a block and asking which character placed it is the question an
     * author actually has, and no forward reading answers it, because the merged
     * palette is assembled in memory from up to three sources.
     *
     * <p>Several characters can map to one block, and a weighted list can hold it
     * among others, so every match is reported rather than the first.
     */
    private static int whichCharacters(CommandContext<CommandSourceStack> ctx, String id) {
        CommandSourceStack source = ctx.getSource();
        String wanted = id.trim();
        head(source, "characters mapping to " + wanted);

        // The chunk is best effort. A caller standing outside any city, or in a
        // dimension with no profile, still wants the answer for the pack being
        // written, and that answer does not depend on where they are.
        BuildingInfo info = chunkSilently(source);
        CompiledPalette palette = info == null ? null : info.getCompiledPalette();
        if (palette == null) {
            line(source, "here", "this chunk has no compiled palette, so only the "
                    + "assets below were searched");
            safely(source, () -> whereProduced(source, wanted));
            return 1;
        }

        int found = 0;
        for (Character c : palette.getCharacters()) {
            if (c == null) {
                continue;
            }
            Set<BlockState> all;
            try {
                all = palette.getAll(c);
            } catch (Exception e) {
                // getCharacters lists every key the merged palette holds, including
                // ones that carry only a mob, loot or tag and resolve to no block at
                // all. getAll throws for those. They cannot be a match, so skip them
                // rather than filling the answer with noise.
                continue;
            }
            if (all == null) {
                continue;
            }
            for (BlockState state : all) {
                if (state == null) {
                    continue;
                }
                // A registry lookup rather than builtInRegistryHolder, which throws
                // for a block that is not in the built-in registry.
                String name = String.valueOf(
                        BuiltInRegistries.BLOCK.getKey(state.getBlock()));
                if (!name.equals(wanted)) {
                    continue;
                }
                found++;
                line(source, String.format("here, '%c'  U+%04X", c, (int) c),
                        all.size() == 1 ? "always"
                                        : "one of " + all.size() + " in a weighted list");
                break;
            }
        }
        if (found == 0) {
            line(source, "here", "no character maps to it in this chunk's palette. The "
                    + "block may come from terrain, from the ruin or explosion pass, or "
                    + "from a part in a different building");
        }
        safely(source, () -> whereProduced(source, wanted));
        return 1;
    }

    /** The chunk the caller is standing in, or null with nothing reported. */
    private static BuildingInfo chunkSilently(CommandSourceStack source) {
        try {
            ServerLevel level = source.getLevel();
            ChunkPos pos = new ChunkPos(
                    net.minecraft.core.BlockPos.containing(source.getPosition()));
            IDimensionInfo provider = Registration.LOSTCITY_FEATURE.get()
                    .getDimensionInfo((WorldGenLevel) level);
            if (provider == null) {
                return null;
            }
            return BuildingInfo.getBuildingInfo(
                    new ChunkCoord(provider.getType(), pos.x, pos.z), provider);
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * Every named asset that defines this character.
     *
     * <p>The chunk's merged palette answers only what the character became where the
     * caller is standing, and where no city generated it answers nothing at all. This
     * is the part that does not depend on position.
     */
    private static void whereDefined(CommandSourceStack source, char c) {
        PaletteLookup.Scan scan = PaletteLookup.scan(source.getLevel());
        int found = 0;
        for (PaletteLookup.Source asset : scan.sources()) {
            Set<BlockState> blocks = PaletteLookup.blocksFor(asset, c);
            if (blocks == null) {
                continue;
            }
            found++;
            line(source, asset.label(), describeBlocks(blocks));
        }
        if (found == 0) {
            line(source, "defined in", "no palette, part or building in this world's "
                    + "assets. Check the character is the one written, and that the "
                    + "pack loaded");
        }
        reportUnreadable(source, scan);
    }

    /** Every named asset holding a character that produces this block. */
    private static void whereProduced(CommandSourceStack source, String blockId) {
        PaletteLookup.Scan scan = PaletteLookup.scan(source.getLevel());
        int found = 0;
        for (PaletteLookup.Source asset : scan.sources()) {
            for (Character c : PaletteLookup.charsFor(asset, blockId)) {
                found++;
                int weight = PaletteLookup.weight(asset, c);
                line(source, asset.label(),
                        String.format("'%c'  U+%04X, %s", c, (int) c,
                                weight <= 1 ? "always"
                                            : "one of " + weight + " in a weighted list"));
            }
        }
        if (found == 0) {
            line(source, "produced by", "no character in any palette, part or building. "
                    + "The block may come from terrain, from the ruin or explosion pass, "
                    + "or from the style rather than a palette");
        }
        reportUnreadable(source, scan);
    }

    /**
     * Runs a lookup and reports what went wrong if it throws.
     *
     * <p>Vanilla catches a command's exception, answers "An unexpected error occurred"
     * and puts the message in hover text that a console, an RCON client and a log line
     * all discard. For a tool whose whole purpose is to say what failed, that is the
     * one answer it must never give.
     */
    private static int safely(CommandSourceStack source, Runnable body) {
        try {
            body.run();
            return 1;
        } catch (Exception e) {
            LostCitiesDevTool.LOGGER.error("lcdev lookup failed", e);
            source.sendFailure(Component.literal(
                    "The lookup failed: " + e.getClass().getSimpleName()
                            + (e.getMessage() == null ? "" : ": " + e.getMessage())
                            + ". The full trace is in the log."));
            return 0;
        }
    }

    /**
     * Names the gap when the search could not read every asset.
     *
     * <p>An answer assembled from part of the assets looks exactly like an answer
     * assembled from all of them. Saying so is the difference between "not defined
     * anywhere" and "not defined anywhere I could read".
     */
    private static void reportUnreadable(CommandSourceStack source,
                                         PaletteLookup.Scan scan) {
        List<PaletteLookup.Unreadable> bad = scan.unreadable();
        if (bad.isEmpty()) {
            return;
        }
        line(source, "incomplete", bad.size() + (bad.size() == 1 ? " asset" : " assets")
                + " could not be built and were not searched");
        for (PaletteLookup.Unreadable u : bad) {
            line(source, "  " + u.kind() + " " + u.id(), u.reason());
        }
    }

    /** {@code /lcdev in <asset> char <c>}: one named asset, from anywhere. */
    private static int charInAsset(CommandContext<CommandSourceStack> ctx, String character) {
        CommandSourceStack source = ctx.getSource();
        return safely(source, () -> charInAssetBody(ctx, source, character));
    }

    private static void charInAssetBody(CommandContext<CommandSourceStack> ctx,
                                        CommandSourceStack source, String character) {
        ResourceLocation id = ResourceLocationArgument.getId(ctx, "asset");
        Character parsed = parseCharacter(source, character);
        if (parsed == null) {
            return;
        }
        char c = parsed;
        PaletteLookup.Scan scan = PaletteLookup.scan(source.getLevel());
        List<PaletteLookup.Source> matches = PaletteLookup.withId(scan.sources(), id);
        if (matches.isEmpty()) {
            reportUnreadable(source, scan);
            source.sendFailure(Component.literal(
                    "No palette, part or building named " + id + " carries a palette. "
                            + "A part or building only appears here if it defines one "
                            + "inline; one using refpalette points at a palette asset."));
            return;
        }
        head(source, String.format("character '%c'  U+%04X in %s", c, (int) c, id));
        for (PaletteLookup.Source asset : matches) {
            Set<BlockState> blocks = PaletteLookup.blocksFor(asset, c);
            line(source, asset.kind(), blocks == null
                    ? "does not define it"
                    : describeBlocks(blocks));
        }
    }

    /** {@code /lcdev in <asset> block <id>}: the reverse lookup, in one named asset. */
    private static int blockInAsset(CommandContext<CommandSourceStack> ctx, String blockId) {
        CommandSourceStack source = ctx.getSource();
        return safely(source, () -> blockInAssetBody(ctx, source, blockId));
    }

    private static void blockInAssetBody(CommandContext<CommandSourceStack> ctx,
                                         CommandSourceStack source, String blockId) {
        ResourceLocation id = ResourceLocationArgument.getId(ctx, "asset");
        String wanted = blockId.trim();
        PaletteLookup.Scan scan = PaletteLookup.scan(source.getLevel());
        List<PaletteLookup.Source> matches = PaletteLookup.withId(scan.sources(), id);
        if (matches.isEmpty()) {
            reportUnreadable(source, scan);
            source.sendFailure(Component.literal(
                    "No palette, part or building named " + id + " carries a palette."));
            return;
        }
        head(source, "characters mapping to " + wanted + " in " + id);
        int found = 0;
        for (PaletteLookup.Source asset : matches) {
            for (Character c : PaletteLookup.charsFor(asset, wanted)) {
                found++;
                int weight = PaletteLookup.weight(asset, c);
                line(source, String.format("'%c'  U+%04X", c, (int) c),
                        (weight <= 1 ? "always" : "one of " + weight + " in a weighted list")
                                + ", in the " + asset.kind());
            }
        }
        if (found == 0) {
            line(source, "no character", "in " + id + " maps to that block");
        }
    }

    /** One block, or a weighted list, in the wording both lookups use. */
    private static String describeBlocks(Set<BlockState> blocks) {
        if (blocks.isEmpty()) {
            return "defined, but not as a block. It carries only a mob, loot or tag, "
                    + "or it is a frompalette alias this file cannot resolve alone";
        }
        if (blocks.size() == 1) {
            return String.valueOf(blocks.iterator().next());
        }
        StringBuilder sb = new StringBuilder(blocks.size() + " in a weighted list:");
        for (BlockState state : blocks) {
            sb.append(' ').append(state);
        }
        return sb.toString();
    }

    /** The chunk the caller is standing in, or null with the reason already reported. */
    private static BuildingInfo chunkAt(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        ChunkPos pos = new ChunkPos(net.minecraft.core.BlockPos.containing(source.getPosition()));
        IDimensionInfo provider = Registration.LOSTCITY_FEATURE.get()
                .getDimensionInfo((WorldGenLevel) level);
        if (provider == null) {
            source.sendFailure(Component.literal(
                    "No Lost Cities profile is attached to " + level.dimension().location()));
            return null;
        }
        try {
            return BuildingInfo.getBuildingInfo(
                    new ChunkCoord(provider.getType(), pos.x, pos.z), provider);
        } catch (Exception e) {
            source.sendFailure(Component.literal(
                    "This chunk cannot be described: " + e.getMessage()));
            return null;
        }
    }

    /**
     * Reads either a literal character or a {@code U+XXXX} code point.
     *
     * <p>A palette character is routinely one a chat box cannot accept, and pasting
     * an invisible or right-to-left character into a command is worse still. Every
     * report prints the code point beside the character for exactly that reason, so
     * the same notation has to be accepted back.
     */
    private static Character parseCharacter(CommandSourceStack source, String text) {
        String t = text.trim();
        if (t.regionMatches(true, 0, "U+", 0, 2)) {
            try {
                int cp = Integer.parseInt(t.substring(2), 16);
                if (cp > 0xFFFF) {
                    source.sendFailure(Component.literal(
                            "U+" + Integer.toHexString(cp).toUpperCase()
                                    + " is above U+FFFF and cannot be a palette key. "
                                    + "The mod keeps only the leading surrogate."));
                    return null;
                }
                return (char) cp;
            } catch (NumberFormatException e) {
                source.sendFailure(Component.literal(
                        "'" + t + "' is not a code point. Write it as U+0470."));
                return null;
            }
        }
        return t.isEmpty() ? null : t.charAt(0);
    }

    private static void head(CommandSourceStack source, String text) {
        source.sendSuccess(() -> Component.literal(text)
                .withStyle(ChatFormatting.AQUA), false);
    }

    private static void line(CommandSourceStack source, String key, String value) {
        source.sendSuccess(() -> Component.literal(key + ": ")
                .withStyle(ChatFormatting.GRAY)
                .append(Component.literal(value).withStyle(ChatFormatting.WHITE)), false);
    }
}
