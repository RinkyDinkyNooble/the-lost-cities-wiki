# Condition Reference

!!! tip "TL;DR"
    `conditions/<name>.json`: a weighted "pick a value based on where you are" table. The same test fields also show up on a [Building](building.md)'s part list, so this page covers both.

## File shape

```json
{
  "values": [
    { "factor": 1.0, "value": "some_string", "inbiome": "minecraft:desert" }
  ]
}
```

All matching entries get collected, then one `value` is picked at random, weighted by `factor`.

!!! note "Weighted here, unweighted in a Building"
    These same test fields are reused by [Building](building.md) part references, but the selection isn't the same. A `Condition` asset weights its candidates by `factor`. A Building's `parts` list has no `factor` at all, every matching part is equally likely.

## The shared test fields

Used by `Condition` entries and, separately, by every part reference inside a [Building](building.md).

| Key | Type | Meaning |
|---|---|---|
| `top` | bool | Is this the building's topmost segment |
| `ground` | bool | Is this the ground floor (`floor == 0`) |
| `cellar` | bool | Is this a cellar (`floor < 0`) |
| `isbuilding` | bool | Is there a building here at all |
| `issphere` | bool | Is this inside a city sphere |
| `floor` | int | Exact floor number |
| `chunkx` / `chunkz` | int | Exact absolute chunk coordinate |
| `range` | string, e.g. `"9,12"` | Floor is between the two numbers, **inclusive both ends** |
| `inpart` | string or list | Current part name is in this set |
| `belowpart` | string or list | The part directly below is in this set |
| `inbuilding` | string or list | Current building name is in this set |
| `inbiome` | string or list | Current biome is in this set |

All optional. **Setting several fields on one entry means all of them must pass** (they're AND-ed, never OR-ed). To express "either A or B", write two separate entries.

!!! warning "`range` is a string of two integers, and `l1`/`l2` are not literal"
    Write `"range": "9,12"`. Both ends are included, so that matches floors 9, 10, 11 and 12. Negatives work the same way, `"-2,-1"` matches the two deepest cellars.

    If you've seen `l1,l2` written anywhere, that comes from the mod's own error message, `Bad range specification: <l1>,<l2>!`, where they're placeholder names. They are not something you type.

    A single number, three numbers, a non-number, or a stray space all throw that error.

No fields set at all = always matches. That's not a degenerate case, it's the standard way to write a fallback: an unconditioned entry guarantees something always matches, which is exactly what prevents the [missing-part crash](building.md#floor-coverage-the-most-common-crash) on buildings.

## Example

```json
{
  "values": [
    { "factor": 3.0, "value": "desert_wall", "inbiome": ["minecraft:desert", "minecraft:badlands"] },
    { "factor": 1.0, "value": "default_wall" }
  ]
}
```

In a desert or badlands biome, `desert_wall` wins 3-to-1. Elsewhere, only `default_wall` matches at all (the first entry's `inbiome` filters it out), so it always wins there by default.

## See also

- [Building Reference](building.md) for how these same fields gate part selection
- [Matchers](../concepts/matchers.md) for the similar-but-different `if_all`/`if_any` shape used elsewhere
