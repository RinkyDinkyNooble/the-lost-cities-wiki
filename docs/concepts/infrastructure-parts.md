# Streets, Highways, Rails & Monorails

!!! tip "TL;DR"
    Streets, highways, rails, and monorails each expect a set of default **part names** to exist. You can point any of those names at your own part instead, and for streets, highways, and railways you can supply a **list** of parts to pick from at random. Monorails accept only one.

This is a contract, not a suggestion. If a part named `street_full` doesn't exist and nothing overrides that name, that piece of infrastructure doesn't generate.

## Yes, you can have more than one variation

The single most common assumption is that each street shape is locked to exactly one part. It isn't. **Streets, highways, and railways accept either a single name or a list of names**, and the mod picks one at random each time it places that piece:

```json title="Both forms are valid in the same object"
{
  "streetblocks": {
    "parts": {
      "full":     ["street_full", "mypack:street_full_cracked", "mypack:street_full_grassy"],
      "straight": "mypack:street_straight_wide"
    }
  }
}
```

| Category | Multiple variants? | How one is chosen |
|---|---|---|
| Streets | **Yes**, list or single string | Uniform random, every entry equally likely |
| Highways | **Yes**, list or single string | Uniform random |
| Railways | **Yes**, list or single string | Uniform random |
| Monorails | **No**, single string only | n/a |

Passing a list to a monorail key is a datapack load error, not a silent fallback.

!!! note "There's no weighting"
    Unlike [building selectors](../reference/citystyle.md) or [Conditions](../reference/condition.md), these lists have no `factor` field. Every entry in the list is equally likely. If you want one variant to be rare, you can't express that here, list it once among many common ones, or use a [Variant](../reference/variant.md) inside the palette instead (see [below](#often-a-better-answer-vary-the-material-not-the-part)).

Adjacent chunks roll independently, with no attempt to match neighbours. Two touching straight-street chunks can and often will pick different variants, so **variants need to line up seamlessly at chunk edges** or the seams will be obvious. Don't count on predicting which variant a given chunk gets before you visit it; once a chunk is generated it's saved, so it won't change afterward.

## Where each override goes

The two families live in **different files**, which is easy to get wrong:

=== "Streets → City Style"

    ```json title="citystyles/<name>.json"
    {
      "streetblocks": {
        "parts": {
          "full":     ["street_full"],
          "straight": ["street_straight"],
          "end":      ["street_end"],
          "bend":     ["street_bend"],
          "t":        ["street_t"],
          "none":     ["street_none"],
          "all":      ["street_all"]
        }
      }
    }
    ```

    Because streets are a City Style property, and a [World Style](../reference/worldstyle.md) can pick city styles per biome, **streets can vary by biome**: give `citystyle_desert` its own `streetblocks.parts` and desert cities get different roads.

=== "Highways, rails, monorails → World Style"

    ```json title="worldstyles/<name>.json"
    {
      "outsidestyle": "outside",
      "citystyles": [ ... ],
      "parts": {
        "highways": {
          "tunnel": ["highway_tunnel", "mypack:highway_tunnel_lit"],
          "open":   "highway_open"
        },
        "railways": {
          "railshorizontal": ["rails_horizontal", "mypack:rails_horizontal_broken"]
        },
        "monorails": {
          "both": "mypack:monorails_both_neon"
        }
      }
    }
    ```

    These are one set per world style, resolved with no biome input, so **highways, rails, and monorails cannot vary by biome**. The only way to differentiate them is a separate world style entirely.

## The part name keys

Any key you leave out keeps its default part name. The keys are not always spelled like the part names they default to.

### Streets

| Key | Default part | Used when |
|---|---|---|
| `full` | `street_full` | Full street chunk |
| `straight` | `street_straight` | 2 connections, opposite sides |
| `bend` | `street_bend` | 2 connections, adjacent sides |
| `t` | `street_t` | 3 connections |
| `all` | `street_all` | 4 connections (crossroads) |
| `end` | `street_end` | 1 connection |
| `none` | `street_none` | 0 connections |

The key is literally `"t"`, not `"tsplit"`.

### Highways

| Key | Default part |
|---|---|
| `tunnel` | `highway_tunnel` |
| `open` | `highway_open` |
| `bridge` | `highway_bridge` |
| `tunnel_bi` | `highway_tunnel_bi` |
| `open_bi` | `highway_open_bi` |
| `bridge_bi` | `highway_bridge_bi` |

`_bi` ("bidirectional") is used where an X highway and a Z highway meet at the same level.

### Railways

Sixteen keys. Note they're all lowercase with no separators, while the default part names they map to are snake_case, an easy source of silent typos.

| Key | Default part |
|---|---|
| `stationunderground` | `station_underground` |
| `stationopen` | `station_open` |
| `stationopenroof` | `station_openroof` |
| `stationundergroundstairs` | `station_underground_stairs` |
| `stationstaircase` | `station_staircase` |
| `stationstaircasesurface` | `station_staircase_surface` |
| `railshorizontal` | `rails_horizontal` |
| `railshorizontalend` | `rails_horizontal_end` |
| `railshorizontalwater` | `rails_horizontal_water` |
| `railsvertical` | `rails_vertical` |
| `railsverticalwater` | `rails_vertical_water` |
| `rails3split` | `rails_3split` |
| `railsbend` | `rails_bend` |
| `railsflat` | `rails_flat` |
| `railsdown1` | `rails_down1` |
| `railsdown2` | `rails_down2` |

Surface stations additionally get a 50/50 coin flip between the `stationopen` and `stationopenroof` lists before a variant is drawn from whichever list won.

### Monorails

| Key | Default part | List allowed |
|---|---|---|
| `both` | `monorails_both` | No |
| `vertical` | `monorails_vertical` | No |
| `station` | `monorails_station` | No |

## Rules your custom parts must follow

!!! danger "A typo in a part name fails in two very different ways"
    | Category | If the named part doesn't exist |
    |---|---|
    | **Streets** | A warning is logged, and **that chunk simply gets no street layer**. No crash, no fallback to the default part, just a gap in the road. In a list of 3 where one name is wrong, roughly 1 in 3 of those street chunks silently comes out broken. |
    | **Highways, railways, monorails** | Chunk generation throws. Loud, but at least obvious. |

    There is never a fallback to the default part name. Check your spelling, and remember a bare name means `lostcities:<name>`, so your own parts need your namespace (see [Namespaces](../getting-started/namespaces.md)).

**Parts must be exactly 16×16.** `xsize` and `zsize` other than 16 parse without complaint but generate corrupted output: rotation math assumes 16, and writes past column 15 wrap back around into the same chunk instead of spilling into the next one. All 32 default infrastructure parts are 16×16.

**Author variants in the same orientation as the part they replace.** The mod picks the rotation from the road layout, not from your part, so a `street_bend` variant gets rotated by the same rule the built-in one does. If your bend is drawn facing a different way than the original, it will be rotated wrongly at three quarters of the corners in your world. `full`, `none`, and `all` are never rotated, so those can safely be asymmetric.

**Reuse the palette characters the category expects.** Street parts use the street/streetbase/streetvariant characters, highways expect their support character, rail parts expect the rail palette. A part referencing a character its palette doesn't define throws during generation.

## Often a better answer: vary the material, not the part

If the goal is "my streets look too repetitive," authoring several near-identical parts is usually the harder path. The [Style](../reference/style.md) and [Variant](../reference/variant.md) systems already randomize *blocks* underneath a single part:

```json title="variants/blackstone.json (shipped with the mod)"
{
  "blocks": [
    { "random": 32,   "block": "minecraft:polished_blackstone_bricks" },
    { "random": 32,   "block": "minecraft:cracked_polished_blackstone_bricks" },
    { "random": 1000, "block": "minecraft:polished_blackstone" }
  ]
}
```

That gives per-block variation with weighting, which flat part lists can't do, and it costs one file instead of several parts. Use part lists when the *shape* differs (a roundabout, a collapsed section, a checkpoint), and variants when only the *material* differs.

!!! note "The mod ships zero examples of the list form"
    None of the built-in world styles or city styles override these part names at all, they all run on exactly one variant per slot. The feature is real and present in the code, it just has no demonstration in the default content, which is why it's widely assumed not to exist.

## An inheritance trap for street parts

City style `inherit` handles `streetblocks.parts` as one unit: writing **any** `parts` block at all, even a partial one, stops the parent's `parts` from being inherited. Keys you didn't list fall back to the hardcoded defaults, not to the parent's overrides.

If a parent city style overrides `full` and `bend`, and your child overrides only `full`, the child's `bend` reverts to the built-in `street_bend`, it does not keep the parent's. Restate every key you want to keep. See [City Style: Inheritance](../reference/citystyle.md#inheritance).

## See also

- [World Style Reference](../reference/worldstyle.md)
- [City Style Reference](../reference/citystyle.md)
- [Building Part Reference](../reference/part.md)
