package com.rinkynooble.lostcitiesdevtool.command;

import mcjty.lostcities.setup.CustomRegistries;
import mcjty.lostcities.worldgen.lost.cityassets.AssetRegistries;
import mcjty.lostcities.worldgen.lost.cityassets.Building;
import mcjty.lostcities.worldgen.lost.cityassets.BuildingPart;
import mcjty.lostcities.worldgen.lost.cityassets.CompiledPalette;
import mcjty.lostcities.worldgen.lost.cityassets.Palette;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.function.BiFunction;
import java.util.function.Function;

/**
 * Every palette an author can write, found by name rather than by standing on it.
 *
 * <p>The chunk report answers what a character became <em>here</em>. That is the wrong
 * question while editing a file, because the chunk in front of the caller usually has
 * nothing to do with the pack being written, and where no city generated there is no
 * pack palette in play at all. Asking a named asset directly answers it from anywhere.
 *
 * <p>Three registries are searched, because a palette is not only a
 * {@code palettes/} file. A building and a part may each carry one inline, and that
 * inline palette is where a character is most often defined and least often findable.
 *
 * <p><b>Built one asset at a time, deliberately.</b> {@code AssetRegistries.loadAll}
 * constructs a whole registry in one loop with no guard, so a single asset that throws
 * stops it and leaves every asset after it unbuilt. Lost Cities 7.4.12 ships one that
 * does: {@code lostcities:bricks_desert_redsand} carries
 * {@code "block": "minecraft:red_sandstone@2"}, a 1.12 style {@code block@meta} string
 * that is not a legal resource location on 1.20. Reading each id separately costs one
 * broken asset its own entry in the answer instead of costing the answer.
 */
public final class PaletteLookup {

    /** One place a character can be defined, with the palette that defines it. */
    public record Source(String kind, ResourceLocation id, CompiledPalette palette) {
        public String label() {
            return kind + " " + id;
        }
    }

    /** An asset that could not be built, and why. */
    public record Unreadable(String kind, ResourceLocation id, String reason) {
    }

    /** The result of a scan: what was read, and what was not. */
    public record Scan(List<Source> sources, List<Unreadable> unreadable) {
    }

    private PaletteLookup() {
    }

    /** Every palette in the world's assets, named, with the failures kept. */
    public static Scan scan(ServerLevel level) {
        List<Source> sources = new ArrayList<>();
        List<Unreadable> unreadable = new ArrayList<>();

        collect(level, sources, unreadable, "palette",
                CustomRegistries.PALETTE_REGISTRY_KEY,
                (lvl, id) -> AssetRegistries.PALETTES.get(lvl, id),
                palette -> palette);
        collect(level, sources, unreadable, "part",
                CustomRegistries.PART_REGISTRY_KEY,
                (lvl, id) -> AssetRegistries.PARTS.get(lvl, id),
                part -> part.getLocalPalette(level));
        collect(level, sources, unreadable, "building",
                CustomRegistries.BUILDING_REGISTRY_KEY,
                (lvl, id) -> AssetRegistries.BUILDINGS.get(lvl, id),
                building -> building.getLocalPalette(level));

        sources.sort(Comparator.comparing((Source s) -> s.kind())
                .thenComparing(s -> s.id().toString()));
        return new Scan(sources, unreadable);
    }

    /** Ids only, for tab completion. A broken asset is simply not offered. */
    public static List<String> ids(ServerLevel level) {
        Set<String> ids = new LinkedHashSet<>();
        for (Source source : scan(level).sources()) {
            ids.add(source.id().toString());
        }
        return new ArrayList<>(ids);
    }

    /**
     * Every source carrying this id.
     *
     * <p>More than one kind can hold the same name, and a pack that names a building
     * and its part alike is normal, so the id is not narrowed to one answer.
     */
    public static List<Source> withId(List<Source> sources, ResourceLocation id) {
        List<Source> matches = new ArrayList<>();
        for (Source source : sources) {
            if (source.id().equals(id)) {
                matches.add(source);
            }
        }
        return matches;
    }

    /**
     * What a character resolves to in one palette, or null if it defines nothing.
     *
     * <p>A palette compiled on its own cannot follow a {@code frompalette} alias into
     * another file, and a character carrying only a mob, loot or tag resolves to no
     * block at all. Both throw rather than return empty, so both are reported as
     * "defined, but not as a block" rather than as a failure of the lookup.
     */
    public static Set<BlockState> blocksFor(Source source, char c) {
        CompiledPalette palette = source.palette();
        if (palette == null || !palette.isDefined(c)) {
            return null;
        }
        try {
            Set<BlockState> all = palette.getAll(c);
            return all == null ? Set.of() : all;
        } catch (Exception e) {
            return Set.of();
        }
    }

    /** Every character in one palette that produces this block. */
    public static List<Character> charsFor(Source source, String blockId) {
        List<Character> found = new ArrayList<>();
        CompiledPalette palette = source.palette();
        if (palette == null) {
            return found;
        }
        for (Character c : palette.getCharacters()) {
            if (c == null) {
                continue;
            }
            Set<BlockState> all;
            try {
                all = palette.getAll(c);
            } catch (Exception e) {
                continue;
            }
            if (all == null) {
                continue;
            }
            for (BlockState state : all) {
                if (state != null && blockId.equals(String.valueOf(
                        BuiltInRegistries.BLOCK.getKey(state.getBlock())))) {
                    found.add(c);
                    break;
                }
            }
        }
        return found;
    }

    /** How many blocks a character can produce, for the "one of N" wording. */
    public static int weight(Source source, char c) {
        Set<BlockState> all = blocksFor(source, c);
        return all == null ? 0 : all.size();
    }

    /**
     * Walks one registry, building each asset alone.
     *
     * <p>The ids come from the datapack registry rather than from whatever the asset
     * cache happens to hold, so the answer does not depend on where the caller has
     * walked or what generation has touched.
     */
    private static <A, R> void collect(ServerLevel level, List<Source> sources,
                                       List<Unreadable> unreadable, String kind,
                                       ResourceKey<Registry<R>> registryKey,
                                       BiFunction<ServerLevel, ResourceLocation, A> read,
                                       Function<A, Palette> toPalette) {
        Registry<R> registry;
        try {
            registry = level.registryAccess().registryOrThrow(registryKey);
        } catch (Exception e) {
            unreadable.add(new Unreadable(kind, null, "the registry is not loaded"));
            return;
        }
        for (ResourceLocation id : registry.keySet()) {
            try {
                A asset = read.apply(level, id);
                if (asset == null) {
                    continue;
                }
                Palette palette = toPalette.apply(asset);
                if (palette == null) {
                    continue;
                }
                sources.add(new Source(kind, id, new CompiledPalette(palette)));
            } catch (Exception e) {
                unreadable.add(new Unreadable(kind, id,
                        e.getClass().getSimpleName()
                                + (e.getMessage() == null ? "" : ": " + e.getMessage())));
            }
        }
    }
}
