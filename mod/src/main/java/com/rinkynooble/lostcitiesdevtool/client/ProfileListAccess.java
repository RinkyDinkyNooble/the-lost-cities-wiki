package com.rinkynooble.lostcitiesdevtool.client;

import javax.annotation.Nullable;
import java.util.List;

/**
 * The Cities screen's own profile list, which {@code LostCitySetupMixin} adds to
 * {@code LostCitySetup}.
 *
 * <p>The backward cycle steps through this list rather than a rebuilt one, so it is
 * the inverse of the forward cycle by construction: the entry {@code customize}
 * appends is in it, and so is any order the list happens to be in.
 */
public interface ProfileListAccess {

    /** The live list, or null before the screen has built one. */
    @Nullable
    List<String> lostcitiesdevtool$profiles();
}
