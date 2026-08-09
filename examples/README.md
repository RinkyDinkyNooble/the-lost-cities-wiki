# Examples

Complete, working Lost Cities content. Every file here is a whole file, not a fragment, so you can copy one wholesale and edit from a known-good starting point.

Targets **Lost Cities 7.4.12 / Minecraft 1.20.1 (Forge)**.

## `first-city/`

The datapack built step by step in [Your First Custom City](../docs/getting-started/first-city.md). A glass-and-concrete tower that replaces most buildings in the city, in its own `mycity` namespace so it collides with nothing.

```
first-city/
  pack.mcmeta
  data/mycity/lostcities/
    palettes/tower.json        five characters, one damaged mapping
    parts/tower_floor.json     16x16x6, the repeating storey
    parts/tower_top.json       16x16x6, the roof
    buildings/tower.json       stacks the parts, sets filler
    citystyles/mycity.json     inherits citystyle_common, adds the tower
    worldstyles/mycity.json    points at that city style
  profile/mycity.json          NOT part of the datapack, see below
```

**`profile/mycity.json` does not go in the datapack.** Profiles are config, not content. It belongs in `config/lostcities/profiles/`. Everything under `data/` is the datapack.

### Using it

Copy `first-city/` into `<world>/datapacks/`, drop `profile/mycity.json` into `config/lostcities/profiles/`, and point a dimension at it in `config/lostcities/common.toml`. Full walkthrough with the reasoning is in [the tutorial](../docs/getting-started/first-city.md).

## `validate.py`

Checks a datapack against the rules this wiki documents:

```bash
python examples/validate.py examples/first-city
```

What it catches, and where each rule comes from:

| Check | Documented at |
|---|---|
| `char` is a single UTF-16 code unit (emoji fail) | [Palette](../docs/reference/palette.md#what-counts-as-a-valid-character) |
| Exactly one of `block`/`variant`/`blocks`/`frompalette` per entry | [Palette](../docs/reference/palette.md) |
| Weighted lists reach 128, and no entry sits past the fill point | [Palette](../docs/reference/palette.md#the-128-slot-rule-for-blocks-and-variant) |
| Parts are 16x16, every row exactly `xsize` **UTF-16 units** long | [Part](../docs/reference/part.md) |
| `meta`, not `metadata` | [Part](../docs/reference/part.md) |
| Buildings have `filler` and at least one unconditioned part | [Building](../docs/reference/building.md#floor-coverage-the-most-common-crash) |
| Floor and cellar bounds inside their windows | [Building](../docs/reference/building.md) |
| Stuff `maxcount` > `mincount`, `maxheight` > `minheight` | [Stuff Object](../docs/reference/stuff.md) |
| Part characters are defined somewhere | [Palette](../docs/reference/palette.md#collisions-and-merge-order) |

This is also how the wiki keeps itself honest: if `validate.py` and the mod ever disagree, one of them is wrong and it's worth finding out which.
