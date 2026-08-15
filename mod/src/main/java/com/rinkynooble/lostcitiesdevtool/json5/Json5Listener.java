package com.rinkynooble.lostcitiesdevtool.json5;

import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimplePreparableReloadListener;
import net.minecraft.util.profiling.ProfilerFiller;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Finds Lost Cities assets that exist as both {@code .json} and {@code .json5}.
 *
 * <p>The listing is redone on every datapack load rather than recorded as the files
 * are read, so the report describes what is on disk now. Asking the resource manager
 * for the {@code .json} sibling directly is what makes that reliable: the
 * {@code .json5} file is served under the sibling's name by the time anything else
 * looks, so counting collisions at the point of substitution would report every file
 * as its own override.
 */
public class Json5Listener extends SimplePreparableReloadListener<List<String>> {

    @Override
    protected List<String> prepare(ResourceManager manager, ProfilerFiller profiler) {
        List<String> overrides = new ArrayList<>();
        if (!Config.on(Config.INSTANCE.acceptJson5Extension, true)) {
            return overrides;
        }
        Map<ResourceLocation, Resource> five = manager.listResources(
                "lostcities", path -> path.getPath().endsWith(Json5.EXT_JSON5));
        for (ResourceLocation location : five.keySet()) {
            ResourceLocation shadowed = Json5.asJson(location);
            if (manager.getResource(shadowed).isPresent()) {
                overrides.add(location.getNamespace() + ":" + location.getPath());
            }
        }
        return overrides;
    }

    @Override
    protected void apply(List<String> overrides, ResourceManager manager,
                         ProfilerFiller profiler) {
        Json5Overrides.setAssets(overrides);
        if (overrides.isEmpty() || !Config.on(Config.INSTANCE.warnOnJson5Override, true)) {
            return;
        }
        LostCitiesDevTool.LOGGER.warn(describe(overrides));
    }

    /** The same wording the log and the chat message on world join both use. */
    public static String describe(List<String> overrides) {
        StringBuilder sb = new StringBuilder();
        sb.append("Lost Cities JSON5: ").append(overrides.size())
          .append(overrides.size() == 1 ? " file is" : " files are")
          .append(" shadowing a .json of the same name");
        for (String file : overrides) {
            sb.append("\n  ").append(file).append("  wins over  ")
              .append(file, 0, file.length() - 1);
        }
        sb.append("\n  The .json is not read. Delete it, or delete the .json5, "
                + "so an edit lands where you expect.");
        sb.append("\n  Set 'warnOnJson5Override' to false to stop saying this.");
        return sb.toString();
    }
}
