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
:   The system that decides what terrain goes in each chunk. Lost Cities ships none: its `lostcities:lostcity` dimension uses vanilla noise terrain with the overworld settings, and the mod adds cities to it as a feature. [code review](examples/claim-tests.md#lw-1){.v .v-c}

Profile
:   A Lost Cities config file, not a datapack file, that picks a world style and sets the generation settings: 131 of them on 7.4.12, 160 on 7.5 and later. See [How It All Connects](getting-started/how-it-connects.md). [code review](examples/claim-tests.md#hic-1){.v .v-c}

World Style
:   The top-level datapack asset a profile points at. Decides which city styles can appear and where. Full reference: [World Style](reference/worldstyle.md). [code review](examples/claim-tests.md#ref-1){.v .v-c}

City Style
:   A theme, building settings, street settings, palettes and more, bundled together. Full reference: [City Style](reference/citystyle.md). [code review](examples/claim-tests.md#ref-1){.v .v-c}

Style
:   A different asset from a City Style, despite the name. A Style is only a stack of palettes, and it decides what a **character** means. A City Style names one in its `style` key, and a World Style names another in `outsidestyle` for everything that is not a city chunk. A character defined in one and not the other resolves in half the world. Full reference: [Style](reference/style.md). [code review](examples/claim-tests.md#sph-3){.v .v-c}

Part
:   One 16 by 16 block of building, written as layers of characters. Buildings, streets, highways and railways are all assembled from parts. Full reference: [Part](reference/part.md). [code review](examples/claim-tests.md#ref-1){.v .v-c}

Palette
:   The mapping from a character to a block. Parts hold characters, palettes turn them into blocks, and several palettes merge into the one a part actually sees. Full reference: [Palette](reference/palette.md). [game test](examples/claim-tests.md#pal-1){.v .v-g}

Matcher
:   A small filter object built from `if_all`, `if_any` and `excluding`, used wherever the mod limits something to certain biomes or blocks. See [Matchers](concepts/matchers.md). [game test](examples/claim-tests.md#mat-1){.v .v-g}

Codec
:   The mod's internal parsing logic for a JSON file type. Nothing you need to touch, mentioned because it is where this wiki's key tables come from. [code review](examples/claim-tests.md#ref-1){.v .v-c}

Forge
:   The mod loader this wiki's target version, 7.4.12, runs on. Lost Cities moved to NeoForge at 8.x, and both lines are covered here. See [Versions](versions/index.md). [code review](examples/claim-tests.md#key-1){.v .v-c}

NeoForge
:   The mod loader that succeeded Forge on Minecraft 1.20.2 and later. Lost Cities 8.x, 9.x and 10.x are NeoForge only. The datapack format is the same on both, which is why one set of reference pages covers them. [game test](examples/claim-tests.md#neo-1){.v .v-g}

KubeJS
:   A scripting mod that can supply datapack content, Lost Cities assets included, from a `kubejs/data/` folder or from JavaScript. See [KubeJS Integration](advanced/kubejs.md). [game test](examples/claim-tests.md#kjs-2){.v .v-g}
