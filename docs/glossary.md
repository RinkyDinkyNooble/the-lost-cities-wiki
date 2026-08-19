---
claims: verified
---

# Glossary

Quick definitions for terms used across this wiki. Click here from any page, then go back. <!-- noclaim -->

Datapack
:   A folder or zip of JSON files that adds or changes game content, no code required. Minecraft loads these itself. Lost Cities content is written as datapack JSON. <!-- noclaim -->

Registry
:   Minecraft's internal list of things that exist: all blocks, all items, or here, all world styles. Adding a JSON file in the right folder registers a new entry. <!-- noclaim -->

Resource location
:   A name in the form `namespace:path`, such as `minecraft:stone` or `lostcities:standard`. This is how Minecraft and Lost Cities refer to any registered thing. See [Namespaces](getting-started/namespaces.md) for why it matters. [code review](examples/claim-tests.md#ns-1){.v .v-c}

Namespace
:   The part before the colon in a resource location, usually your mod or pack's ID. In a Lost Cities reference, leaving it off means `lostcities:` rather than "whatever pack this file is in". See [Namespaces](getting-started/namespaces.md). [code review](examples/claim-tests.md#ns-3){.v .v-c}

Dimension
:   A separate world in the Minecraft sense: the Overworld, the Nether, or a custom Lost Cities dimension. Each has its own terrain generation rules. <!-- noclaim -->

Biome
:   A region type such as desert, plains or ocean. Lost Cities can hook into specific biomes without needing its own dimension. [code review](examples/claim-tests.md#hic-4){.v .v-c}

Chunk
:   A 16 by 16 block column, the unit Minecraft generates and loads terrain in. Most Lost Cities parts fill exactly one chunk footprint, though a building front is deliberately a narrower strip. [code review](examples/claim-tests.md#ref-2){.v .v-c}

World generation feature
:   A piece of terrain generation logic Minecraft can inject into biomes, like ore veins or trees. Lost Cities reaches ordinary worlds this way instead of through a dedicated dimension. [code review](examples/claim-tests.md#hic-4){.v .v-c}

Chunk generator
:   The system that decides what terrain goes in each chunk. Lost Cities ships its own for its dedicated dimension, `lostcities:lostcity`. [code review](examples/claim-tests.md#hic-3){.v .v-c}

Profile
:   A Lost Cities config file, not a datapack file, that picks a world style and sets 131 generation settings. See [How It All Connects](getting-started/how-it-connects.md). [code review](examples/claim-tests.md#hic-1){.v .v-c}

World Style
:   The top-level datapack asset a profile points at. Decides which city styles can appear and where. Full reference: [World Style](reference/worldstyle.md). [code review](examples/claim-tests.md#ref-1){.v .v-c}

City Style
:   A theme, building settings, street settings, palettes and more, bundled together. Full reference: [City Style](reference/citystyle.md). [code review](examples/claim-tests.md#ref-1){.v .v-c}

Codec
:   The mod's internal parsing logic for a JSON file type. Nothing you need to touch, mentioned because it is where this wiki's key tables come from. [code review](examples/claim-tests.md#ref-1){.v .v-c}

Forge
:   The mod loader Lost Cities and this wiki's target version run on. <!-- noclaim -->

KubeJS
:   A scripting mod that can supply datapack content, Lost Cities assets included, from a `kubejs/data/` folder or from JavaScript. See [KubeJS Integration](advanced/kubejs.md). [game test](examples/claim-tests.md#kjs-2){.v .v-g}
