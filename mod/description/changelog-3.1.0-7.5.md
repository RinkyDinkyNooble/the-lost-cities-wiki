# 3.1.0-7.5

For The Lost Cities 7.5.1 to 7.5.5, on Minecraft 1.20.1 and Forge 47+.

Two import fixes, both found from a pack in the wild, and the supported range
extended to 7.5.5.

| Your Lost Cities | Download |
|---|---|
| 7.4.12 | `3.0.0` |
| 7.5.1, 7.5.2, 7.5.3, 7.5.4, 7.5.5 | `3.1.0-7.5` |

The 7.5 file is now ahead of the 7.4.12 file. Both fixes below are in this one and
not in `3.0.0`.

## An import now reads the profile, not only the world style

Generation starts from a profile. The profile picks the world style, and it can also
name a `cityStyleAlternative` that no world style mentions, entered whenever a city's
factor falls below `cityStyleThreshold`.

An import walked only the world style's own `citystyles` list, so every asset living
under that second style was invisible to it. The pack came into the workshop looking
smaller than it is, and nothing said why.

Every profile pointing at the world style being imported is now walked as well.

**This affects Lost Cities' own pack.** The shipped `largecities` profile names
`citystyle_border` at a threshold of 0.4, so that style was never imported either.

Measured against ChaosZPack, whose world style lists one city style while its profile
names another: **84 assets** arrived that previously did not, among them the mall,
the school and the row buildings.

An alternative style left at the default `cityStyleThreshold` of `-1.0` can never be
reached, because no city factor falls below it. It is imported anyway and the import
says so, rather than leaving a pack that looks correct and generates nothing from
that style.

An export puts the style back where it came from. It is kept off the world style's
`citystyles` list, because listing it there would weight it against the others and
roll it for ordinary cities, and the profile written beside the pack points at it
under the pack's own namespace.

## Multi-building footprints are no longer capped at 10 chunks

The catalogue stopped at 10x10, which is the largest footprint the default
`multisettings.areasize` can place. A pack may widen that area and ship a bigger
building, and packs do. An import had no plot for those, so it dropped the largest
buildings a pack had.

Footprints past the catalogue are now added to it when an import meets them.

ChaosZPack sets `areasize` to 16 and ships an 11x8 walmart and a 4x11. Both now
import; before, both were dropped. Its two 16-wide aircraft carriers are in the jar
and referenced by no city style, so they stay out either way.

Rows are appended in the order they are first seen and that order is saved with the
world, so a build after a restart puts them back in the same place. Nothing that was
already laid out moves to make room: measured at **388 plots before an import and 390
after, none of them moved**.

A footprint past 64 chunks is refused and named. At that size it is a typo in `dimx`
rather than a building.

## Supported range

Now 7.5.1 through 7.5.5, closed at the top.

Every mixin injection point was compared across 7.4.12, 7.5.1, 7.5.2, 7.5.3, 7.5.4
and 7.5.5, by exact descriptor and by counting every redirected call inside its
target method, with 7.4.12 as a control. All nineteen hold on 7.5.5. 7.5.5 changes 45
classes and adds one, and none of them is one this mod patches.

The range is closed rather than open to 7.6 because an open bound bets that a patch
release moves nothing, and 7.5.5 moved 45 classes. A version that does not exist yet
cannot have been checked.

## Known gap on 7.5.5

The key reference this mod ships is generated from 7.5.4, and 7.5.5 declares six keys
it does not:

| Key | Where | What is missing |
|---|---|---|
| `railwaySpacingNorthSouth`, `railwaySpacingEastWest` | profile | `/lcdev key` does not describe them, and an export writes them under the wrong section, where Lost Cities does not read them |
| `bridgesupport`, `bridgesupportpart` | city style, world style | No plot in the workshop, so an import does not bring them in and an export does not write them |
| `highwaysupport`, `highwaysupportpart` | world style | The same |

Nothing here throws and no pack is refused: the asset check has no list of permitted
keys, so a 7.5.5 pack using them loads and generates normally. What is lost is the
authoring support for those six, on 7.5.5 only. Regenerating the reference needs the
same per-version pass every other version had.
