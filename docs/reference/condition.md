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
| `range` | string `"l1,l2"` | Floor is between l1 and l2, inclusive |
| `inpart` | string or list | Current part name is in this set |
| `belowpart` | string or list | The part directly below is in this set |
| `inbuilding` | string or list | Current building name is in this set |
| `inbiome` | string or list | Current biome is in this set |

All optional. No fields set = always matches.

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
