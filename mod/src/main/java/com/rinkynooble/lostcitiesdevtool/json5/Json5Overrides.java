package com.rinkynooble.lostcitiesdevtool.json5;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Which files are being shadowed by a {@code .json5} of the same name.
 *
 * <p>Two lists, because they are found at different times and neither can replace the
 * other. Profiles are read from {@code config/lostcities/profiles} once, during mod
 * construction. Datapack assets are listed again on every {@code /reload}, so that
 * list is replaced wholesale each time rather than accumulated, and a shadowed file
 * that an author deletes stops being reported at the next reload.
 *
 * <p>An override is not an error. It is reported because the two files look
 * interchangeable in an editor and are not: only one of them is in play, and an edit
 * to the wrong one changes nothing.
 */
public final class Json5Overrides {

    private static volatile List<String> assets = List.of();
    private static volatile List<String> profiles = List.of();

    private Json5Overrides() {
    }

    public static void setAssets(List<String> found) {
        assets = List.copyOf(found);
    }

    public static void setProfiles(List<String> found) {
        profiles = List.copyOf(found);
    }

    /** The shadowed profiles, found before any config file has been read. */
    public static List<String> profiles() {
        return profiles;
    }

    /** Every shadowed file, profiles first, in the order each was found. */
    public static List<String> all() {
        if (assets.isEmpty() && profiles.isEmpty()) {
            return Collections.emptyList();
        }
        List<String> both = new ArrayList<>(profiles);
        both.addAll(assets);
        return both;
    }
}
