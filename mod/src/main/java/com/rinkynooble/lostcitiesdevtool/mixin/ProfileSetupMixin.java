package com.rinkynooble.lostcitiesdevtool.mixin;

import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.json5.Json5;
import com.rinkynooble.lostcitiesdevtool.json5.Json5Overrides;
import mcjty.lostcities.config.ProfileSetup;
import org.apache.commons.io.FileUtils;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Feature 2.2 for {@code config/lostcities/profiles}, which the resource manager never
 * sees.
 *
 * <p>Profiles are plain files read with {@code File.listFiles} during mod
 * construction, filtered on {@code .json}, so the datapack hook cannot reach them.
 * They are also the files most worth writing as JSON5: a profile is the longest
 * hand-edited file in a pack and the one where a note about why a value was chosen is
 * most useful.
 *
 * <p>Two redirects, both narrow. The listing gains {@code .json5} files and drops any
 * {@code .json} they shadow. The read is relaxed, on the same rule the datapack side
 * uses: a {@code .json5} always, a {@code .json} only while
 * {@code acceptCommentsAndTrailingCommas} is on.
 *
 * <p>Nothing downstream needs changing. Lost Cities derives the profile name with
 * {@code getName().split("\\.")[0]}, which yields the same name from either
 * extension.
 *
 * <p>This runs before configs are loaded, so both toggles read as their defaults on
 * the pass that matters and a change to either takes effect at the next launch.
 */
@Mixin(value = ProfileSetup.class, remap = false)
public abstract class ProfileSetupMixin {

    @Redirect(method = "readProfiles",
            at = @At(value = "INVOKE",
                    target = "Ljava/io/File;listFiles(Ljava/io/FilenameFilter;)[Ljava/io/File;"))
    private static File[] lostcitiesdevtool$listJson5Profiles(File directory,
                                                              FilenameFilter filter) {
        File[] json = directory.listFiles(filter);
        if (!Config.on(Config.INSTANCE.acceptJson5Extension, true)) {
            return json;
        }
        File[] json5 = directory.listFiles(
                (dir, name) -> name.endsWith(Json5.EXT_JSON5));
        if (json5 == null || json5.length == 0) {
            return json;
        }

        Set<String> shadowing = new LinkedHashSet<>();
        for (File file : json5) {
            shadowing.add(Json5.baseName(file.getName()));
        }

        List<File> chosen = new ArrayList<>(List.of(json5));
        List<String> overridden = new ArrayList<>();
        if (json != null) {
            for (File file : json) {
                if (shadowing.contains(Json5.baseName(file.getName()))) {
                    overridden.add("config/lostcities/profiles/"
                            + Json5.baseName(file.getName()) + Json5.EXT_JSON5);
                } else {
                    chosen.add(file);
                }
            }
        }
        // Recorded, not reported. This runs before any config file is read, so a
        // warning raised here could not honour the setting that silences it.
        // ModEvents logs it at common setup instead.
        Json5Overrides.setProfiles(overridden);
        return chosen.toArray(new File[0]);
    }

    @Redirect(method = "readProfiles",
            at = @At(value = "INVOKE",
                    target = "Lorg/apache/commons/io/FileUtils;readFileToString"
                            + "(Ljava/io/File;Ljava/lang/String;)Ljava/lang/String;"))
    private static String lostcitiesdevtool$relaxProfile(File file, String charset)
            throws IOException {
        String raw = FileUtils.readFileToString(file, charset);
        boolean json5 = file.getName().endsWith(Json5.EXT_JSON5);
        if (json5 || Config.on(Config.INSTANCE.acceptCommentsAndTrailingCommas, true)) {
            return Json5.sanitise(raw);
        }
        return raw;
    }
}
