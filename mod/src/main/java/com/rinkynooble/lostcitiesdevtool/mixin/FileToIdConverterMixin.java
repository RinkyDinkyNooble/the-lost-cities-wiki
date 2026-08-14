package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.json5.Json5;
import net.minecraft.resources.FileToIdConverter;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.server.packs.resources.ResourceManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Feature 2.1. Routes Lost Cities asset files through the relaxed reader.
 *
 * <p>This is the one place where a datapack registry's files are listed together with
 * the {@link ResourceLocation} each came from, which is what makes it possible to
 * treat Lost Cities assets differently from everything else. A hook further down,
 * where only a stream is in hand, could not tell them apart.
 *
 * <p>Entries outside {@code lostcities/} are returned untouched, so no other mod's
 * files and none of Minecraft's own change behaviour. When nothing in the listing is
 * a Lost Cities asset, which is the usual case, the original map is returned as it
 * came.
 */
@Mixin(FileToIdConverter.class)
public abstract class FileToIdConverterMixin {

    @Inject(method = "listMatchingResources", at = @At("RETURN"), cancellable = true)
    private void lostcitiesdevtool$relaxLostCitiesAssets(
            ResourceManager manager,
            CallbackInfoReturnable<Map<ResourceLocation, Resource>> cir) {

        if (!Config.INSTANCE.acceptCommentsAndTrailingCommas.get()) {
            return;
        }
        Map<ResourceLocation, Resource> found = cir.getReturnValue();
        if (found == null || found.isEmpty()) {
            return;
        }
        boolean anyOurs = false;
        for (ResourceLocation location : found.keySet()) {
            if (Json5.appliesTo(location)) {
                anyOurs = true;
                break;
            }
        }
        if (!anyOurs) {
            return;
        }
        Map<ResourceLocation, Resource> relaxed = new LinkedHashMap<>(found);
        found.forEach((location, resource) -> {
            if (Json5.appliesTo(location)) {
                relaxed.put(location, Json5.wrap(resource));
            }
        });
        cir.setReturnValue(relaxed);
    }
}
