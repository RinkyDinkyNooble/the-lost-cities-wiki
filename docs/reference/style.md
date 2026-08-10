# Style Reference

!!! tip "TL;DR"
    `styles/<name>.json`. Not a visual theme, a **random palette picker**. Each "slot" rolls one palette from a weighted list, then all rolled palettes merge.

## Fields

| Key | Required | Meaning |
|---|---|---|
| `randompalettes` | **yes** | List of lists. Each inner list is one "slot": `{factor, palette}` weighted choices. |

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

Two slots, rolled independently, then merged:

- **Wall slot**: 50/50 between `bricks_standard` and `bricks_gray`.
- **Glass slot**: `glass_pane` is 3× as likely as `glass_full`.

Each roll happens once per generated building. All buildings using the same city style do not necessarily match each other, that is the point, it is what gives a city visual variety without hand-authoring every combination.

## See also

- [The Content Model](../getting-started/content-model.md)
- [Palette Reference](palette.md) for what a resolved palette actually contains
