package com.rinkynooble.lostcitiesdevtool.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
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
                                        StringArgumentType.getString(ctx, "id"))))));
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

        CompiledPalette palette = info.getCompiledPalette();
        if (palette == null) {
            line(source, "palette", "this chunk has no compiled palette");
            return;
        }
        head(source, String.format("character '%c'  U+%04X", c, (int) c));

        if (!palette.isDefined(c)) {
            line(source, "resolves to", "NOTHING. Generation would fail this chunk with "
                    + "'Could not find entry'");
            line(source, "check", "the part's palette, then the building's, then the "
                    + "style's, and whether it is a frompalette alias in a cycle");
            return;
        }
        Set<BlockState> all = palette.getAll(c);
        if (all == null || all.isEmpty()) {
            line(source, "resolves to", String.valueOf(palette.get(c)));
            return;
        }
        if (all.size() == 1) {
            line(source, "resolves to", String.valueOf(all.iterator().next()));
        } else {
            line(source, "resolves to", all.size() + " possible blocks, a weighted list");
            for (BlockState state : all) {
                line(source, "  ", String.valueOf(state));
            }
        }
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
        BuildingInfo info = chunkAt(source);
        if (info == null) {
            return 0;
        }
        CompiledPalette palette = info.getCompiledPalette();
        if (palette == null) {
            source.sendFailure(Component.literal("This chunk has no compiled palette."));
            return 0;
        }

        String wanted = id.trim();
        head(source, "characters mapping to " + wanted);

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
                line(source, String.format("'%c'  U+%04X", c, (int) c),
                        all.size() == 1 ? "always"
                                        : "one of " + all.size() + " in a weighted list");
                break;
            }
        }
        if (found == 0) {
            line(source, "no character", "maps to that block in this chunk's palette. "
                    + "The block may come from terrain, from the ruin or explosion pass, "
                    + "or from a part in a different building");
        }
        return 1;
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
