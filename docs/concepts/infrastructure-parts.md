# Streets, Highways, Rails & Monorails

!!! tip "TL;DR"
    Streets, highways, rails, and monorails each expect a set of default **part names** to exist. You don't have to build these, but if you skip them, generation has nothing to place. Override the names via `parts` in a [World Style](../reference/worldstyle.md) or the nested `parts` under a City Style's `streetblocks`.

This is a contract, not a suggestion. If a part named `street_full` doesn't exist and nothing overrides that name, that piece of infrastructure just doesn't generate.

## Streets

| Default part name | Shape |
|---|---|
| `street_full` | Open on all sides |
| `street_straight` | Through-street |
| `street_end` | Dead end |
| `street_bend` | Corner |
| `street_t` | T-junction |
| `street_none` | No connections |
| `street_all` | 4-way junction |

## Highways

Six names, three shapes × normal/bidirectional (`_bi`):

`highway_tunnel`, `highway_open`, `highway_bridge`, `highway_tunnel_bi`, `highway_open_bi`, `highway_bridge_bi`

## Monorails

`monorails_both`, `monorails_vertical`, `monorails_station`

## Railways

Sixteen names covering stations and track orientations: underground/open/open-roof stations, underground stairs, staircases (regular and surface), horizontal rails (plain, end, over water), vertical rails (plain, over water), a 3-way split, a bend, a flat piece, and two downward-sloping pieces.

## Overriding names

```json title="In a World Style"
{
  "parts": {
    "highways": { "tunnel": "my_highway_tunnel" }
  }
}
```

Only override what you're actually replacing, everything else keeps the default name.

## See also

- [World Style Reference](../reference/worldstyle.md)
- [City Style Reference](../reference/citystyle.md)
