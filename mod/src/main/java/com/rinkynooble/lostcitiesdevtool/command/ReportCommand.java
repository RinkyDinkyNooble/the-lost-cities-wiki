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
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;

import java.util.Set;

/**
 * {@code /lcdev report} and {@code /lcdev report <char>}.
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
                        .executes(ctx -> report(ctx, null))
                        .then(Commands.argument("character", StringArgumentType.greedyString())
                                .executes(ctx -> report(ctx,
                                        StringArgumentType.getString(ctx, "character"))))));
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
        char c = character.charAt(0);
        if (character.length() > 1) {
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
