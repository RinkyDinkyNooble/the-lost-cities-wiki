# Glossary

Quick definitions for terms used across this wiki. Click here from any page, then go back.

Datapack
:   A folder (or zip) of JSON files that adds or changes game content, no code required. Minecraft loads these itself. Lost Cities content is written as datapack JSON.

Registry
:   Minecraft's internal list of "things that exist," like all blocks, all items, or (relevant here) all world styles. Adding a JSON file in the right folder registers a new entry.

Resource location
:   A name in the form `namespace:path`, like `minecraft:stone` or `lostcities:standard`. This is how Minecraft (and Lost Cities) refers to any registered thing. See [Namespaces](getting-started/namespaces.md) for why this matters.

Namespace
:   The part before the colon in a resource location. Usually your mod or pack's ID. See [Namespaces](getting-started/namespaces.md).

Dimension
:   A separate "world" in the Minecraft sense, like the Overworld, the Nether, or a custom Lost Cities dimension. Has its own terrain generation rules.

Biome
:   A region type (desert, plains, ocean, and so on). Lost Cities can hook into specific biomes without needing its own dimension.

Chunk
:   A 16×16 block column, the unit Minecraft generates and loads terrain in. Lost Cities parts are sized to fit exactly one chunk footprint.

World generation feature
:   A piece of terrain generation logic Minecraft can inject into biomes, like ore veins or trees. Lost Cities can hook into worlds this way instead of using a dedicated dimension.

Chunk generator
:   The system that decides what terrain goes in each chunk. Lost Cities ships its own custom one (`lostcities:lostcity`) for its dedicated dimension.

Profile
:   A Lost Cities config file (not a datapack file) that picks a world style and sets ~100 generation behavior knobs. See [How It All Connects](getting-started/how-it-connects.md).

World Style
:   The top-level datapack asset a profile points to. Decides which city styles can appear and where. Full reference: coming soon.

City Style
:   A "theme," building settings, street settings, palettes, and more, bundled together. Full reference: coming soon.

Codec
:   The mod's internal parsing logic for a JSON file type. Not something you need to touch, mentioned here only because it's where this wiki's technical accuracy comes from.

Forge
:   The mod loader Lost Cities and this wiki's target version run on.

KubeJS
:   A scripting mod that can generate datapack-style content (including Lost Cities assets) from JavaScript instead of hand-written JSON files.
