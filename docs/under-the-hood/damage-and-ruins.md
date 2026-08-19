---
claims: verified
---

# Damage, Ruins & Explosions

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This page covers the mechanism behind keys you are already setting on the Profile page, for tuning them with intent rather than by trial and error. <!-- noclaim -->

!!! tip "TL;DR"
    Each chunk independently rolls for explosions, then breaks blocks around each centre. `notbreakable`-tagged blocks never break and `easybreakable`-tagged ones break more easily. Ruins are a separate destruction pass on top of a fully placed building. Both run after part selection has finished. [code review](../examples/claim-tests.md#dmg-1){.v .v-c} [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

## Explosions are per-chunk, independent rolls

Every city chunk independently rolls for a normal explosion, with `explosionChance`, a radius from `explosionMinRadius` and `explosionMaxRadius`, and a height from `explosionMinHeight` and `explosionMaxHeight`. It separately rolls a mini explosion, with `miniExplosionChance` and its own radius and height range. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

One chunk can end up with several overlapping explosions, either by rolling more than one type or by catching a neighbouring chunk's blast, and damage from every overlapping source accumulates rather than only the strongest applying. `explosionsInCitiesOnly` restricts where a blast's **centre** can roll, not how far it reaches, so a blast centred just inside a city can still tear into non-city terrain at its edge. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## What actually breaks

Whether a block breaks under nearby damage is not a flat roll. Block identity matters. [code review](../examples/claim-tests.md#dmg-1){.v .v-c}

| Tag | Effect |
|---|---|
| `lostcities:notbreakable` | Never breaks, whatever the explosion strength. Bedrock, end portal, end portal frame and end gateway by default |
| `lostcities:easybreakable` | Breaks more readily than an untagged block. `forge:glass` by default |
| *(untagged)* | Normal odds, roughly proportional to distance from the blast centre and its strength |
[code review](../examples/claim-tests.md#dmg-1){.v .v-c}

When a block does break, the palette entry's `damaged` key decides what it becomes: rubble, a broken variant, or whatever else was authored there. A character with no `damaged` value breaks to air. [game test](../examples/claim-tests.md#pal-13){.v .v-g}

!!! warning "`damaged` covers the rubble band, not the ruined section"
    Measured rather than assumed, and narrower than this page once claimed. See [Palette Reference](../reference/palette.md). [game test](../examples/claim-tests.md#pal-13){.v .v-g}

## Debris spreads into neighbouring chunks

Damage does not stop cleanly at a chunk border. `debrisToNearbyChunkFactor` controls how much of a damaged chunk's rubble bleeds into its neighbours, and the relationship is inverse: **higher values mean less spillover**. Scattered rubble just outside the chunk that rolled the explosion is expected, not a sign of a misconfiguration. [code review](../examples/claim-tests.md#dmg-2){.v .v-c}

## Ruins are a separate pass, after the building already exists

Ruin generation is gated on `ruinChance` and destroys a band of the building's height between `ruinMinlevelPercent` and `ruinMaxlevelPercent`. It runs strictly **after** the building's parts have been selected and placed, so part selection never knows it is about to be ruined and ruin state cannot bias which variant of a floor was picked. It only removes blocks from what was already going to generate. [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

The ruin pass is also what consumes a palette's `rubble` character. A character used nowhere else appeared 40 times with ruins on and never with ruins off. [game test](../examples/claim-tests.md#bld-8){.v .v-g}

!!! warning "Ruins and explosions are not the same phase, despite being described together"
    The distinction changes what each one can touch. [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

    Ruins run **inside** the city-chunk pass, immediately after the building and street are placed: <!-- noclaim -->

    ```
    generateBuilding -> generateStreet -> generateRuins -> highways
      -> generateStreetDecorations -> generateHighways -> generateRubble -> generateStuff
    ```

    Explosions and debris run **much later**, back in the top-level chunk pass, after railways and the torch fixup, just before the chunk is flushed. [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

    So anything generated after `generateRuins` in that list is **not** ruined. Street decorations, highways, rubble and stuff objects all land on top of an already-ruined building and survive intact, while explosion damage, running later still, does reach them. A half-collapsed building with pristine street furniture around it is expected. See [The Generation Pipeline](generation-pipeline.md). [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

## You cannot exempt one building from ruin

**A Building asset has no key that protects it from the ruin pass.** No `preventruins`, no `noruin`, and no equivalent under another name. [code review](../examples/claim-tests.md#dmg-3){.v .v-c}

| What you want | How to get it |
|---|---|
| A specific landmark left intact | Place it through a [Predefined City](../reference/predefined.md) and set `preventruins: true` on that entry. The only per-building exemption in the mod [game test](../examples/claim-tests.md#pre-3){.v .v-g} |
| Fewer ruined buildings everywhere | Lower `ruinChance` in the [Profile](../reference/profile.md) |
| No ruined buildings at all | Set `ruinChance` to `0` |
| Specific blocks to survive | Add them to the `lostcities:notbreakable` tag. That protects the blocks, not the building [code review](../examples/claim-tests.md#dmg-1){.v .v-c} |
[code review](../examples/claim-tests.md#dmg-3){.v .v-c}

!!! note "Ruin chance is profile-wide and cannot vary by city style"
    A city style can override `explosionchance`, and there is no city style key for ruin chance, so one district cannot be ruined while another stays pristine through city styles. A predefined city is the only per-place control. [code review](../examples/claim-tests.md#dmg-4){.v .v-c}

    The asymmetry is easy to miss, because the two are usually described together even though they run in different phases. [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

## See also

- [Profile Reference](../reference/profile.md#explosions) for every key named above
- [Palette Reference](../reference/palette.md) for the `damaged` key and block tags
- [The Generation Pipeline](generation-pipeline.md) <!-- noclaim -->
