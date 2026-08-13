# Condition Reference

!!! tip "TL;DR"
    `conditions/<name>.json` holds a weighted table that picks a value based on where you are. A [Building](building.md) reuses the same test keys on its part list, so this page covers both.

!!! note "`belowpart` needs 7.4.12"
    The key was added in 7.4.12 and is absent in 8.2.2. See
    [Key availability](../versions/key-availability.md).

## File shape

```json
{
  "values": [
    { "factor": 1.0, "value": "some_string", "inbiome": "minecraft:desert" }
  ]
}
```

The mod collects every entry whose tests pass, then picks one `value` at random. `factor` weights that pick. If no entry matches, the condition returns nothing.

!!! note "Weighted here, unweighted in a Building"
    A Building reuses these test keys but not the weighting. A Condition entry requires `factor` and weights the pick by it. A Building part entry has no `factor` key at all, so every matching part is equally likely.

## The shared test keys

A Condition entry and a Building part entry accept the same 13 test keys.

| Key | Type | Meaning |
|---|---|---|
| `top` | bool | If `true`, matches only when the floor index is at or above the building's top floor. If `false`, matches every other floor. |
| `ground` | bool | If `true`, matches only floor index 0. If `false`, matches every other floor. |
| `cellar` | bool | If `true`, matches only a negative floor index. If `false`, matches index 0 and above. |
| `isbuilding` | bool | If `true`, matches only where a building stands. If `false`, matches only where none does. |
| `issphere` | bool | If `true`, matches only inside a city sphere. If `false`, matches only outside one. |
| `floor` | int | Matches when the floor index equals this number exactly. |
| `chunkx` | int | Matches when the absolute chunk X coordinate equals this number. |
| `chunkz` | int | Matches when the absolute chunk Z coordinate equals this number. |
| `range` | string | Matches when the floor index falls between the two numbers, including both ends. |
| `inpart` | string or list | Matches when the current part name is in this set. |
| `belowpart` | string or list | Matches when the part directly below is in this set. |
| `inbuilding` | string or list | Matches when the current building name is in this set. |
| `inbiome` | string or list | Matches when the current biome is in this set. |

Every key is optional.

**Setting several keys on one entry means all of them must pass.** The mod chains tests with a logical AND and never with an OR. To express "either A or B", write two separate entries.

An entry with no test keys always matches. That is the standard way to write a fallback. An unconditioned entry guarantees that something always matches, which is what prevents the [missing-part crash](building.md#floor-coverage-the-most-common-crash) on a building.

## Writing `range`

`range` is a string holding two integers separated by a comma.

```json
{ "range": "9,12" }
```

Both ends are included, so this matches floor indices 9, 10, 11 and 12. Negative numbers work the same way. `"-2,-1"` matches the two deepest cellars.

!!! warning "A malformed `range` either throws or is silently misread"
    The mod splits the string on commas, then reads the first two pieces as integers. It throws `Bad range specification: <l1>,<l2>!` when that fails.

    | You write | Result |
    |---|---|
    | `"9,12"` | Matches floors 9 to 12. |
    | `"9"` | Throws. There is no second number. |
    | `"9, 12"` | Throws. The space makes `" 12"` a non-number. |
    | `"abc,def"` | Throws. Neither piece is a number. |
    | `"1,2,3"` | **Does not throw.** The mod uses `1,2` and discards the `3`. |

    The last row is the dangerous one. A third number produces no error and no log line, and the floor range you get is not the one you wrote.

!!! note "`l1` and `l2` are not something you type"
    The names `l1` and `l2` appear only in the mod's error message, `Bad range specification: <l1>,<l2>!`, where they stand in for the two numbers. Write real integers.

## Example

```json
{
  "values": [
    { "factor": 3.0, "value": "desert_wall", "inbiome": ["minecraft:desert", "minecraft:badlands"] },
    { "factor": 1.0, "value": "default_wall" }
  ]
}
```

In a desert or badlands biome both entries match, so `desert_wall` wins 3 times out of 4. In every other biome the first entry fails its `inbiome` test, so `default_wall` is the only candidate and always wins.

## See also

- [Building Reference](building.md) for how these same keys gate part selection
- [Matchers](../concepts/matchers.md) for the different `if_all` and `if_any` shape used elsewhere
