package com.rinkynooble.lostcitiesdevtool.client;

import mcjty.lostcities.config.LostCityProfile;
import mcjty.lostcities.config.ProfileSetup;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * The profile list the Cities screen offers, built the way
 * {@code LostCitySetup.toggleProfile} builds it.
 *
 * <p>Which profiles appear: every entry of {@code ProfileSetup.STANDARD_PROFILES}
 * whose {@code isPublic()} is true. That flag defaults to true and is false only
 * where a profile's own JSON says {@code "public": false}, which is how the
 * sphere-outside profiles are hidden. Nothing tests the characters of a name. The
 * order is {@link ProfileOrder}'s.
 *
 * <p>Written once here, because the Customize repair builds this list too, and a
 * list built there in another order is the one the forward cycle then keeps: the
 * repair used to build it unsorted, so after it fired the left click cycled in hash
 * order and the right click in sorted order.
 */
public final class Profiles {

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
        return ProfileOrder.sorted(names);
    }
}
