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
 * Features 2.1 and 2.2. Routes Lost Cities asset files through the relaxed reader, and
 * lets them be named {@code .json5}.
 *
 * <p>This is the one place where a datapack registry's files are listed together with
 * the {@link ResourceLocation} each came from, which is what makes it possible to
 * treat Lost Cities assets differently from everything else. A hook further down,
 * where only a stream is in hand, could not tell them apart.
 *
 * <p>Folders outside {@code lostcities/} return before anything is touched, so no
 * other mod's files and none of Minecraft's own change behaviour.
 *
 * <p>A {@code .json5} file is added to the listing under its {@code .json} name.
 * Vanilla filters this listing on the extension and then strips a fixed number of
 * characters to derive the id, so a file left under its own name would be either
 * invisible or registered under a mangled id. Renaming it here keeps both steps
 * correct and means no other vanilla method needs patching.
 *
 * <p>Where both names exist the {@code .json5} wins, because it is the one written by
 * hand: {@code ProfileSetup} rewrites every shipped profile as {@code .json} on each
 * launch, so the opposite rule would make overriding one impossible. The collision is
 * reported separately, by {@code Json5Listener}.
 */
@Mixin(FileToIdConverter.class)
public abstract class FileToIdConverterMixin {

    @Inject(method = "listMatchingResources", at = @At("RETURN"), cancellable = true)
    private void lostcitiesdevtool$relaxLostCitiesAssets(
            ResourceManager manager,
            CallbackInfoReturnable<Map<ResourceLocation, Resource>> cir) {

        boolean comments = Config.on(Config.INSTANCE.acceptCommentsAndTrailingCommas, true);
        boolean extension = Config.on(Config.INSTANCE.acceptJson5Extension, true);
        if (!comments && !extension) {
            return;
        }
        String folder = Json5.folderOf((FileToIdConverter) (Object) this);
        if (folder == null || !Json5.appliesToFolder(folder)) {
            return;
        }

        Map<ResourceLocation, Resource> found = cir.getReturnValue();
        Map<ResourceLocation, Resource> relaxed = new LinkedHashMap<>();
        if (found != null) {
            found.forEach((location, resource) ->
                    relaxed.put(location, comments ? Json5.wrap(resource) : resource));
        }
        if (extension) {
            // A .json5 file is read relaxed whatever the comments toggle says. Comments
            // are the reason to write one, and its name is what asks for them.
            manager.listResources(folder, path -> path.getPath().endsWith(Json5.EXT_JSON5))
                    .forEach((location, resource) ->
                            relaxed.put(Json5.asJson(location), Json5.wrap(resource)));
        }
        cir.setReturnValue(relaxed);
    }
}
