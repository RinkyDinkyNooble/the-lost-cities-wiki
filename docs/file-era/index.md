---
claims: verified
---

# The File-Asset Era

!!! tip "TL;DR"
    Lost Cities 1.0.1 through 5.0.4 does not read datapacks. Content lives in a few combined JSON files inside the jar, you add your own through one `userassets.json`, and the config is Forge's old `.cfg`. Minecraft 1.12.2 is the popular version in this era. [code review](../examples/claim-tests.md#f12-1){.v .v-c}

The rest of this wiki documents the datapack system, which arrived in 5.3.29. On an earlier build none of those files are ever read. These three pages cover what the system was instead. [code review](../examples/claim-tests.md#f12-1){.v .v-c}

!!! info "Read from the jar, not yet run"
    Everything here comes from `lostcities-1.12-2.0.22.jar`, the newest build for Minecraft 1.12.2. None of it has been generated in a world. Forge 1.12.2 boots through LaunchWrapper, which needs the system class loader to be a `URLClassLoader`, and Java 9 stopped making it one, so the rig waits on a Java 8 runtime. Where a page here says a thing happens, it means the code says so. [code review](../examples/claim-tests.md#f12-1){.v .v-c}

## Which versions

| Mod versions | Minecraft | Asset system |
|---|---|---|
| 1.0.1 through 5.0.4 | 1.11.2 through 1.18 | File |
| 5.3.29 and later | 1.18 and later | Datapack |
[code review](../examples/claim-tests.md#f12-1){.v .v-c}

The change lands **inside** the Minecraft 1.18 line. 5.0.4 is a file build and 5.3.29 is a datapack build, and both are labelled 1.18, so the mod version decides rather than the Minecraft version. [code review](../examples/claim-tests.md#f12-1){.v .v-c}

For Minecraft 1.12.2 the builds are `1.12-1.0.1`, `1.12-1.0.2` and `1.12-2.0.22`. The last is the newest and is what these pages describe. [code review](../examples/claim-tests.md#f12-1){.v .v-c}

## How to tell in ten seconds

Open the jar and look for a folder. [code review](../examples/claim-tests.md#f12-1){.v .v-c}

| What you find | Era |
|---|---|
| `assets/lostcities/citydata/` holding `library.json`, `palette.json` and similar | File |
| `data/lostcities/lostcities/` holding `buildings/`, `palettes/`, `citystyles/` | Datapack |
[code review](../examples/claim-tests.md#f12-1){.v .v-c}

The class names agree: a file build carries `AbstractAssetRegistry` and a datapack build carries `RegistryAssetRegistry`. [code review](../examples/claim-tests.md#f12-1){.v .v-c}

## What changed, and what did not

The concepts survived the move almost intact. A building still stacks parts, a part is still a grid of characters, a palette still maps a character to a block, and a city style still picks buildings. What changed is where those objects live and how they are named. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

| | File era | Datapack era |
|---|---|---|
| Unit of a file | Many assets per file, mixed types | One asset per file |
| How an asset is named | A `name` key inside the object | The file path |
| How a type is decided | A `type` key inside the object | The folder |
| Namespaces | None | `namespace:path`, everywhere |
| Adding your own | One `userassets.json` named in a config list | Any datapack |
| Overriding | Load order in that list, later wins | Pack order, later wins |
| Config | `general.cfg` plus `profile_<name>.cfg` | `common.toml` plus `profiles/<name>.json` |
| Asset types | 10 | 13 |
[code review](../examples/claim-tests.md#f12-2){.v .v-c} [code review](../examples/claim-tests.md#f12-5){.v .v-c}

Five datapack types have no file-era equivalent: `variant`, `scattered`, `stuff`, and the separate predefined city and sphere registries. Predefined placements do exist here, as the `city` and `sphere` types, but as asset types among the rest rather than registries of their own. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

!!! danger "Block names are pre-flattening"
    A file-era palette writes `minecraft:rail@1`, not `minecraft:rail[shape=...]`. The `@` carries the old metadata value. Copying such a palette into a modern version breaks it, and not gently: the whole palette fails to build rather than that one entry. See [Known Issues](../troubleshooting/known-issues.md#a-shipped-palette-carries-a-112-block-id-and-cannot-be-built), where a leftover of exactly this kind still ships in 7.4.12. [code review](../examples/claim-tests.md#f12-7){.v .v-c} [game test](../examples/claim-tests.md#prf-1){.v .v-g}

## Which pages here apply to you

| Page | Covers |
|---|---|
| [File-Era Assets](assets.md) | The ten types, the shape of a file, and what each type holds |
| [Adding Your Own Content](adding-content.md) | `userassets.json`, the load list, overriding, and the config |
[code review](../examples/claim-tests.md#f12-2){.v .v-c}

The reference section of this wiki does **not** apply. Its key tables are read from datapack codecs that do not exist here. Where a key name matches, treat that as a coincidence worth checking rather than a guarantee. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## See also

- [Which Version Do I Have](../versions/index.md)
- [Key availability](../versions/key-availability.md) for the datapack era's own version differences <!-- noclaim -->
