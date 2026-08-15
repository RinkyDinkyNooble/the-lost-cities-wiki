package com.rinkynooble.lostcitiesdevtool.client;

import mcjty.lostcities.config.LostCityProfile;
import mcjty.lostcities.config.ProfileSetup;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * The profile list the Cities screen offers, in the order it offers it.
 *
 * <p>Built the same way {@code LostCitySetup.toggleProfile} builds it, so anything
 * reading this list steps through exactly the entries the button does. Written once
 * here rather than twice, because a backward cycle that disagreed with the forward
 * one about the order would be worse than no backward cycle.
 *
 * <p>Two rules, both read from {@code toggleProfile} in 7.4.12:
 *
 * <ul>
 *   <li><b>Which profiles appear.</b> Every entry of
 *       {@code ProfileSetup.STANDARD_PROFILES} whose {@code isPublic()} is true.
 *       That flag defaults to true and is false only where a profile's own JSON says
 *       {@code "public": false}, which is how the sphere-outside profiles are hidden.
 *       Nothing tests the characters of a name.
 *   <li><b>The order.</b> {@code default} pinned first, then {@code String.compareTo}
 *       on the profile key. That is code point order, so a digit sorts before an
 *       uppercase letter and an uppercase letter before a lowercase one. It is not
 *       case-insensitive alphabetical, and it sorts the key rather than the label.
 * </ul>
 */
public final class Profiles {

    /** The profile pinned to the front of the list, whatever it would sort as. */
    private static final String PINNED = "default";

    private Profiles() {
    }

    /** Every selectable profile, in the order the Cities button steps through them. */
    public static List<String> selectable() {
        List<String> names = new ArrayList<>();
        for (Map.Entry<String, LostCityProfile> entry
                : ProfileSetup.STANDARD_PROFILES.entrySet()) {
            if (entry.getValue().isPublic()) {
                names.add(entry.getKey());
            }
        }
        names.sort((a, b) -> {
            if (PINNED.equals(a)) {
                return -1;
            }
            if (PINNED.equals(b)) {
                return 1;
            }
            return a.compareTo(b);
        });
        return names;
    }

    /**
     * The entry before {@code current}, or null for the disabled state.
     *
     * <p>The exact inverse of the forward cycle, which runs null, first, second, and
     * so on to last, then back to null. So going back from null reaches the last
     * entry, and going back from the first reaches null. An unrecognised name lands
     * on null, which is what the forward cycle does with one too.
     */
    public static String previous(String current) {
        List<String> names = selectable();
        if (names.isEmpty()) {
            return null;
        }
        if (current == null) {
            return names.get(names.size() - 1);
        }
        int index = names.indexOf(current);
        if (index <= 0) {
            return null;
        }
        return names.get(index - 1);
    }
}
