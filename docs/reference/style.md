---
claims: verified
---

# Style Reference

!!! tip "TL;DR"
    `styles/<name>.json` is not a visual theme. It is a **random palette picker**. Each slot rolls one palette from a weighted list, and the mod merges every rolled palette. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

## Keys

| Key [code review](../examples/claim-tests.md#ref-1){.v .v-c} | Required | Meaning |
|---|---|---|
| `randompalettes` | **yes** | A list of lists. Each inner list is one slot, and every slot rolls independently |

Each entry inside a slot takes two keys, both required: [code review](../examples/claim-tests.md#ref-1){.v .v-c}

| Key | Required | Meaning [code review](../examples/claim-tests.md#ref-1){.v .v-c} |
|---|---|---|
| `palette` | **yes** | The name of a [Palette](palette.md). Resolved with `getOrThrow`, so a wrong namespace throws rather than falling through to another choice |
| `factor` | **yes** | The weight of this choice within its slot. Weights are relative to the others in the same slot, not to 1.0 |

## Example: two independent slots

```json
{
  "randompalettes": [
    [
      { "factor": 1.0, "palette": "bricks_standard" },
      { "factor": 1.0, "palette": "bricks_gray" }
    ],
    [
      { "factor": 3.0, "palette": "glass_pane" },
      { "factor": 1.0, "palette": "glass_full" }
    ]
  ]
}
```

The two slots roll independently and the results are merged. The wall slot picks `bricks_standard` or `bricks_gray` with equal probability, and the glass slot picks `glass_pane` three times as often as `glass_full`. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

Every palette named here goes through `getOrThrow`, so a name in the wrong namespace throws rather than falling through to the next choice. [code review](../examples/claim-tests.md#ns-4){.v .v-c}

## Two styles are in play, and which one applies depends on the chunk

A Style is named in two different places, and a world uses both at once: [game test](../examples/claim-tests.md#bhv-5){.v .v-g}

| Named by | Key | Applies to [game test](../examples/claim-tests.md#bhv-5){.v .v-g} |
|---|---|---|
| [City Style](citystyle.md) | `style` | Chunks that are city chunks |
| [World Style](worldstyle.md) | `outsidestyle` | Every chunk that is not |

A chunk compiles its palette from one or the other, never from both, so a character
defined in only one of them resolves in half the world and is undefined in the rest. [game test](../examples/claim-tests.md#bhv-5){.v .v-g}

!!! danger "A city sphere's shell is drawn on non-city chunks"
    Which makes it the case that catches people out. The shell character comes from
    the city style, and it is placed on chunks that resolve against the **outside**
    style. Define it only in the city style's `style` and the lookup returns null,
    and the sphere feature has no null check: the **server** goes down with a bare
    `NullPointerException` during feature placement, naming no file, no part and no
    character. [game test](../examples/claim-tests.md#bhv-5){.v .v-g}

    A pack that uses its own characters anywhere outside a building wants the same
    palette layered into both styles. [game test](../examples/claim-tests.md#bhv-5){.v .v-g}

## When the roll happens

Every slot rolls **once per chunk**, from a random source seeded by the chunk coordinate, so the same chunk in the same world always lands on the same palette. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

A normal building occupies one chunk, which makes that the same as once per building. Two neighbouring buildings under one city style do not have to match, which is where a city gets its variety without anyone authoring every combination. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

!!! note "A multi-building rolls once per chunk, not once per structure"
    Each chunk of a [Multi-Building](multibuilding.md) rolls its palette on its own, so the quarters of a large structure can land on different palettes. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    A multi-chunk structure that has to be uniform needs its parts to carry a `refpalette`, which takes precedence over the style's palettes. See [Collisions and merge order](palette.md#collisions-and-merge-order). [game test](../examples/claim-tests.md#pal-1){.v .v-g}

## See also

- [The Content Model](../getting-started/content-model.md)
- [Palette Reference](palette.md) for what a resolved palette contains
- [City Style Reference](citystyle.md) and [World Style Reference](worldstyle.md), the two assets that point at a Style <!-- noclaim -->
