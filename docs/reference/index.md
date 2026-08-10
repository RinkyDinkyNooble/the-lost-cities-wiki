# Reference

Key-by-key documentation for every Lost Cities asset type, verified against **7.4.12, Minecraft 1.20.1**.

Every type except the Profile is datapack JSON, and lives at `data/<namespace>/lostcities/<type>/<name>.json`. The Profile is config, at `config/lostcities/profiles/<name>.json`. See [Namespaces](../getting-started/namespaces.md#the-exact-folder-layout) if that path looks wrong to you.

## The chain

The Profile sits outside the datapack system and names a world style. The six datapack types below it then compose from the top down, each one naming the next. This is the spine of the whole system, and [The Content Model](../getting-started/content-model.md) explains how the pieces fit together.

| # | Page | Folder | What it decides |
|---|---|---|---|
| 0 | [Profile](profile.md) | *(config)* | Which world style a dimension uses, plus about 100 generation settings |
| 1 | [World Style](worldstyle.md) | `worldstyles/` | Which city styles appear, and where |
| 2 | [City Style](citystyle.md) | `citystyles/` | The theme: palettes, building, street and park settings, and which buildings exist |
| 3 | [Style](style.md) | `styles/` | Which palettes are merged, rolled per slot |
| 4 | [Building](building.md) | `buildings/` | Which parts stack, per floor and per cellar |
| 5 | [Building Part](part.md) | `parts/` | The block grid itself, 16 by 16 by 6 |
| 6 | [Palette](palette.md) | `palettes/` | What each character means |

Break any link in that chain and your content silently never loads. [Namespaces](../getting-started/namespaces.md) covers that failure.

## Supporting types

These are optional. Reach for them once the chain above works.

| Page | Folder | What it is for |
|---|---|---|
| [Variant](variant.md) | `variants/` | A reusable weighted block list, referenced from a palette |
| [Condition](condition.md) | `conditions/` | A weighted table that picks a value based on where you are |
| [Multi-Building](multibuilding.md) | `multibuildings/` | One structure spanning several chunks |
| [Scattered Building](scattered.md) | `scattered/` | Standalone structures out in the wilderness |
| [Stuff Object](stuff.md) | `stuff/` | Small decorative extras placed by scanning columns |
| [Predefined City and Sphere](predefined.md) | `predefinedcities/`, `predefinedspheres/` | Pin a city or sphere to exact coordinates |

Together these two tables cover all 13 registries the mod creates. There is no asset type this reference omits.

## Reading these pages

Each page opens with a TL;DR, then a key table, then the behaviour that the keys alone do not tell you.

!!! warning "No number in any of these files is validated"
    There is no range checking anywhere in the mod, in an asset or in a profile. Every range these pages document is the window the mod was designed around, not a rule it enforces. An out-of-range value loads silently and is used as written.

    [`validate.py`](../examples/index.md#validatepy) checks the rules that can be checked outside the game.

Three pages carry most of the traps, and are worth reading before you write anything:

- [Palette](palette.md#the-128-slot-rule-for-blocks-and-variant), for the 128-slot rule and what a `char` may legally be
- [Building](building.md#floor-coverage-the-most-common-crash), for the floor-coverage crash
- [City Style](citystyle.md#inheritance), for inheritance being additive in a way that surprises nearly everyone

## See also

- [Your First Custom City](../getting-started/first-city.md) for these types as six real files
- [Examples](../examples/index.md) for a complete working datapack
- [Error Messages](../troubleshooting/errors.md) for when one of these files is wrong
- [Glossary](../glossary.md)
