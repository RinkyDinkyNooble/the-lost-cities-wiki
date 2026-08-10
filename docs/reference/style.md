# Style Reference

!!! tip "TL;DR"
    `styles/<name>.json` is not a visual theme. It is a **random palette picker**. Each slot rolls one palette from a weighted list, and the mod then merges every rolled palette.

## Keys

| Key | Required | Meaning |
|---|---|---|
| `randompalettes` | **yes** | A list of lists. Each inner list is one slot, holding weighted `{factor, palette}` choices. |

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

The mod rolls the two slots independently, then merges the results.

- **The wall slot** picks `bricks_standard` or `bricks_gray`, with equal probability.
- **The glass slot** picks `glass_pane` 3 times as often as `glass_full`.

## When the roll happens

The mod rolls every slot **once per chunk**, from a random source seeded by the chunk coordinate. The result is therefore stable: the same chunk in the same world always produces the same palette.

For a normal building, which occupies one chunk, that is the same as once per building. Two neighbouring buildings in the same city style do not have to match, and that is the point. It gives a city visual variety without you authoring every combination.

!!! note "A multi-building rolls once per chunk, not once per structure"
    Because the roll is per chunk, each chunk of a [Multi-Building](multibuilding.md) rolls its palette independently. The quarters of a large structure can land on different palettes.

    If you need a multi-chunk structure to be uniform, do not rely on the Style layer to keep it consistent. Give its parts a `refpalette` of their own, which takes precedence over the Style's palettes. See [Collisions and merge order](palette.md#collisions-and-merge-order).

## See also

- [The Content Model](../getting-started/content-model.md)
- [Palette Reference](palette.md) for what a resolved palette contains
- [City Style Reference](citystyle.md) for what points at a Style
