# The Lost Cities - DevTool

A companion mod for [The Lost Cities](https://www.curseforge.com/minecraft/mc-mods/the-lost-cities),
for people authoring content for it. It reports faults earlier and more accurately,
and can optionally repair behaviour traced to a bug.

It adds no blocks, no items and no generation of its own. Removing it leaves every
world it touched loadable by vanilla Lost Cities.

The build plan, including everything not yet written, is in [PLAN.md](PLAN.md).

## Requirements

| | |
|---|---|
| Minecraft | 1.20.1 |
| Forge | 47.4.10 |
| The Lost Cities | 7.4.12, a hard dependency |

The Lost Cities version range is deliberately narrow. A mixin is bound to the shape
of the code it patches, so each target version needs its own verification pass.

## Configuration

`config/lostcities_devtool-common.toml`, in two groups.

| Group | Default | Rule |
|---|---|---|
| `diagnostics` | on | Only changes what is reported. Cannot alter block placement. |
| `repairs` | off | Changes what generates. A world made with one enabled will not come out the same without it. |

## What it does today

### `catchSphereFeatureErrors`

`LostCityFeature` wraps its generation call in a `catch (Exception)`, which is what
makes a mistake in a datapack survivable: the chunk fails, a line is logged, and
generation continues.

`LostCitySphereFeature` has no `try` anywhere in the class, and it reaches the same
`BuildingInfo` work through `Spheres.generateSpheres`. On `landscapeType` spheres,
cavernspheres or space, a fault that would normally be logged per chunk escapes to
vanilla's feature placer instead.

Measured on Lost Cities 7.4.12, same pack, same profile, same seed, with only the
toggle changed:

| Toggle | Faults escaping | Faults logged | Server |
|---|---|---|---|
| off | 21 | 0 | connection dropped mid-run |
| on | **0** | 338 | ran to completion |

Nothing about what generates changes. A chunk that would have failed still fails and
is left in the same partial state. Only the survivability changes.

### `detailedFaultReports`

The mod logs `Error generating chunk <x>,<z>: <message>`. Those coordinates are the
chunk being generated, which for a whole class of faults is not the chunk at fault:
a fault raised while a chunk's `BuildingInfo` is built spreads to every neighbour
that queries it, and those queries chain.

Two things are added, and nothing the mod logs is suppressed.

**The misconfiguration message is enriched at the throw**, where the building and
its chunk are known exactly:

```
Misconfiguration! Floor were generated for a building where no part condition matches!
  [building wt5:rangetest at chunk 10,8, levels 0 to 6 inclusive.
   Every chunk that queries this one fails the same way]
```

On a pack with three broken buildings, that turned 78 undifferentiated failures
across a 13 by 10 chunk area into three named faults.

**A fuller report is logged beside each caught fault**, naming the profile, world
style, city style, building, floor and cellar counts, and the whole cause chain. For
an unresolved palette character it gives the code point and Unicode name, which a
console cannot render:

```
Lost Cities generation fault
    chunk 8,14
    fault: RuntimeException: Could not find entry '?' in the palette for part 'wt7:ct_box'!
    undefined character: '?'  U+0470  CYRILLIC CAPITAL LETTER PSI
    used by part: wt7:ct_box
    the message names the part, but the fault is in a palette. Check, in this order:
      1. the part's own 'palette' or 'refpalette'
      ...
```

## Building

```bash
./gradlew build
```

The jar lands in `build/libs/`. `libs/lostcities-1.20-7.4.12.jar` is compile-only
and is not bundled.

## Testing

Acceptance tests run on the wiki's headless server rig, which boots a real server,
force loads a grid and reads the world back over RCON.

```bash
cd ../research/server-1.20.1-7.4.12
python harness.py --pack ../../docs/examples/wiki-test8 --profile wteight \
    --probes probes/wt8ruins.json \
    --profile-patch '{"lostcity":{"landscapeType":"spheres","ruinChance":1.0}}'
```

Every feature in [PLAN.md](PLAN.md) names the test that proves it.

## Licence

[0BSD](LICENSE.txt). No rights reserved, no attribution required.

Not affiliated with or endorsed by McJty.
