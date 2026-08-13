# Multi-Building Reference

!!! tip "TL;DR"
    `multibuildings/<name>.json` holds a grid of building names. It occupies several city chunks at once instead of one.

## Keys

| Key | Required | Limits | Meaning |
|---|---|---|---|
| `dimx` / `dimz` | **yes** | 1 or more, and no larger than the `areasize` it is placed with | The grid size, in chunks. |
| `buildings` | **yes** | | A nested list of building names. See [Grid order](#grid-order) below, because it is not laid out the way it looks. |

## Grid order

The mod reads the grid as `buildings[x][z]`. **The outer list is the X axis, and the inner list is the Z axis.**

That is the opposite of how a nested list usually reads. The outer list is not a row running east. Each outer entry is a **column** at one X coordinate, and the entries inside it run north to south.

| Position | Index | Compass corner |
|---|---|---|
| `buildings[0][0]` | x 0, z 0 | North-west |
| `buildings[0][1]` | x 0, z 1 | South-west |
| `buildings[1][0]` | x 1, z 0 | North-east |
| `buildings[1][1]` | x 1, z 1 | South-east |

The mod's own `center.json` follows this. Its entries are named `center00`, `center01`, `center10` and `center11`, which is `center<x><z>`.

!!! warning "Getting the order wrong produces a scrambled building, with no error"
    Nothing validates the grid against the parts it names. If you lay the list out as rows running east, the north-east and south-west chunks swap places. The building generates, no message appears, and the halves do not line up.

## Example

```json
{
  "dimx": 2,
  "dimz": 2,
  "buildings": [
    ["mall_nw", "mall_sw"],
    ["mall_ne", "mall_se"]
  ]
}
```

This is a footprint of 2 by 2 chunks, tiling four separate building definitions into one structure. The first inner list is the western column, running from north to south. Each entry is a normal [Building](building.md) name, referenced the usual [namespaced](../getting-started/namespaces.md) way.

!!! danger "A multi-building larger than its placement area fails the chunk"
    The mod picks a random offset inside a square area of chunks, using `random(areasize - dimx + 1)`. If `dimx` or `dimz` exceeds `areasize`, that bound reaches zero or goes negative and the mod throws `bound must be positive`.

    Two different `areasize` values apply, depending on how the multi-building is reached.

    | Reached through | Setting | Shipped default |
    |---|---|---|
    | A city style's `multibuildings` selector | [World Style](worldstyle.md) `multisettings.areasize` | `10` |
    | A [Scattered Building](scattered.md)'s `multibuilding` | [World Style](worldstyle.md) `scattered.areasize` | `8` |

    A multi-building used both ways has to fit the smaller of the two. Nothing checks this at load. The mod only fails when a chunk in that area generates.

## See also

- [Building Reference](building.md)
- [World Style Reference](worldstyle.md) for the two `areasize` settings
- [Error Messages](../troubleshooting/errors.md) for `bound must be positive`
