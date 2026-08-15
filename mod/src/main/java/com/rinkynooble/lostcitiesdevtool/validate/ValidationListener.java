package com.rinkynooble.lostcitiesdevtool.validate;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.rinkynooble.lostcitiesdevtool.Config;
import com.rinkynooble.lostcitiesdevtool.json5.Json5;
import com.rinkynooble.lostcitiesdevtool.LostCitiesDevTool;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimplePreparableReloadListener;
import net.minecraft.util.profiling.ProfilerFiller;

import java.io.BufferedReader;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Reads every Lost Cities asset file when datapacks load, and reports what will fail
 * before a chunk is generated.
 *
 * <p>The mod discovers these faults during generation, one chunk at a time, often
 * thousands of times over and with the wrong coordinates attached. Everything checked
 * here is decidable from a single file, so it can be said once, at load, with a file
 * name and a line number.
 */
public class ValidationListener extends SimplePreparableReloadListener<List<Finding>> {

    /** The asset folders worth reading. Others carry no rule this can check. */
    private static final List<String> KINDS = List.of("buildings", "palettes", "parts");

    @Override
    protected List<Finding> prepare(ResourceManager manager, ProfilerFiller profiler) {
        List<Finding> findings = new ArrayList<>();
        if (!Config.INSTANCE.validateOnLoad.get()) {
            return findings;
        }

        boolean json5 = Config.on(Config.INSTANCE.acceptJson5Extension, true);
        for (String kind : KINDS) {
            String folder = "lostcities/" + kind;
            // Keyed by the name on disk rather than the name the loader sees, so a
            // finding names the file the author has to open.
            Map<ResourceLocation, Resource> chosen = new LinkedHashMap<>(
                    manager.listResources(folder,
                            loc -> loc.getPath().endsWith(Json5.EXT_JSON)));
            if (json5) {
                manager.listResources(folder,
                        loc -> loc.getPath().endsWith(Json5.EXT_JSON5))
                        .forEach((loc, resource) -> {
                            // Same precedence the loader applies, so a shadowed .json
                            // is not reported for faults nothing will ever hit.
                            chosen.remove(Json5.asJson(loc));
                            chosen.put(loc, resource);
                        });
            }
            for (Map.Entry<ResourceLocation, Resource> entry : chosen.entrySet()) {
                readOne(findings, kind, entry.getKey(), entry.getValue());
            }
        }
        return findings;
    }

    private void readOne(List<Finding> findings, String kind, ResourceLocation id,
                         Resource resource) {
        String file = id.getNamespace() + ":" + id.getPath();
        String raw;
        try (BufferedReader reader = resource.openAsReader()) {
            raw = reader.lines().reduce("", (a, b) -> a.isEmpty() ? b : a + "\n" + b);
        } catch (Exception e) {
            findings.add(Finding.error(file, 0, "cannot be read: " + e.getMessage(),
                    "Check the file exists and is readable"));
            return;
        }
        JsonObject json;
        try {
            // Parse the relaxed form, since that is what the loader will see. Blanking
            // preserves offsets, so a line number found here still matches the file on
            // disk, comments and all.
            boolean relax = id.getPath().endsWith(Json5.EXT_JSON5)
                    || Config.on(Config.INSTANCE.acceptCommentsAndTrailingCommas, true);
            String forParsing = relax ? Json5.sanitise(raw) : raw;
            json = JsonParser.parseString(forParsing).getAsJsonObject();
        } catch (Exception e) {
            // The registry loader reports this too, but without saying which rule of
            // JSON was broken in a way an author can act on.
            findings.add(Finding.error(file, 0, "not valid JSON: " + e.getMessage(),
                    "A trailing comma and a comment are both rejected by strict JSON"));
            return;
        }
        try {
            findings.addAll(AssetValidator.validate(file, kind, json, raw));
        } catch (Exception e) {
            LostCitiesDevTool.LOGGER.error("DevTool could not check {}: {}", file, e.toString());
        }
    }

    @Override
    protected void apply(List<Finding> findings, ResourceManager manager,
                         ProfilerFiller profiler) {
        if (findings.isEmpty()) {
            if (Config.INSTANCE.validateOnLoad.get()) {
                LostCitiesDevTool.LOGGER.info(
                        "Lost Cities assets checked, nothing to report");
            }
            return;
        }

        long errors = findings.stream()
                .filter(f -> f.severity() == Finding.Severity.ERROR).count();
        long warnings = findings.size() - errors;

        // Grouped by file, because an author fixes one file at a time.
        Map<String, List<Finding>> byFile = new LinkedHashMap<>();
        for (Finding f : findings) {
            byFile.computeIfAbsent(f.file(), k -> new ArrayList<>()).add(f);
        }

        StringBuilder sb = new StringBuilder();
        sb.append("Lost Cities asset check: ")
          .append(errors).append(errors == 1 ? " error, " : " errors, ")
          .append(warnings).append(warnings == 1 ? " warning" : " warnings");
        for (Map.Entry<String, List<Finding>> e : byFile.entrySet()) {
            for (Finding f : e.getValue()) {
                sb.append("\n  ").append(f.severity()).append("  ")
                  .append(f.location()).append("  ").append(f.message())
                  .append("\n         ").append(f.fix());
            }
        }
        sb.append("\n  Every one of these fails during chunk generation instead, "
                + "once per affected chunk.");

        if (errors > 0) {
            LostCitiesDevTool.LOGGER.error(sb.toString());
        } else {
            LostCitiesDevTool.LOGGER.warn(sb.toString());
        }
    }
}
