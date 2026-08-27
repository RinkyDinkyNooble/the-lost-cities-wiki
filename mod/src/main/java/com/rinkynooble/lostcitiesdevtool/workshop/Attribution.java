package com.rinkynooble.lostcitiesdevtool.workshop;

import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import com.rinkynooble.lostcitiesdevtool.mixin.PathPackResourcesAccessor;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.packs.PackResources;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.PathPackResources;
import net.minecraft.server.packs.resources.IoSupplier;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.world.level.storage.LevelResource;

import javax.annotation.Nullable;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Stream;

/**
 * Finding what a pack's author said about their work, and keeping it with it.
 *
 * <p><b>Attribution is the target, not prevention.</b> A flag that refused to import
 * an unlicensed pack would bind only the people already being careful and would
 * leave authors falsely confident, and nothing here can stop anyone reading files
 * they already have. What it can do is make the statement travel: surfaced when
 * assets are taken in, carried into whatever is compiled out of them.
 *
 * <p>Two places are looked in, in this order:
 *
 * <ul>
 *   <li><b>{@code data/<namespace>/lostcities/license.txt}</b>, which is the one
 *       that works everywhere. A pack living in {@code kubejs/data/<ns>/} has no
 *       root of its own and neither does one shipped inside a mod jar, so the root
 *       belongs to KubeJS or to the mod rather than to the assets.</li>
 *   <li><b>The pack root</b>, beside {@code pack.mcmeta}, where a repository's own
 *       file lands when the repository is zipped into a pack.</li>
 * </ul>
 *
 * <p>One statement per namespace, because a namespace is one author's asset set.
 * Per folder was considered and is answering a question nobody has: terms differ
 * between authors, not between a building and the palette it resolves through.
 *
 * <p>The text is copied into the world at import. Reading it again at export would
 * be less state and would lose the statement exactly when it matters, since a
 * workshop outlives the packs it was filled from and a pack removed from the world
 * would take its author's terms with it silently.
 */
public final class Attribution {

    private static final String DIR = "lostcitiesdevtool";
    private static final String LICENCES = "licences";

    /**
     * Root file names tried, lowest common denominator first.
     *
     * <p>A folder pack is listed rather than probed, so for that half these are only
     * compared case-insensitively. A zip pack cannot be listed through the pack API,
     * so each of these is tried against it in three casings.
     */
    private static final List<String> ROOT_NAMES = List.of(
            "license.txt", "license.md", "license",
            "licence.txt", "licence.md", "licence",
            "copying.txt", "copying");

    /** The same names in the casings an author is likely to have used. */
    private static final Set<String> SPELLINGS = spellings();

    /** What a namespace states, and where it says it. */
    public record Found(String namespace, String text, String where,
                        boolean truncated) {
    }

    /** The same, cut down to what a chat line holds. */
    public record Stated(String namespace, Licence.Summary summary, String where) {
    }

    private Attribution() {
    }

    // ------------------------------------------------------------------ finding

    /**
     * What each of these namespaces states, keyed by namespace. One absent from the
     * result states nothing.
     *
     * <p>Absent is weak evidence and is not a determination: plenty of packs state
     * their terms on a project page and ship no file. Whatever reports this has to
     * say what was looked for rather than what the absence means.
     *
     * <p><b>Asked for all of them at once on purpose.</b> The pack root is the
     * second place looked, and finding which packs supply a namespace means asking
     * every loaded pack, which lists its {@code data/} folder on each call. Once per
     * namespace on an instance holding hundreds of packs was hundreds of directory
     * listings apiece for an answer that cannot change while one import runs.
     *
     * <p>The map of packs is a local and dies with the call. Holding it in a static
     * the way {@link Assets} holds parsed JSON would be holding {@link PackResources}
     * instead, and those belong to a resource manager that a {@code /reload}
     * replaces and closes: the cache would go on referencing the closed ones until
     * something happened to call this again.
     */
    public static Map<String, Found> findAll(MinecraftServer server,
                                             Collection<String> namespaces) {
        ResourceManager manager = server.getResourceManager();
        Map<String, Found> out = new LinkedHashMap<>();
        Map<String, List<PackResources>> providers = null;
        for (String namespace : namespaces) {
            Found primary = fromData(manager, namespace);
            if (primary != null) {
                out.put(namespace, primary);
                continue;
            }
            // Built on the first namespace that needs it, and not at all where every
            // one of them states its terms in the place they are meant to.
            if (providers == null) {
                providers = providers(manager);
            }
            Found root = fromRoot(providers, namespace);
            if (root != null) {
                out.put(namespace, root);
            }
        }
        return out;
    }

    @Nullable
    private static Found fromData(ResourceManager manager, String namespace) {
        ResourceLocation id;
        try {
            id = new ResourceLocation(namespace, Licence.PATH);
        } catch (RuntimeException e) {
            // A namespace read off an asset reference, so it is whatever somebody
            // typed. One that cannot be a resource location has no primary path.
            return null;
        }
        Optional<Resource> resource = manager.getResource(id);
        if (resource.isEmpty()) {
            return null;
        }
        return read(namespace, resource.get()::open, Licence.pathIn(namespace));
    }

    @Nullable
    private static Found fromRoot(Map<String, List<PackResources>> providers,
                                  String namespace) {
        Found found = null;
        try {
            for (PackResources pack : providers.getOrDefault(namespace, List.of())) {
                Found here = rootOf(pack, namespace);
                // The last pack providing the namespace wins, which is the order
                // everything else about a namespace already resolves in.
                if (here != null) {
                    found = here;
                }
            }
        } catch (RuntimeException e) {
            LostCitiesDevTool.LOGGER.warn("could not look for a licence in the packs "
                    + "providing {}: {}", namespace, e.toString());
        }
        return found;
    }

    /**
     * Which loaded packs supply which namespace, in load order.
     *
     * <p><b>One pack that will not answer costs only itself.</b> This walks whatever
     * a modpack has loaded, and a {@link PackResources} that is not one of
     * Minecraft's own is free to throw: the vanilla two swallow their own IO errors
     * and a delegating or virtual one need not. Letting that out of the loop would
     * abandon every pack after it and quietly turn the root fallback off for the
     * whole import, reporting namespaces that do state terms as stating nothing.
     */
    private static Map<String, List<PackResources>> providers(
            ResourceManager manager) {
        Map<String, List<PackResources>> out = new LinkedHashMap<>();
        List<PackResources> loaded;
        try (Stream<PackResources> packs = manager.listPacks()) {
            loaded = packs.toList();
        } catch (RuntimeException e) {
            LostCitiesDevTool.LOGGER.warn("could not list the loaded packs: {}",
                    e.toString());
            return out;
        }
        for (PackResources pack : loaded) {
            try {
                for (String ns : pack.getNamespaces(PackType.SERVER_DATA)) {
                    out.computeIfAbsent(ns, k -> new ArrayList<>()).add(pack);
                }
            } catch (RuntimeException e) {
                LostCitiesDevTool.LOGGER.warn("pack {} would not say which "
                        + "namespaces it holds: {}", packId(pack), e.toString());
            }
        }
        return out;
    }

    /** A pack's id, for a message, where asking the pack anything may be broken. */
    private static String packId(PackResources pack) {
        try {
            return pack.packId();
        } catch (RuntimeException e) {
            return pack.getClass().getSimpleName();
        }
    }

    @Nullable
    private static Found rootOf(PackResources pack, String namespace) {
        Path root = folderOf(pack);
        if (root != null) {
            return fromFolder(pack, root, namespace);
        }
        for (String name : SPELLINGS) {
            IoSupplier<InputStream> open;
            try {
                open = pack.getRootResource(name);
            } catch (RuntimeException e) {
                // getRootResource validates path segments on some pack shapes and
                // throws on an uppercase one rather than answering no.
                continue;
            }
            if (open != null) {
                Found found = read(namespace, open::get,
                        pack.packId() + "/" + name);
                if (found != null) {
                    return found;
                }
            }
        }
        return null;
    }

    /** The folder a loose pack sits in, or null where it is not one. */
    @Nullable
    private static Path folderOf(PackResources pack) {
        if (!(pack instanceof PathPackResources)) {
            return null;
        }
        try {
            return ((PathPackResourcesAccessor) pack).lostcitiesdevtool$root();
        } catch (RuntimeException e) {
            return null;
        }
    }

    @Nullable
    private static Found fromFolder(PackResources pack, Path root, String namespace) {
        // Grouped by which name it is before any of them is read, because the
        // listing arrives in whatever order the filesystem keeps. Taking the first
        // entry that matched anything would let NTFS's alphabetical order put
        // COPYING ahead of LICENSE.txt, which is the reverse of the order these are
        // written in, and would make one pack answer differently on two machines.
        Map<String, List<Path>> byName = new LinkedHashMap<>();
        try (Stream<Path> listing = Files.list(root)) {
            for (Path file : listing.toList()) {
                String name = file.getFileName().toString().toLowerCase(Locale.ROOT);
                if (Files.isRegularFile(file) && ROOT_NAMES.contains(name)) {
                    byName.computeIfAbsent(name, k -> new ArrayList<>()).add(file);
                }
            }
        } catch (IOException | RuntimeException e) {
            LostCitiesDevTool.LOGGER.warn("could not list the root of pack {}: {}",
                    pack.packId(), e.toString());
            return null;
        }
        for (String name : ROOT_NAMES) {
            for (Path file : byName.getOrDefault(name, List.of())) {
                // Past an empty or unreadable one rather than stopping there. A
                // zero byte COPYING beside a real LICENSE.txt would otherwise
                // report the pack as stating nothing.
                Found found = read(namespace, () -> Files.newInputStream(file),
                        pack.packId() + "/" + file.getFileName());
                if (found != null) {
                    return found;
                }
            }
        }
        return null;
    }

    /**
     * Each root name in three casings.
     *
     * <p>Only for a pack that cannot be listed, which is a zip. A folder pack's root
     * is read and matched case-insensitively instead, so it finds spellings no list
     * like this would think of.
     */
    private static Set<String> spellings() {
        Set<String> out = new LinkedHashSet<>();
        for (String name : ROOT_NAMES) {
            int dot = name.indexOf('.');
            String stem = dot < 0 ? name : name.substring(0, dot);
            String ext = dot < 0 ? "" : name.substring(dot);
            out.add(name);
            out.add(stem.toUpperCase(Locale.ROOT) + ext);
            out.add(name.toUpperCase(Locale.ROOT));
        }
        return out;
    }

    /**
     * The text, up to the cap.
     *
     * <p>One byte past the cap is read so that stopping there can be reported rather
     * than looking like the whole file. Cutting UTF-8 at a byte can split a
     * character, which costs one replacement glyph at the very end of text nothing
     * reads to the end of.
     */
    @Nullable
    private static Found read(String namespace, Opener opener, String where) {
        try (InputStream in = opener.open()) {
            byte[] bytes = in.readNBytes(Licence.MAX_BYTES + 1);
            boolean truncated = bytes.length > Licence.MAX_BYTES;
            int length = Math.min(bytes.length, Licence.MAX_BYTES);
            String text = new String(bytes, 0, length, StandardCharsets.UTF_8);
            return text.isBlank() ? null
                    : new Found(namespace, text, where, truncated);
        } catch (IOException | RuntimeException e) {
            LostCitiesDevTool.LOGGER.warn("could not read the licence at {}: {}",
                    where, e.toString());
            return null;
        }
    }

    @FunctionalInterface
    private interface Opener {
        InputStream open() throws IOException;
    }

    // ------------------------------------------------------------------ keeping

    public static Path root(MinecraftServer server) {
        return server.getWorldPath(LevelResource.ROOT).resolve(DIR)
                .resolve(LICENCES).toAbsolutePath().normalize();
    }

    /**
     * Copy what a namespace states into the world, or forget it where it states
     * nothing.
     *
     * <p>Both halves matter. Importing a pack that has since dropped its licence
     * over one that had it would otherwise leave the old text behind, and the next
     * export would carry terms the pack no longer claims.
     */
    public static void keep(MinecraftServer server, String namespace,
                            @Nullable Found found) throws IOException {
        Path file = fileOf(server, namespace);
        if (file == null) {
            return;
        }
        if (found == null) {
            Files.deleteIfExists(file);
            return;
        }
        Files.createDirectories(file.getParent());
        Files.writeString(file, found.text(), StandardCharsets.UTF_8);
    }

    /** What is kept for these namespaces, by namespace, skipping those with none. */
    public static Map<String, String> kept(MinecraftServer server,
                                           Collection<String> namespaces)
            throws IOException {
        Map<String, String> out = new TreeMap<>();
        for (String namespace : namespaces) {
            Path file = fileOf(server, namespace);
            if (file != null && Files.isRegularFile(file)) {
                String text = Files.readString(file, StandardCharsets.UTF_8);
                if (!text.isBlank()) {
                    out.put(namespace, text);
                }
            }
        }
        return out;
    }

    /**
     * Drop every kept statement, for a workshop being emptied.
     *
     * <p><b>Cannot fail the wipe.</b> A wipe calls this after it has emptied every
     * plot, deleted their settings and reset the grown rows, and before it repaints.
     * Anything thrown from here leaves that half done and reports the whole clear as
     * failed, which is a bad trade for a bookkeeping file: a locked file, a
     * read-only folder or a directory somebody put in here would each do it. What is
     * left behind instead is inert, since an export carries a statement only for a
     * namespace some plot still names, and a wipe has just removed every plot.
     *
     * <p>Regular files only, for the same reason and because this has no business
     * deleting a folder somebody made.
     */
    public static void forget(MinecraftServer server) {
        Path root = root(server);
        if (!Files.isDirectory(root)) {
            return;
        }
        List<Path> files;
        try (Stream<Path> listing = Files.list(root)) {
            files = listing.filter(Files::isRegularFile).toList();
        } catch (IOException | RuntimeException e) {
            LostCitiesDevTool.LOGGER.warn("could not list the kept licences: {}",
                    e.toString());
            return;
        }
        for (Path file : files) {
            try {
                Files.deleteIfExists(file);
            } catch (IOException | RuntimeException e) {
                LostCitiesDevTool.LOGGER.warn("could not drop the kept licence {}: "
                        + "{}", file.getFileName(), e.toString());
            }
        }
    }

    /**
     * Where one namespace's text is kept, or null for a name that cannot be one.
     *
     * <p>The namespace becomes a file name, so it is checked rather than trusted.
     * It arrives from an asset reference in somebody else's pack, and a name holding
     * a separator would write outside the folder.
     */
    @Nullable
    private static Path fileOf(MinecraftServer server, String namespace) {
        if (namespace.isEmpty() || !namespace.matches("[a-z0-9._-]+")
                || namespace.contains("..")) {
            return null;
        }
        return root(server).resolve(namespace + ".txt");
    }
}
