---
claims: verified
---

# The Generation Pipeline

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This page covers the order things happen in during generation, which explains why certain interactions play out as they do. <!-- noclaim -->

!!! tip "TL;DR"
    A chunk generates in a fixed order: decide city or not, place the building or street, place rails, fix up torches, apply explosion and ruin damage, flush to the world. Damage always happens **after** the building is fully placed, so it cannot affect which part variant was chosen. [code review](../examples/claim-tests.md#pipe-1){.v .v-c}

## Per-chunk order of operations

For a single chunk, roughly in this order: [code review](../examples/claim-tests.md#pipe-1){.v .v-c}

1. **Structure-avoidance check.** A vanilla or modded structure already claiming this chunk makes Lost Cities step aside rather than overwrite it.
2. **City or non-city chunk.** See [How a Chunk Becomes a City](city-generation.md) for how that is decided. A city chunk generates a building or street; a non-city chunk gets normal terrain, plus scattered buildings, bridges and highways where any pass through.
3. **City-sphere centre piece**, where this chunk is a sphere's centre and the active World Style defines one.
4. **Railways**, then railway dungeons.
5. **Torch attachment fixup.** Torches placed by any part in this chunk do not get their facing decided at placement time. They are queued and resolved afterwards by checking which of the four cardinal neighbours, then straight down, actually holds a solid block once the whole chunk's geometry exists. That is why a palette's `torch` entries never need an explicit facing.
6. **Damage, ruins and debris.** See [Damage, Ruins & Explosions](damage-and-ruins.md). This step runs against the fully placed chunk.
7. **Flush to the world**, then a last pass adds vine overgrowth and anything else deferred by a tick. [code review](../examples/claim-tests.md#pipe-1){.v .v-c}

Because step 6 runs last, ruin and explosion damage can never influence which part, floor or building variant was selected. That decision is long finished by the time anything breaks. A rare, expensive loot-tier part can roll, generate in full, and then get partially blown up by an explosion in the same chunk. Expected, not a bug in either system. [code review](../examples/claim-tests.md#pipe-1){.v .v-c}

### Inside step 2, for a city chunk

Step 2 is not one action, and the position of `generateRuins` inside it matters: [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

```
generateBuilding -> generateStreet -> generateRuins -> highway levels
  -> generateStreetDecorations -> generateHighways -> generateRubble -> generateStuff
```

Ruins therefore happen **inside step 2**, not in step 6 with the explosions. Everything after `generateRuins` in that list lands on an already-ruined building and is not itself ruined: street decorations, highways, rubble and stuff objects all survive intact. [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

Explosion damage in step 6 is the opposite. It runs after all of the above and damages whatever it finds. That is the real difference between the two systems, and the reason to keep them apart in your head even though they are usually described together. [code review](../examples/claim-tests.md#pipe-2){.v .v-c}

## From a part's characters to placed blocks

Every part placement, buildings, streets, highways and railways alike, funnels through the same block-by-block resolution. [code review](../examples/claim-tests.md#pipe-1){.v .v-c}

- Each character resolves to a block through the palette, following the [128-slot weighted rule](../reference/palette.md#the-128-slot-rule-for-blocks-and-variant). [game test](../examples/claim-tests.md#pal-3){.v .v-g}
- A part placed rotated or mirrored rotates only the blocks in the [`lostcities:rotatable` tag](../reference/palette.md#rotation-and-the-lostcitiesrotatable-tag), plus rails, which always rotate. Covered in full on the Palette page. [unverified](../examples/claim-tests.md#ref-3){.v .v-u}
- **Air is not always air.** Parts carry a placeholder for anything that should be empty *unless* context says otherwise. Depending on which system is placing the part, and the current Y against the world's water level, that placeholder becomes real air, water, or nothing. This, rather than anything authored in the part, is why some building basements fill with water below sea level and others do not. [code review](../examples/claim-tests.md#pipe-3){.v .v-c}
- **Loot, mob spawner and `tag` characters** dispatch to their own logic, all covered on the [Palette page](../reference/palette.md). Loot rolls lazily and only where nothing overwrote that block first, `mob` resolves through a [Condition](../reference/condition.md) rather than naming an entity, and `tag` writes a block entity directly, bypassing normal placement, which is also why the [command-block stair-shape workaround](../advanced/command-blocks.md) works. [game test](../examples/claim-tests.md#pal-9){.v .v-g} [game test](../examples/claim-tests.md#pal-12){.v .v-g}
- **Saplings and flowers** are special-cased on top of normal palette resolution. Where foliage is being avoided, through `avoidFoliage` at profile or city style level, they are stripped to air instead of placed. Otherwise they are either grown into a full tree shortly after placement or given a random growth stage, controlled by the mod's own configuration rather than anything per-part. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## See also

- [How a Chunk Becomes a City](city-generation.md)
- [Damage, Ruins & Explosions](damage-and-ruins.md)
- [Palette Reference](../reference/palette.md) <!-- noclaim -->
