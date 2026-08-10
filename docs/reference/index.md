# Reference

Field-by-field documentation for every Lost Cities asset type, verified against **7.4.12 / MC 1.20.1**.

Everything except the Profile is datapack JSON living at `data/<namespace>/lostcities/<type>/<name>.json`. The Profile is config, at `config/lostcities/profiles/<name>.json`. See [Namespaces](../getting-started/namespaces.md#the-exact-folder-layout) if that path looks odd.

## The chain

These six compose top to bottom, each one naming the next. This is the spine of the whole system, and [The Content Model](../getting-started/content-model.md) explains how they fit together.

| # | Page | Folder | What it decides |
|---|---|---|---|
| 0 | [Profile](profile.md) | *(config)* | Which world style a dimension uses, plus ~100 generation knobs |
| 1 | [World Style](worldstyle.md) | `worldstyles/` | Which city styles appear, and where |
| 2 | [City Style](citystyle.md) | `citystyles/` | A theme: palettes, building/street/park settings, which buildings exist |
| 3 | [Style](style.md) | `styles/` | Which palettes get merged, randomly per slot |
| 4 | [Building](building.md) | `buildings/` | Which parts stack, per floor and cellar |
| 5 | [Building Part](part.md) | `parts/` | The actual 16×16×6 block grid |
| 6 | [Palette](palette.md) | `palettes/` | What each character means |

Break any link in that chain and your content silently never loads. That failure mode is covered in [Namespaces](../getting-started/namespaces.md).

## Supporting types

Optional. Reach for these once the chain above works.

| Page | Folder | What it's for |
|---|---|---|
| [Variant](variant.md) | `variants/` | A reusable weighted block list, referenced from a palette |
| [Condition](condition.md) | `conditions/` | A weighted "pick a value based on where you are" table |
| [Multi-Building](multibuilding.md) | `multibuildings/` | One structure spanning several chunks |
| [Scattered Building](scattered.md) | `scattered/` | Standalone structures out in the wilderness |
| [Stuff Object](stuff.md) | `stuff/` | Small decorative extras placed by column scan |
| [Predefined City & Sphere](predefined.md) | `predefinedcities/`, `predefinedspheres/` | Pin a city or sphere to exact coordinates |

## Reading these pages

Each starts with a TL;DR, then a field table, then the behaviour that isn't obvious from the fields.

!!! warning "No number in any of these files is validated"
    There is no range checking anywhere in the mod, in assets or in profiles. Every range these pages document is the window the mod was designed around, not a rule it enforces. Out-of-range values load silently and are used as written.

    [`validate.py`](../examples/index.md#validatepy) checks the rules that can be checked outside the game.

Three pages carry most of the traps worth reading before you write anything:

- [Palette](palette.md#the-128-slot-rule-for-blocks-and-variant), for the 128-slot rule and what a `char` may legally be
- [Building](building.md#floor-coverage-the-most-common-crash), for the floor-coverage crash
- [City Style](citystyle.md#inheritance), for inheritance being additive in a way nobody expects

## See also

- [Your First Custom City](../getting-started/first-city.md) for these types as six real files
- [Examples](../examples/index.md) for a complete working datapack
- [Error Messages](../troubleshooting/errors.md) for when one of these files is wrong
- [Glossary](../glossary.md)
