package com.rinkynooble.lostcitiesdevtool.platform;

import com.rinkynooble.lostcitiesdevtool.core.Catalogue;
import net.minecraftforge.fml.ModList;

import javax.annotation.Nullable;

/**
 * Which Lost Cities the shipped reference was built for, and which one is here.
 *
 * <p><b>These are two different facts and the workshop used to print only the
 * first, labelled as though it were the second.</b> `/lcdev workshop go` said
 * "version 7.5.4" on a server running 7.5.5, because `catalogue.json` is generated
 * against one jar at build time and carries that jar's number. Read on screen it
 * looks like the mod reporting what it found, and it is nothing of the kind.
 *
 * <p>The catalogue being older than the running game is allowed: the range spans
 * five versions and the reference is generated from one of them. What is not
 * allowed is saying so ambiguously, so every place that shows a version now shows
 * which of the two it means, and says plainly when they differ.
 */
public final class Versions {

    /** Lost Cities' mod id, which is how the loader is asked what it has. */
    private static final String LOSTCITIES = "lostcities";

    /**
     * Lost Cities reports itself with the Minecraft branch in front, as
     * {@code 1.20-7.5.5}. Only the part after the dash is comparable with what the
     * generators write, which is a bare {@code 7.5.5}.
     */
    private static final String BRANCH_SEPARATOR = "-";

    private Versions() {
    }

    /** The version the catalogue and the key reference were generated from. */
    public static String catalogue() {
        return Catalogue.version();
    }

    /**
     * What Lost Cities reports on this server, branch and all, or null where the
     * loader has no answer.
     *
     * <p>Null is reachable: a plain JVM test has no mod list, and asking then throws
     * rather than returning nothing. Every caller treats null as "cannot say" rather
     * than as a mismatch, because claiming a mismatch on no evidence is the same
     * class of error this class exists to stop.
     */
    @Nullable
    public static String running() {
        try {
            return ModList.get().getModContainerById(LOSTCITIES)
                    .map(c -> c.getModInfo().getVersion().toString())
                    .orElse(null);
        } catch (RuntimeException | LinkageError e) {
            return null;
        }
    }

    /** The running version with the Minecraft branch stripped, or null. */
    @Nullable
    public static String runningShort() {
        String full = running();
        if (full == null) {
            return null;
        }
        int dash = full.lastIndexOf(BRANCH_SEPARATOR);
        return dash >= 0 && dash < full.length() - 1
                ? full.substring(dash + 1) : full;
    }

    /** Whether the reference describes the Lost Cities that is installed. */
    public static boolean current() {
        String here = runningShort();
        return here == null || here.equals(catalogue());
    }

    /**
     * One line saying the reference is older than the game, or null when it is not.
     *
     * <p>Worth saying every time rather than once at boot. Somebody who opens the
     * workshop months later and finds a key missing needs the reason in front of
     * them, not in a log they have already rotated away.
     */
    @Nullable
    public static String mismatch() {
        if (current()) {
            return null;
        }
        return "This reference was generated for Lost Cities " + catalogue()
                + " and this server runs " + runningShort() + ". Anything "
                + runningShort() + " added is not described here, has no plot in "
                + "the catalogue, and is not written by an export.";
    }
}
