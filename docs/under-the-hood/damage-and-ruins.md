# Damage, Ruins & Explosions

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This page explains the mechanism behind fields you are already setting on the Profile page, useful for tuning them with intent instead of by trial and error.

!!! tip "TL;DR"
    Each chunk independently rolls for explosions, then breaks blocks around each explosion's center. `notbreakable`-tagged blocks never break; `easybreakable`-tagged ones break more easily. Ruins are a separate, similarly-rolled destruction pass on top of a fully-placed building. Both run after part selection is already finished.

## Explosions are per-chunk, independent rolls

Every city chunk independently rolls for a normal explosion (`explosionChance`, radius from `explosionMinRadius`/`Max`, height from `explosionMinHeight`/`Max`) and, separately, a mini explosion (`miniExplosionChance` and its own radius/height range). A single chunk can end up with several overlapping explosions if it is unlucky enough to roll more than one type, or if a neighbouring chunk's explosion reaches into it, damage from every overlapping source accumulates rather than only the strongest one applying. `explosionsInCitiesOnly` restricts where an explosion's *center* can roll, not how far its blast can reach, a blast centered just inside a city can still tear into non-city terrain at its edge.

## What actually breaks

Whether a given block breaks under nearby damage is not a flat roll, block identity matters:

| Tag | Effect |
|---|---|
| `lostcities:notbreakable` | Never breaks, regardless of explosion strength. Bedrock, end portal, end portal frame, end gateway by default. |
| `lostcities:easybreakable` | Breaks more readily than an untagged block. `forge:glass` by default. |
| *(untagged)* | Normal odds, roughly proportional to distance from the explosion center and its strength. |

When a block does break, the palette entry's `damaged` field (see [Palette Reference](../reference/palette.md)) decides what it becomes, rubble, a broken variant, or whatever else was authored there. A character with no `damaged` value set just breaks to air.

## Debris spreads into neighbouring chunks

Damage does not stop cleanly at a chunk border. `debrisToNearbyChunkFactor` controls how much of a damaged chunk's rubble bleeds into its neighbours, and it is an inverse relationship, **higher values mean less spillover**, not more. Seeing scattered rubble just outside the chunk that actually rolled the explosion is expected behaviour, not a sign that damage settings are misconfigured.

## Ruins are a separate pass, after the building already exists

Ruin generation (`ruinChance`, destruction range `ruinMinlevelPercent`–`ruinMaxlevelPercent` of the building's height) runs as its own chance-gated pass, alongside explosion/debris handling, and like explosions it happens strictly **after** the building's parts have already been fully selected and placed (see [The Generation Pipeline](generation-pipeline.md)). A building's floor/part selection never knows in advance that it is about to be ruined, ruin state cannot bias which variant of a floor got picked, it only ever removes blocks from whatever was already going to generate.

## See also

- [Profile Reference](../reference/profile.md#explosions) for every field named above
- [Palette Reference](../reference/palette.md) for the `damaged` field and block tags
- [The Generation Pipeline](generation-pipeline.md)
