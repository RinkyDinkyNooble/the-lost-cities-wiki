# Damage, Ruins & Explosions

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This page explains the mechanism behind keys you are already setting on the Profile page, useful for tuning them with intent instead of by trial and error.

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

When a block does break, the palette entry's `damaged` key (see [Palette Reference](../reference/palette.md)) decides what it becomes, rubble, a broken variant, or whatever else was authored there. A character with no `damaged` value set just breaks to air.

## Debris spreads into neighbouring chunks

Damage does not stop cleanly at a chunk border. `debrisToNearbyChunkFactor` controls how much of a damaged chunk's rubble bleeds into its neighbours, and it is an inverse relationship, **higher values mean less spillover**, not more. Seeing scattered rubble just outside the chunk that actually rolled the explosion is expected behaviour, not a sign that damage settings are misconfigured.

## Ruins are a separate pass, after the building already exists

Ruin generation is chance-gated on `ruinChance`, and destroys a band of the building's height between `ruinMinlevelPercent` and `ruinMaxlevelPercent`. It runs strictly **after** the building's parts have been selected and placed. A building's part selection never knows it is about to be ruined, so ruin state cannot bias which variant of a floor was picked. It only removes blocks from what was already going to generate.

!!! warning "Ruins and explosions are not the same phase, despite being described together"
    This is easy to get wrong, and the distinction changes what each one can touch.

    Ruins run **inside** the city-chunk pass, immediately after the building and street are placed:

    ```
    generateBuilding -> generateStreet -> generateRuins -> highways
      -> generateStreetDecorations -> generateHighways -> generateRubble -> generateStuff
    ```

    Explosions and debris run **much later**, back in the top-level chunk pass, after railways and the torch fixup, just before the chunk is flushed.

    The practical consequence: anything generated after `generateRuins` in that list is **not** ruined. Street decorations, highways, rubble and stuff objects all land on top of an already-ruined building and survive intact. Explosion damage, running later still, does affect all of them.

    So a half-collapsed building with pristine street furniture around it is expected, not a bug. See [The Generation Pipeline](generation-pipeline.md).

## You cannot exempt one building from ruin

This is the first thing people look for, so it is worth stating plainly: **a Building asset has no key that protects it from the ruin pass.** There is no `preventruins`, no `noruin`, and no equivalent under another name.

The full set of controls:

| What you want | How to get it |
|---|---|
| A specific landmark left intact | Place it through a [Predefined City](../reference/predefined.md) and set `preventruins: true` on that entry. This is the only per-building exemption in the mod. |
| Fewer ruined buildings everywhere | Lower `ruinChance` in the [Profile](../reference/profile.md). |
| No ruined buildings at all | Set `ruinChance` to `0`. |
| Specific blocks to survive | Add them to the `lostcities:notbreakable` tag. That protects the blocks, not the building. |

!!! note "Ruin chance is profile-wide and cannot vary by city style"
    A city style can override `explosionchance`, but there is no city style key for ruin chance. So you cannot make one district ruined and another pristine through city styles. The only per-place control is a predefined city.

    This asymmetry is easy to miss, because explosions and ruins are otherwise described together and run in the same phase.

## See also

- [Profile Reference](../reference/profile.md#explosions) for every key named above
- [Palette Reference](../reference/palette.md) for the `damaged` key and block tags
- [The Generation Pipeline](generation-pipeline.md)
