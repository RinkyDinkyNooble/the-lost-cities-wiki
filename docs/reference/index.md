---
claims: verified
---

# Reference

Key-by-key documentation for every Lost Cities asset type, read against **7.4.12, Minecraft 1.20.1**. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

Every type except the Profile is datapack JSON living at `data/<namespace>/lostcities/<type>/<name>.json`. The Profile is config, at `config/lostcities/profiles/<name>.json`. See [Namespaces](../getting-started/namespaces.md#the-exact-folder-layout) if that path looks wrong. [game test](../examples/claim-tests.md#ns-2){.v .v-g}

## The chain

The Profile sits outside the datapack system and names a world style. The six datapack types below it compose from the top down, each naming the next. [The Content Model](../getting-started/content-model.md) walks the same chain with a worked example. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

| # | Page [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Folder | What it decides |
|---|---|---|---|
| 0 | [Profile](profile.md) | *(config)* | Which world style a dimension uses, plus 131 generation settings |
| 1 | [World Style](worldstyle.md) | `worldstyles/` | Which city styles appear, and where |
| 2 | [City Style](citystyle.md) | `citystyles/` | The theme: palettes, building, street and park settings, and which buildings exist |
| 3 | [Style](style.md) | `styles/` | Which palettes are merged, rolled per slot |
| 4 | [Building](building.md) | `buildings/` | Which parts stack, per floor and per cellar |
| 5 | [Building Part](part.md) | `parts/` | The block grid itself, 16 by 16 by 6 |
| 6 | [Palette](palette.md) | `palettes/` | What each character means |

Break a link in that chain and the failure throws rather than passing quietly, though where it surfaces depends on which link broke. [Namespaces](../getting-started/namespaces.md#what-a-reference-into-the-wrong-namespace-actually-does) has the three cases. [game test](../examples/claim-tests.md#ns-4){.v .v-g}

## When a key appears to do nothing

[Key Interactions](interactions.md) collects the cases where one key is gated, overridden or outranked by another. A correctly set key that produces no change is usually one of those rather than a mistake in the file. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Supporting types

Optional, and worth reaching for once the chain above works. <!-- noclaim -->

| Page [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Folder | What it is for |
|---|---|---|
| [Variant](variant.md) | `variants/` | A reusable weighted block list, named from a palette |
| [Condition](condition.md) | `conditions/` | A weighted table that picks a value based on where you are |
| [Multi-Building](multibuilding.md) | `multibuildings/` | One structure spanning several chunks |
| [Scattered Building](scattered.md) | `scattered/` | Standalone structures out in the wilderness |
| [Stuff Object](stuff.md) | `stuff/` | Small decorative extras placed by scanning columns |
| [Predefined City and Sphere](predefined.md) | `predefinedcities/`, `predefinedspheres/` | Pin a city or sphere to exact coordinates |

Together the two tables cover all 13 registries the mod creates, so no asset type is missing from this reference. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

## Reading these pages

Each page opens with a TL;DR, then a key table, then the behaviour the keys alone do not tell you. <!-- noclaim -->

!!! warning "No number in any of these files is validated"
    Nothing in the mod range-checks a value, in an asset or in a profile. Every range these pages document is the window the mod was designed around, not a rule it enforces, and an out-of-range value loads silently and is used as written. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    [`validate.py`](../examples/index.md#validatepy) checks the rules that can be checked outside the game. <!-- noclaim -->

Three pages carry most of the traps and are worth reading before writing anything: <!-- noclaim -->

- [Palette](palette.md#the-128-slot-rule-for-blocks-and-variant), for the 128-slot rule and what a `char` may legally be [game test](../examples/claim-tests.md#pal-3){.v .v-g}
- [Building](building.md#floor-coverage-the-most-common-failure), for the floor-coverage failure [game test](../examples/claim-tests.md#bld-4){.v .v-g}
- [City Style](citystyle.md#inheritance), for inheritance being additive in a way that surprises nearly everyone [game test](../examples/claim-tests.md#cty-5){.v .v-g}

## See also

- [Your First Custom City](../getting-started/first-city.md) for these types as six real files
- [Examples](../examples/index.md) for a complete working datapack
- [Error Messages](../troubleshooting/errors.md) for when one of these files is wrong
- [Glossary](../glossary.md) <!-- noclaim -->
