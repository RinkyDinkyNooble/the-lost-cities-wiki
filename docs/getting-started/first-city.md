# Your First Custom City

!!! tip "TL;DR"
    Six files plus one config line gets a building of your own generating in a real world. This page writes all seven, in the order you would actually write them, and ends with a command that proves it worked.

Everything here is in the repo as a complete, working datapack: [the example bundle](../examples/index.md). Copy that if you would rather read finished files than build them up.

## What you are making

A glass-and-concrete tower that takes over most of the buildings in a city, in a namespace called `mycity`. It is deliberately plain, the point is the wiring, not the architecture.

## The minimum viable set

This is the part nobody states, so: to get one custom building into a world you need **six** content files and **one** config line.

| # | File | Why it is needed |
|---|---|---|
| 1 | a **Palette** | maps characters to blocks |
| 2 | a **Part** | the actual 16×16×6 block grid |
| 3 | a **Building** | stacks parts into a structure |
| 4 | a **City Style** | tells the city your building exists |
| 5 | a **World Style** | tells the world that city style exists |
| 6 | a **Profile** | tells a dimension which world style to use |
| 7 | `common.toml` | maps a dimension to that profile |

Skip any one and nothing happens, usually with no error at all. That silence is why this page exists.

!!! warning "Two things worth knowing before you start"
    - **Assets load once, when the world loads.** `/reload` does nothing. See [Seeing your changes](../tooling/commands.md#seeing-your-changes).
    - **Already-generated chunks never change.** Test in a fresh world, or travel somewhere you have never been.

## Where the files go

```
<world>/datapacks/first-city/
  pack.mcmeta
  data/mycity/lostcities/<type>/<name>.json

config/lostcities/profiles/mycity.json
config/lostcities/common.toml
```

Note there is **one** `lostcities` in the datapack path, not two. The mod's own files look doubled (`data/lostcities/lostcities/...`) only because its pack namespace happens to match the registry namespace. See [Namespaces](namespaces.md#the-exact-folder-layout).

```json title="pack.mcmeta"
{
  "pack": {
    "pack_format": 15,
    "description": "Lost Cities wiki: first custom city example"
  }
}
```

## 1. The palette

Characters to blocks. Five entries is enough.

```json title="data/mycity/lostcities/palettes/tower.json"
{
  "palette": [
    { "char": "α", "block": "minecraft:light_gray_concrete",
      "damaged": "minecraft:cracked_stone_bricks" },
    { "char": "β", "block": "minecraft:light_blue_stained_glass" },
    { "char": "γ", "block": "minecraft:smooth_stone" },
    { "char": "δ", "block": "minecraft:cobblestone" },
    { "char": "ε", "block": "minecraft:bookshelf" }
  ]
}
```

Greek letters on purpose. Your palette is merged with the mod's, collisions silently overwrite each other, and the mod already claims most printable ASCII. See [What counts as a valid character](../reference/palette.md#what-counts-as-a-valid-character).

`damaged` is what `α` turns into when this building is ruined. Optional, but it is one line and ruins look much better with it.

## 2. The part

A part is one chunk footprint, one floor tall: **16 wide, 16 deep, 6 layers**. `slices` runs bottom to top. Every row must be exactly 16 characters. A space is air.

This is the whole file, exactly as it ships in [the example bundle](../examples/index.md). Nothing is left out, because the row lengths are the part of this you most need to see.

```json title="data/mycity/lostcities/parts/tower_floor.json"
{
  "xsize": 16,
  "zsize": 16,
  "refpalette": "mycity:tower",
  "slices": [
    [
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ",
      "γγγγγγγγγγγγγγγγ"
    ],
    [
      "αααααααααααααααα",
      "α              α",
      "α              α",
      "α  εε          α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "αααααααααααααααα"
    ],
    [
      "ααααββββββββαααα",
      "α              α",
      "α              α",
      "α              α",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "α              α",
      "α              α",
      "α              α",
      "ααααββββββββαααα"
    ],
    [
      "ααααββββββββαααα",
      "α              α",
      "α              α",
      "α              α",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "β              β",
      "α              α",
      "α              α",
      "α              α",
      "ααααββββββββαααα"
    ],
    [
      "αααααααααααααααα",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "αααααααααααααααα"
    ],
    [
      "αααααααααααααααα",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "α              α",
      "αααααααααααααααα"
    ]
  ]
}
```

Reading it bottom to top:

| Layer | What it is |
|---|---|
| 0 | A solid `γ` slab. This is the floor you stand on. |
| 1 | The `α` perimeter wall, hollow inside, with two `ε` bookshelves as interior detail. |
| 2 and 3 | The `α` wall with a band of `β` glass, which is the window strip. |
| 4 and 5 | Plain `α` wall again, closing the storey off. |

Each layer is 16 rows, and each row is 16 characters. Count one and you have counted them all.

!!! danger "Count characters, not letters"
    Nothing checks row lengths. A row one character short does not error, it shifts every block after it in that layer and comes out as a diagonal smear. And length is counted in UTF-16 units, so an emoji counts as **two** even though your editor and your script both say one. Generate these files with a script and count carefully. See [Part](../reference/part.md).

Make a second part, `tower_top.json`, the same way, with a solid roof layer at the top. That is the one that caps the building.

## 3. The building

Stacks parts. `filler` is required.

```json title="data/mycity/lostcities/buildings/tower.json"
{
  "filler": "δ",
  "rubble": "δ",
  "parts": [
    { "part": "mycity:tower_top", "top": true },
    { "part": "mycity:tower_floor" }
  ]
}
```

Read this as a list of candidates, not a stack. For each level, the generator collects every entry whose conditions pass and picks one. `tower_top` only matches the topmost level. `tower_floor` has no conditions, so it matches **everything**, including the top.

!!! danger "The unconditioned entry is what stops the most common crash"
    Your building's height comes from the [Profile](../reference/profile.md), not from your building. If a level ever has no matching part, generation throws `Misconfiguration! Floor were generated for a building where no part condition matches!`.

    Always keep at least one part reference with no condition keys. Full explanation at [Floor coverage](../reference/building.md#floor-coverage-the-most-common-crash).

`filler` seats the building into uneven terrain and skirts its cellars. It must be a character your palette defines. See [Filler](../reference/building.md#filler-what-it-is-and-why-it-is-required).

## 4. The city style

```json title="data/mycity/lostcities/citystyles/mycity.json"
{
  "inherit": "citystyle_common",
  "style": "standard",
  "buildingsettings": { "buildingchance": 0.6 },
  "selectors": { "buildings": [ { "factor": 20.0, "value": "mycity:tower" } ] }
}
```

`inherit: "citystyle_common"` is doing a lot of work: it hands you every street, park, corridor, rail and sphere block character the generator needs. Write a city style from scratch and you have to supply all of those yourself.

!!! warning "Selectors add, they never replace"
    You did **not** replace the vanilla building list. `citystyle_common` lists 8 buildings totalling 2.2 in weight, and yours is appended to them. `factor: 20.0` is why your tower wins about 90% of the time rather than 1 in 9.

    There is no way to narrow an inherited list. If you want *only* your buildings, do not inherit from a style that has any. See [Inheritance](../reference/citystyle.md#inheritance).

## 5. The world style

```json title="data/mycity/lostcities/worldstyles/mycity.json"
{
  "outsidestyle": "outside",
  "citystyles": [ { "factor": 1.0, "citystyle": "mycity:mycity" } ]
}
```

Only two keys are required. `multisettings`, `settings`, and `parts` all fall back to working defaults, and `scattered` and `cityspheres` are simply off when absent.

Note `mycity:mycity`: the namespace **and** the file name. A bare `mycity` would be read as `lostcities:mycity` and silently find nothing. This is the single most common way custom content fails to load.

## 6. The profile

Profiles are **config, not datapack**. This one goes in `config/lostcities/profiles/mycity.json`.

```json title="config/lostcities/profiles/mycity.json"
{
  "lostcity": {
    "worldStyle": "mycity:mycity",
    "description": "First custom city example",
    "buildingMinFloors": 2,
    "buildingMaxFloors": 5,
    "ruinChance": 0.2
  },
  "cities": { "cityChance": 0.05 }
}
```

Every key is optional except, in practice, `worldStyle`. `cityChance: 0.05` is five times the default, so you do not have to fly far to find a city.

!!! danger "Never edit a built-in profile file"
    The mod **rewrites all 17 built-in profiles on every single launch**, not just the first. Any edit you make to `wasteland.json` or `default.json` is silently gone next time the game starts.

    Files with names the mod does not ship are left alone. Always use your own name, like `mycity.json` here.

!!! tip "Start from a real one"
    `/lostcities saveprofile <name>` writes a fully populated profile with every key at its default, which beats typing one from scratch. See [Commands](../tooling/commands.md).

## 7. Wire it to a dimension

```toml title="config/lostcities/common.toml"
dimensionsWithProfiles = [
    "lostcities:lostcity=mycity"
]
```

Format is `<dimension id>=<profile name>`. This line is the actual switch. Without it, everything above is inert.

## Check that it worked

Restart, load the world, then:

```
/lostcities locate mycity:tower
```

Spirals out up to 30 chunks and reports coordinates of the first matches in chat. Matches mean the whole chain resolved.

If it finds nothing, go stand in a city chunk and run:

```
/lostcities debug
```

That dumps every decision the generator made for that chunk to the **server console** (not chat): profile name, city style, building type, floor count. It tells you exactly which link in the chain broke.

## When nothing happens

In the order worth checking:

1. **Did you restart?** `/reload` does not reload these files.
2. **Are you in new chunks?** Existing ones are saved and never regenerate.
3. **Did you leave a namespace off?** `"mycity"` means `lostcities:mycity`. Missing content is silent.
4. **Is the profile actually attached?** `/lostcities debug` prints the profile name it is using.
5. **Did the profile file survive?** If you named it after a built-in, it was overwritten on launch.

An actual error message instead of silence is good news. Look it up in [Error Messages](../troubleshooting/errors.md).

## Next

- Give it cellars and a proper roof: [Building](../reference/building.md)
- Make the material vary without authoring more parts: [Variant](../reference/variant.md)
- Change the streets too: [Streets, Highways, Rails & Monorails](../concepts/infrastructure-parts.md)
- Understand what the chain is doing: [The Content Model](content-model.md)
