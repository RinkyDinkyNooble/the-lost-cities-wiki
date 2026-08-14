package com.rinkynooble.lostcitiesdevtool.diagnostics;

import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import mcjty.lostcities.varia.ChunkCoord;
import mcjty.lostcities.worldgen.IDimensionInfo;
import mcjty.lostcities.worldgen.lost.BuildingInfo;
import mcjty.lostcities.worldgen.lost.cityassets.CityStyle;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Turns a caught generation fault into a report that names everything the mod knows
 * at that moment.
 *
 * <p>The mod's own line is {@code Error generating chunk <x>,<z>: <message>}. That
 * names the chunk that was being generated, which for a whole class of faults is not
 * the chunk at fault: a fault raised while building a chunk's {@code BuildingInfo}
 * spreads to every neighbour that queries it, and on 7.4.12 three broken buildings
 * produced 77 failed chunks across a 13 by 10 chunk area.
 *
 * <p>Two further problems make the stock line hard to act on. The palette message
 * names the part rather than the palette that failed to define the character, and
 * the JVM stops recording stack traces for a repeatedly thrown exception, so most
 * lines in a long run carry only a message or {@code null}.
 */
public final class FaultReport {

    /** {@code Could not find entry 'X' in the palette for part 'ns:name'!} */
    private static final Pattern MISSING_CHAR = Pattern.compile(
            "Could not find entry '(.)' in the palette for part '([^']*)'!");

    private FaultReport() {
    }

    public static void log(int chunkX, int chunkZ, IDimensionInfo provider, Throwable fault) {
        List<String> lines = new ArrayList<>();
        lines.add("chunk " + chunkX + "," + chunkZ);

        describeFault(lines, fault);
        describeDimension(lines, provider);
        describeChunk(lines, chunkX, chunkZ, provider);

        StringBuilder sb = new StringBuilder("Lost Cities generation fault");
        for (String line : lines) {
            sb.append("\n    ").append(line);
        }
        LostCitiesDevTool.LOGGER.error(sb.toString());
    }

    /**
     * The message, its type, and every cause under it.
     *
     * <p>Worth printing in full because the JVM drops the stack trace for a
     * repeatedly thrown exception, and the earliest failures are the useful ones.
     */
    private static void describeFault(List<String> lines, Throwable fault) {
        if (fault == null) {
            lines.add("fault: none supplied");
            return;
        }
        lines.add("fault: " + fault.getClass().getSimpleName() + ": " + fault.getMessage());
        for (Throwable cause = fault.getCause(); cause != null; cause = cause.getCause()) {
            lines.add("caused by: " + cause.getClass().getSimpleName()
                    + ": " + cause.getMessage());
        }
        describeMissingCharacter(lines, fault.getMessage());
    }

    /**
     * A palette character that did not resolve is worth spelling out. The character
     * itself may be invisible, may be a lookalike from another alphabet, or may be
     * the trailing half of a surrogate pair, and none of those are readable in a log.
     */
    private static void describeMissingCharacter(List<String> lines, String message) {
        if (message == null) {
            return;
        }
        Matcher m = MISSING_CHAR.matcher(message);
        if (!m.find()) {
            return;
        }
        char c = m.group(1).charAt(0);
        lines.add(String.format(
                "undefined character: '%c'  U+%04X  %s", c, (int) c, characterNote(c)));
        lines.add("used by part: " + m.group(2));
        lines.add("the message names the part, but the fault is in a palette. Check, in this order:");
        lines.add("  1. the part's own 'palette' or 'refpalette'");
        lines.add("  2. the building's 'palette' or 'refpalette'");
        lines.add("  3. the style's palettes, which the city style selects");
        lines.add("  4. whether the character is a 'frompalette' alias in a cycle, "
                + "which resolves to nothing and reports nothing at load");
    }

    private static String characterNote(char c) {
        if (Character.isHighSurrogate(c) || Character.isLowSurrogate(c)) {
            return "half of a surrogate pair. A character above U+FFFF cannot be a "
                    + "palette key, and occupies two positions in a slices row";
        }
        if (Character.isWhitespace(c)) {
            return "whitespace. A space is only air because the shipped 'common' "
                    + "palette defines it that way";
        }
        if (c > 0x7F) {
            return Character.getName(c);
        }
        return "printable ASCII";
    }

    private static void describeDimension(List<String> lines, IDimensionInfo provider) {
        if (provider == null) {
            return;
        }
        try {
            if (provider.getProfile() != null) {
                lines.add("profile: " + provider.getProfile().getName());
            }
            if (provider.getWorldStyle() != null) {
                lines.add("world style: " + provider.getWorldStyle().getName());
            }
        } catch (Exception e) {
            lines.add("profile: unreadable (" + e.getMessage() + ")");
        }
    }

    /**
     * Ask the chunk what it was building.
     *
     * <p>Guarded, because for a condition fault this is the call that threw in the
     * first place and it will throw again. The mod's own {@code logChunkInfo} hits
     * the same wall and reports {@code Error loging chunk info!}.
     */
    private static void describeChunk(List<String> lines, int chunkX, int chunkZ,
                                      IDimensionInfo provider) {
        if (provider == null) {
            return;
        }
        try {
            ChunkCoord coord = new ChunkCoord(provider.getType(), chunkX, chunkZ);
            BuildingInfo info = BuildingInfo.getBuildingInfo(coord, provider);
            if (info == null) {
                return;
            }
            lines.add("is city: " + info.isCity + ", city level: " + info.cityLevel);
            if (info.hasBuilding) {
                // getId is the full namespace:path, which is what a reader has to
                // search their datapack for. getName alone is ambiguous across packs.
                lines.add("building: " + info.getBuilding().getId()
                        + ", floors: " + info.getNumFloors()
                        + ", cellars: " + info.getNumCellars()
                        + " (levels run " + (-info.getNumCellars())
                        + " to " + info.getNumFloors() + " inclusive)");
            } else {
                lines.add("no building in this chunk, so the fault belongs to a "
                        + "chunk this one queried. The building is named in the "
                        + "message above");
            }
            CityStyle style = info.getCityStyle();
            if (style != null) {
                lines.add("city style: " + style.getName());
            }
        } catch (Exception e) {
            // The usual case for a condition fault. Say so rather than staying silent,
            // because it is itself evidence about which kind of fault this is.
            lines.add("chunk detail unavailable: rebuilding this chunk's info threw "
                    + e.getClass().getSimpleName() + ": " + e.getMessage());
            lines.add("that means the fault is in the chunk's own selection stage, "
                    + "not in block placement, so it will also fail every neighbour "
                    + "that queries this chunk");
        }
    }
}
