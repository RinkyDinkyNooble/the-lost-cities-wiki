# The Generation Pipeline

!!! info "You do not need this page to build a custom city"
    Everything required to author content lives in [Reference](../reference/profile.md) and [Concepts](../concepts/matchers.md). This page explains the order things happen in during generation, useful for understanding *why* certain interactions play out the way they do, not for authoring content itself.

!!! tip "TL;DR"
    A chunk generates in a fixed order: decide city or not, place the building/street, place rails, fix up torches, then apply explosion/ruin damage, then flush to the world. Damage always happens **after** the building is fully placed, it cannot affect which part variant was chosen.

## Per-chunk order of operations

For a single chunk, roughly in this order:

1. **Structure-avoidance check.** If a vanilla or modded structure already claims this chunk, Lost Cities steps aside rather than overwriting it.
2. **City or non-city chunk.** See [How a Chunk Becomes a City](city-generation.md) for how this gets decided. A city chunk generates a building or street; a non-city chunk gets normal terrain, plus scattered buildings, bridges, and highways if any pass through.
3. **City-sphere center piece**, if this chunk happens to be a sphere's center and the active World Style defines one.
4. **Railways**, then railway dungeons.
5. **Torch attachment fixup.** Torches placed by any part in this chunk do not get their facing decided at placement time, they are queued and resolved afterward by checking which of the four cardinal neighbours (then straight down) actually has a solid block once the whole chunk's geometry exists. This is why a palette's `torch` entries never need an explicit facing.
6. **Damage, ruins, and debris.** See [Damage, Ruins & Explosions](damage-and-ruins.md). This step runs against the fully-placed chunk.
7. **Flush to the world**, then a last pass adds vine overgrowth and anything else deferred to run one tick later.

**The practical consequence of step 6 running last**: ruin and explosion damage can never influence which part, floor, or building variant got selected, that decision is long finished by the time anything breaks. A rare, expensive loot-tier part can still roll, generate in full, and then get partially blown up by an explosion in the same chunk, that is expected, not a bug in either system.

### Inside step 2, for a city chunk

Step 2 is not one action. A city chunk runs this sequence, and the position of `generateRuins` inside it matters:

```
generateBuilding -> generateStreet -> generateRuins -> highway levels
  -> generateStreetDecorations -> generateHighways -> generateRubble -> generateStuff
```

Ruins therefore happen **inside step 2**, not in step 6 with the explosions. Everything after `generateRuins` in that list lands on an already-ruined building and is not itself ruined: street decorations, highways, rubble and stuff objects all survive intact.

Explosion damage in step 6 is the opposite. It runs after all of the above and damages whatever it finds. That is the real difference between the two systems, and it is why the two are worth keeping apart in your head even though they are usually described together.

## From a part's characters to placed blocks

Every part placement, buildings, streets, highways, railways, all of it, funnels through the same block-by-block resolution:

- Each character resolves to a block via the palette, following the [128-slot weighted rule](../reference/palette.md#the-128-slot-rule-for-blocks-and-variant).
- If the part is being placed rotated or mirrored, rotation only applies to blocks in the [`lostcities:rotatable` tag](../reference/palette.md#rotation-and-the-lostcitiesrotatable-tag) (plus rails, always). Covered in full on the Palette page.
- **Air is not always air.** Parts use a placeholder ("hard air") for anything that should be empty *unless* context says otherwise. Depending on which system is placing the part and the current Y versus the world's water level, hard air resolves to real air, water, or stays empty. This, not anything authored in the part itself, is why some building basements fill with water below sea level and others do not, it is decided by the caller placing that part, not by the part's own JSON.
- **Loot, mob spawner, and `tag` characters** dispatch to their own logic, all covered on the [Palette page](../reference/palette.md): loot rolls lazily and only if nothing overwrote that block first, `mob` resolves through a [Condition](../reference/condition.md) rather than being a literal mob ID, and `tag` writes a block entity directly, bypassing normal placement (which is also why the [command-block stair-shape workaround](../advanced/command-blocks.md) works at all).
- **Saplings and flowers** get special-cased on top of normal palette resolution: if foliage is being avoided (`avoidFoliage`, profile- or city-style-level), they are stripped to air instead of placed. Otherwise they are either grown into a full tree shortly after placement or given a random growth stage, controlled by the mod's own configuration rather than anything set per-part.

## See also

- [How a Chunk Becomes a City](city-generation.md)
- [Damage, Ruins & Explosions](damage-and-ruins.md)
- [Palette Reference](../reference/palette.md)
