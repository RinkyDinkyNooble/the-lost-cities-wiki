---
claims: verified
---

# The file-asset era

Mod versions 1.0.1 through 5.0.4 do not read datapacks. Nothing in this wiki's
reference section applies to them, because those pages describe datapack codecs that
do not exist there. [code review](../examples/claim-tests.md#key-1){.v .v-c}

**That era has its own section now.** [The File-Asset Era](../file-era/index.md)
covers the ten asset types, the shape of a file, and how to add your own content,
read out of the 1.12.2 jar. This page stays as the quick answer to which era you are
in. [code review](../examples/claim-tests.md#f12-2){.v .v-c}

## Which versions

| Mod versions [code review](../examples/claim-tests.md#key-1){.v .v-c} | Minecraft | Asset system |
|---|---|---|
| 1.0.1 through 5.0.4 | 1.11.2 through 1.18 | File |
| 5.3.29 and later | 1.18 and later | Datapack |

The change lands inside the Minecraft 1.18 line. 5.0.4 is a file-asset version and
5.3.29 is a datapack version, and both are labelled 1.18. The mod version decides,
not the Minecraft version. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## How to tell in 10 seconds

Open the jar and look for a folder. <!-- noclaim -->

| What you find [code review](../examples/claim-tests.md#key-1){.v .v-c} | Era |
|---|---|
| `assets/lostcities/citydata/` contains `buildingparts.json`, `palette.json` and similar | File |
| `data/lostcities/lostcities/` contains `buildings/`, `palettes/`, `citystyles/` | Datapack |

## What the file system was

The mod shipped its city content as a small set of combined JSON files inside the
jar: [code review](../examples/claim-tests.md#key-1){.v .v-c}

```
assets/lostcities/citydata/buildingparts.json
assets/lostcities/citydata/palette.json
assets/lostcities/citydata/conditions.json
assets/lostcities/citydata/highwayparts.json
assets/lostcities/citydata/monorailparts.json
assets/lostcities/citydata/railparts.json
assets/lostcities/citydata/library.json
```

Each file held many assets rather than one. Adding your own content meant writing a
single extra file and pointing the mod at it: [code review](../examples/claim-tests.md#key-1){.v .v-c}

```
config/lostcities/userassets.json
```

The datapack system replaced this with one file per asset, discovered by folder and
loaded through Minecraft's own registry. That is why renaming does not convert
between them: the unit of a file changed, and so did who loads it. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## Config format also differs

| Mod versions [code review](../examples/claim-tests.md#key-1){.v .v-c} | Config file |
|---|---|
| 1.0.1 through 2.0.22 | `config/lostcities/general.cfg`, in Forge's `.cfg` format |
| 2.0.28 and 3.0.2 | `config/lostcities-common.toml` |
| 4.0.5 and later | `config/lostcities/common.toml` |

The mod builds the first path from the config directory, then `lostcities`, then
`general.cfg`, and all four versions in that era do the same. [code review](../examples/claim-tests.md#key-1){.v .v-c}

The profile keys themselves overlap heavily across all of these. The file that holds
them, and its syntax, does not. [code review](../examples/claim-tests.md#key-1){.v .v-c}

## If you are on one of these versions

Two options, and neither one is bad. <!-- noclaim -->

| Option | What it costs [code review](../examples/claim-tests.md#f12-2){.v .v-c} |
|---|---|
| Stay | Nothing. [The File-Asset Era](../file-era/index.md) documents the system you have |
| Move to a datapack version | Rewriting your content once, into one file per asset, and every block name with it |

Minecraft 1.12.2 remains widely used, which is why that section exists. [code review](../examples/claim-tests.md#f12-1){.v .v-c}
