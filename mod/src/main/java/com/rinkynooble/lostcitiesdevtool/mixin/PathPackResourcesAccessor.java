package com.rinkynooble.lostcitiesdevtool.mixin;

import net.minecraft.server.packs.PathPackResources;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

import java.nio.file.Path;

/**
 * Reaches the folder a loose datapack sits in.
 *
 * <p>Needed for one thing: finding a {@code LICENSE.txt} at the root of a pack that
 * is a folder rather than a zip. {@code getRootResource} is the public way in and it
 * cannot reach that file, because it validates every path segment against
 * {@code [-._a-z0-9]+} and throws on an uppercase one. A zip pack has no such check,
 * so the same file is readable there and not here, and the commonest spelling of the
 * commonest file is the one that fails.
 *
 * <p>With the folder in hand the root can be listed instead of guessed at, which
 * also finds {@code COPYING}, {@code Licence.md} and whatever else an author used.
 */
@Mixin(PathPackResources.class)
public interface PathPackResourcesAccessor {

    @Accessor("root")
    Path lostcitiesdevtool$root();
}
