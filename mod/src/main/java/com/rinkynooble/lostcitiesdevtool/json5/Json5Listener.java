package com.rinkynooble.lostcitiesdevtool.json5;

import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import com.rinkynooble.lostcitiesdevtool.chat.Chat;
import net.minecraft.network.chat.Component;
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
        sb.append(headline(overrides));
        for (String file : overrides) {
            sb.append("\n  ").append(pair(file));
        }
        sb.append("\n  ").append(CONSEQUENCE);
        sb.append("\n  ").append(QUIET);
        return sb.toString();
    }

    /**
     * The same thing for chat, one component per line.
     *
     * <p>Chat is not a log file. A single literal with newlines in it is wrapped by
     * the client wherever it runs out of width, so each entry breaks across two or
     * three lines and the list stops reading as a list. One component per line does
     * not.
     *
     * <p>The pair is named once rather than twice. "x.json5 wins over x.json" says
     * the same word twice for every entry, and the heading already says what is
     * happening, so the file is enough.
     */
    public static List<Component> lines(List<String> overrides) {
        List<Component> out = new ArrayList<>(Chat.headerLines("Lost Cities JSON5",
                overrides.size() + (overrides.size() == 1 ? " file" : " files")));
        for (String file : overrides) {
            out.add(Chat.itemLine(pair(file)));
        }
        out.add(Chat.noteLine(CONSEQUENCE));
        out.add(Chat.noteLine(QUIET));
        return out;
    }

    private static String headline(List<String> overrides) {
        return "Lost Cities JSON5: " + overrides.size()
                + (overrides.size() == 1 ? " file is" : " files are")
                + " shadowing a .json of the same name";
    }

    /** The name both files share, which is the only part worth reading. */
    private static String pair(String file) {
        return file.endsWith(EXT) ? file.substring(0, file.length() - EXT.length())
                : file;
    }

    private static final String EXT = ".json5";

    private static final String CONSEQUENCE =
            "The .json of each is not read. Delete one of the pair so an edit lands "
                    + "where you expect.";

    private static final String QUIET =
            "Set 'warnOnJson5Override' to false to stop saying this.";
}
