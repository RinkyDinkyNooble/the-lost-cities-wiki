# Building Reference

!!! tip "TL;DR"
    `buildings/<name>.json`. A vertical stack: cellars, ground floor, floors, top. Each slot picks from a list of candidate parts, optionally filtered by [conditions](condition.md).

## Fields

| Key | Required | Default | Meaning |
|---|---|---|---|
| `filler` | **yes** | | Single-char filler block. |
| `rubble` | no | | Single-char rubble block. |
| `refpalette` | no | | Shared palette name. |
| `palette` | no | | Embedded palette, instead of `refpalette`. |
| `mincellars` / `minfloors` / `maxcellars` / `maxfloors` | no | unset | Floor/cellar count bounds. |
| `allowDoors` | no | `true` | camelCase, unlike most of this file. |
| `allowFillers` | no | `true` | Also camelCase. |
| `overrideFloors` | no | `false` | Also camelCase. |
| `preferslonely` | no | `0` | Lowercase. Spacing/isolation bias for placement. |
| `parts` | **yes** | | List of part references (see below). |
| `parts2` | no | | A second, independent list of part references. |

!!! warning "Casing isn't consistent here either"
    `allowDoors`, `allowFillers`, `overrideFloors` are camelCase. `filler`, `rubble`, `preferslonely` are lowercase, in the same file. Same rule as [City Style](citystyle.md): copy the exact key, don't guess.

## Part references

Each entry in `parts` (or `parts2`) is a part name plus the full [condition test field set](condition.md#the-shared-test-fields):

```json
{ "part": "apartment_floor", "floor": 2 }
```

At generation time, every entry whose conditions match the current slot is collected, and one is picked at random. This is the real mechanism behind "unique vs. generic floor variant": it's not just floor-number matching, it can key off chunk position, biome, or the part below.

## Example: two candidates for the same floor

```json
{
  "filler": "#",
  "parts": [
    { "part": "apartment_floor_a", "floor": 2 },
    { "part": "apartment_floor_b", "floor": 2 }
  ]
}
```

Floor 2 randomly becomes `apartment_floor_a` or `apartment_floor_b`, 50/50 (no `factor` field here, so it's a plain random pick among matches, unlike `Condition`'s weighted pick).

## See also

- [Building Part Reference](part.md) for what a part actually contains
- [Condition Reference](condition.md) for the full test field table
