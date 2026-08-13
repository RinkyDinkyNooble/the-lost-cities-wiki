# The file-asset era

Mod versions 1.0.1 through 5.0.4 do not read datapacks. Nothing this wiki
documents about buildings, parts, palettes, city styles or world styles applies to
them.

This page exists so you can tell quickly whether you are in that era, and so you
know what the system was instead. It is not a guide to that system. This wiki does
not document it.

## Which versions

| Mod versions | Minecraft | Asset system |
|---|---|---|
| 1.0.1 through 5.0.4 | 1.11.2 through 1.18 | File |
| 5.3.29 and later | 1.18 and later | Datapack |

The change lands inside the Minecraft 1.18 line. 5.0.4 is a file-asset version and
5.3.29 is a datapack version, and both are labelled 1.18. The mod version decides,
not the Minecraft version.

## How to tell in 10 seconds

Open the jar and look for a folder.

| What you find | Era |
|---|---|
| `assets/lostcities/citydata/` contains `buildingparts.json`, `palette.json` and similar | File |
| `data/lostcities/lostcities/` contains `buildings/`, `palettes/`, `citystyles/` | Datapack |

## What the file system was

The mod shipped its city content as a small set of combined JSON files inside the
jar:

```
assets/lostcities/citydata/buildingparts.json
assets/lostcities/citydata/palette.json
assets/lostcities/citydata/conditions.json
assets/lostcities/citydata/highwayparts.json
assets/lostcities/citydata/monorailparts.json
assets/lostcities/citydata/railparts.json
assets/lostcities/citydata/library.json
```

Each file held many assets, not one. To add your own content you wrote a single
extra file and pointed the mod at it:

```
config/lostcities/userassets.json
```

The datapack system replaced this with one file per asset, discovered by folder,
loaded through Minecraft's own registry. That is why the two are not convertible by
renaming: the unit of a file changed, and so did who loads it.

## Config format also differs

| Mod versions | Config file |
|---|---|
| 1.0.1 through 2.0.22 | `config/lostcities/general.cfg`, in Forge's `.cfg` format |
| 2.0.28 and 3.0.2 | `config/lostcities-common.toml` |
| 4.0.5 and later | `config/lostcities/common.toml` |

The mod builds the first path from the config directory, then `lostcities`, then
`general.cfg`. All 4 versions in that era do the same.

The profile keys themselves overlap heavily across all of these. The file that
holds them, and its syntax, does not.

## If you are on one of these versions

Two options.

| Option | What it costs |
|---|---|
| Move to a datapack version | You rewrite your content once, into one file per asset. Everything on this wiki then applies. |
| Stay | Use the mod's own documentation for your version. This wiki cannot help you, and applying it will waste your time. |

Minecraft 1.12.2 remains widely used, so staying is a real choice. It is simply
outside what this wiki covers.
