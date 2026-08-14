package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import mcjty.lostcities.worldgen.LostCitySphereFeature;
import mcjty.lostcities.worldgen.LostCityTerrainFeature;
import mcjty.lostcities.worldgen.gen.Spheres;
import net.minecraft.server.level.WorldGenRegion;
import net.minecraft.world.level.chunk.ChunkAccess;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Feature 1.1. Gives the sphere feature the catch the terrain feature already has.
 *
 * <p>{@code LostCityFeature} wraps its call to {@code LostCityTerrainFeature.generate}
 * in a {@code catch (Exception)}, which is what makes a mistake in a datapack
 * survivable: the chunk fails, a line is logged, and generation moves on.
 *
 * <p>{@code LostCitySphereFeature} contains no {@code try} anywhere in the class. It
 * reaches {@code BuildingInfo} through {@code Spheres.generateSpheres} and
 * {@code ChunkFixer.generateVines}, and building that info is what evaluates a
 * building's part conditions. So the same fault escapes to vanilla's feature placer
 * and becomes a {@code ReportedException: Feature placement}.
 *
 * <p>The sphere feature only does this work on {@code landscapeType} spheres,
 * cavernspheres or space, which is why the difference goes unnoticed on a default
 * profile.
 *
 * <p>Measured on Lost Cities 7.4.12 with one building whose levels were not fully
 * covered: {@code default} gave 35 caught faults and none escaping, {@code spheres}
 * gave 18 caught and 21 escaping, and the dedicated server shut down.
 *
 * <p>Redirecting the {@code generateSpheres} call rather than wrapping the whole
 * method is deliberate. It puts the guard around exactly the work the terrain
 * feature guards, and leaves {@code getDimensionInfo} unguarded in both features, so
 * a profile pointing at a missing world style still fails loudly rather than being
 * silently swallowed here.
 *
 * <p>This changes nothing about what generates. A chunk that would have failed still
 * fails, and is left in the same partial state. It changes only whether the failure
 * takes the server with it.
 */
@Mixin(LostCitySphereFeature.class)
public abstract class LostCitySphereFeatureMixin {

    /**
     * {@code remap = false} on both the target method and the injection point.
     *
     * <p>Neither name belongs to Minecraft. {@code LostCitySphereFeature} overrides a
     * Minecraft method, so in a shipped jar the override already carries the SRG name
     * {@code m_142674_}, and {@code Spheres.generateSpheres} is Lost Cities' own
     * method which is never remapped. Letting the annotation processor try to remap
     * either one fails, because there is no mapping to find.
     *
     * <p>The consequence is that this mixin targets a shipped Lost Cities jar. That
     * is the only environment it is meant for, and the acceptance test runs against
     * one.
     */
    @Redirect(
            method = "m_142674_(Lnet/minecraft/world/level/levelgen/feature/FeaturePlaceContext;)Z",
            remap = false,
            at = @At(
                    value = "INVOKE",
                    remap = false,
                    target = "Lmcjty/lostcities/worldgen/gen/Spheres;generateSpheres("
                            + "Lmcjty/lostcities/worldgen/LostCityTerrainFeature;"
                            + "Lnet/minecraft/server/level/WorldGenRegion;"
                            + "Lnet/minecraft/world/level/chunk/ChunkAccess;)V"))
    private void lostcitiesdevtool$guardSphereGeneration(
            LostCityTerrainFeature feature, WorldGenRegion region, ChunkAccess chunk) {

        if (!Config.INSTANCE.catchSphereFeatureErrors.get()) {
            Spheres.generateSpheres(feature, region, chunk);
            return;
        }

        try {
            Spheres.generateSpheres(feature, region, chunk);
        } catch (Exception e) {
            // Same shape as the message LostCityFeature logs, with 'sphere' added so
            // the two paths can be told apart in a log.
            LostCitiesDevTool.LOGGER.error("Error generating sphere chunk {},{}: {}",
                    chunk.getPos().x, chunk.getPos().z, e.getMessage());
            e.printStackTrace();
        }
    }
}
