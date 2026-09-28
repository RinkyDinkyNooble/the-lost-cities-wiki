package com.rinkynooble.lostcitiesdevtool.client;

import javax.annotation.Nullable;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * The order the Cities screen steps through profiles in, with no Lost Cities type in
 * it, so it can be exercised without a client.
 *
 * <p>Read from {@code LostCitySetup.toggleProfile} in 7.5.4: {@code default} pinned
 * first, then {@code String.compareTo} on the name, which is code point order, so a
 * digit sorts before an uppercase letter and an uppercase letter before a lowercase
 * one. The forward cycle runs null, first, second and so on to last, then back to
 * null.
 *
 * <p>{@code toggleProfile} sorts only a list it built itself. A list somebody else
 * built is stepped through in whatever order it arrives in, which is why every list
 * this mod hands the screen comes out of {@link #sorted}.
 */
public final class ProfileOrder {

    /** The profile pinned to the front of the list, whatever it would sort as. */
    public static final String PINNED = "default";

    private ProfileOrder() {
    }

    /** These names in the order {@code toggleProfile} sorts them into. */
    public static List<String> sorted(Collection<String> names) {
        List<String> out = new ArrayList<>(names);
        out.sort((a, b) -> {
            if (PINNED.equals(a)) {
                return PINNED.equals(b) ? 0 : -1;
            }
            if (PINNED.equals(b)) {
                return 1;
            }
            return a.compareTo(b);
        });
        return out;
    }

    /**
     * The entry before {@code current} in the cycle this list makes, or null for
     * the disabled state.
     *
     * <p>The exact inverse of the forward cycle. Going back from null reaches the
     * last entry, and going back from the first reaches null. An unrecognised name
     * lands on null, which is what the forward cycle does with one too.
     */
    @Nullable
    public static String previous(List<String> cycle, @Nullable String current) {
        if (cycle.isEmpty()) {
            return null;
        }
        if (current == null) {
            return cycle.get(cycle.size() - 1);
        }
        int index = cycle.indexOf(current);
        return index <= 0 ? null : cycle.get(index - 1);
    }
}
