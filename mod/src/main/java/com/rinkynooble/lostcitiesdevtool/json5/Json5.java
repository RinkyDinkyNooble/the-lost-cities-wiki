package com.rinkynooble.lostcitiesdevtool.json5;

import com.rinkynooble.lostcitiesdevtool.core.Json5Text;
import net.minecraft.resources.FileToIdConverter;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.PackResources;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.server.packs.resources.ResourceManager;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Accepts comments and trailing commas in Lost Cities asset files: the half that
 * finds such files in a datapack and presents them to the loader. What a relaxed
 * file may hold, and how it is blanked, is {@link Json5Text}.
 *
 * <p><b>Scoped by path.</b> Only resources under {@code lostcities/} are touched. No
 * other mod's files, and none of Minecraft's own, are affected.
 */
public final class Json5 {

    /** The datapack folder every Lost Cities asset lives under. */
    private static final String PREFIX = "lostcities/";

    /** The namespace and folder a Lost Cities datapack registry is rooted at. */
    private static final String ROOT = "lostcities";

    /**
     * A location no pack will hold, used to read a converter's folder and extension
     * back out of it. See {@link #folderOf}.
     */
    private static final String PROBE = "lcdevprobe";

    private Json5() {
    }

    public static boolean appliesTo(ResourceLocation location) {
        return location.getPath().startsWith(PREFIX)
                && location.getPath().endsWith(Json5Text.EXT_JSON);
    }

    /** True for a resource folder that a Lost Cities datapack registry reads from. */
    public static boolean appliesToFolder(String folder) {
        return ROOT.equals(folder) || folder.startsWith(PREFIX);
    }

    /**
     * The {@code .json} location a {@code .json5} file stands in for.
     *
     * <p>Presenting the file under this name is what makes the extension work without
     * touching {@link FileToIdConverter#fileToId}, which strips a fixed number of
     * characters and would otherwise leave a trailing {@code 5} in the id. A dot is a
     * legal character in a resource path, so that would not throw: the asset would
     * simply register under a name nothing references.
     */
    public static ResourceLocation asJson(ResourceLocation json5) {
        String path = json5.getPath();
        return new ResourceLocation(json5.getNamespace(),
                path.substring(0, path.length() - Json5Text.EXT_JSON5.length()) + Json5Text.EXT_JSON);
    }

    /**
     * The folder a converter reads, or {@code null} if it does not read {@code .json}.
     *
     * <p>The folder is a private field. Rather than shadow it, which binds this mixin
     * to a mapping for a vanilla class, the converter is asked to build the file name
     * for a location that cannot exist and the answer is read back. The result is
     * {@code folder + "/" + PROBE + extension}, so both parts fall out of one public
     * call.
     */
    public static String folderOf(FileToIdConverter converter) {
        String path = converter.idToFile(new ResourceLocation(ROOT, PROBE)).getPath();
        int at = path.lastIndexOf(PROBE);
        if (at <= 0 || !Json5Text.EXT_JSON.equals(path.substring(at + PROBE.length()))) {
            return null;
        }
        return path.substring(0, at - 1);
    }

    /**
     * One folder's Lost Cities files once {@code .json5} is taken into account.
     *
     * @param files    the file each asset is read from, keyed by its name on disk
     * @param shadowed the {@code .json} files a {@code .json5} in the same pack, or a
     *                 later one, replaced
     */
    public record Listing(Map<ResourceLocation, Resource> files,
                          List<ResourceLocation> shadowed) {
    }

    /**
     * The {@code .json} files a folder holds, with the {@code .json5} ones merged in.
     *
     * <p><b>Pack order decides first.</b> Two files of one name in two packs is
     * how a datapack overrides another, and the later pack wins. Only between the
     * two extensions inside one pack does {@code .json5} win, because that is the
     * file somebody wrote by hand. The rule used to be ".json5 always wins", which
     * let a {@code .json5} in an early pack override the {@code .json} a later pack
     * put there to replace it, and then told the reader to delete one of a pair
     * that was not theirs to delete.
     *
     * <p>Here once rather than in each of the four places that list these files, so
     * the loader, the load check, the override report and the import cannot
     * disagree about which file an asset comes from.
     *
     * @param json what the manager lists for the folder with a {@code .json} filter
     */
    public static Listing merge(ResourceManager manager, String folder,
                                Map<ResourceLocation, Resource> json) {
        Map<ResourceLocation, Resource> files = new LinkedHashMap<>(json);
        List<ResourceLocation> shadowed = new ArrayList<>();
        Map<PackResources, Integer> order = new IdentityHashMap<>();
        manager.listPacks().forEach(pack -> order.putIfAbsent(pack, order.size()));
        manager.listResources(folder, path -> path.getPath().endsWith(Json5Text.EXT_JSON5))
                .forEach((location, resource) -> {
                    ResourceLocation sibling = asJson(location);
                    Resource plain = files.get(sibling);
                    if (plain != null) {
                        if (rank(order, plain) > rank(order, resource)) {
                            return;
                        }
                        files.remove(sibling);
                        shadowed.add(sibling);
                    }
                    files.put(location, resource);
                });
        return new Listing(files, shadowed);
    }

    /** Where a resource's pack sits in load order; later packs rank higher. */
    private static int rank(Map<PackResources, Integer> order, Resource resource) {
        return order.getOrDefault(resource.source(), -1);
    }

    /** A resource that yields the same file with comments and trailing commas blanked. */
    public static Resource wrap(Resource original) {
        return new Resource(original.source(), () -> relax(original.open()));
    }

    private static InputStream relax(InputStream in) throws IOException {
        String text;
        try (InputStream stream = in) {
            text = new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        }
        return new ByteArrayInputStream(
                Json5Text.sanitise(text).getBytes(StandardCharsets.UTF_8));
    }
}
