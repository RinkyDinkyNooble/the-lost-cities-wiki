# The DevTool Commands

Every `/lcdev` command, what each argument means, and what it does to your world.

!!! note "This page documents the companion mod, not Lost Cities"
    `/lcdev` comes from [The Lost Cities - DevTool](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/releases/tag/mod-v1.3.0). Lost Cities' own commands are on [Testing and Debugging Commands](commands.md). Nothing here is a claim about Lost Cities' behaviour, so it carries no verification chips: it describes a tool this wiki ships.

## Everything at a glance

**Every `/lcdev` command needs permission level 2.** That is the operator level, which
a single-player world gets with cheats enabled and a server gives with `op`. It is a
tool for building a pack, not a feature for players: it teleports between dimensions,
writes tens of thousands of blocks, and reads and writes files beside your world.

| Command | What it is for |
|---|---|
| `/lcdev report` | What the generator chose for the chunk you are standing in |
| `/lcdev key <name>` | What a profile key means, its section, type, range and default |
| `/lcdev char <character>` | What a palette character resolves to here |
| `/lcdev block <id>` | Which characters produce a given block here |
| `/lcdev in <asset> char <character>` | The same lookup inside one named asset |
| `/lcdev in <asset> block <id>` | The same, in reverse, inside one named asset |
| `/lcdev workshop go` | Teleport to the workshop dimension |
| `/lcdev workshop leave` | Go back where you ran `go`, or to world spawn if nothing was recorded |
| `/lcdev workshop rows` | Every catalogue row, each one a place to click |
| `/lcdev workshop here` | Which plot you are standing on and what it compiles into |
| `/lcdev workshop build` | Lay the catalogue out, or repaint it |
| `/lcdev workshop grow <row> <plots>` | Make a row longer, or lay out one that is empty |
| `/lcdev workshop clear [confirm [anyway]]` | Empty every plot, after a backup |
| `/lcdev plot get [key]` | What this plot's settings say |
| `/lcdev plot keys` | Every setting this plot accepts, and what each does |
| `/lcdev plot file` | Where this plot's settings file is, click to copy |
| `/lcdev plot resolve <dx> <dz> <level>` | The settings that apply to one chunk on one level |
| `/lcdev plot set <key> <value>` | Set a value for the whole plot |
| `/lcdev plot setchunk <dx> <dz> <key> <value>` | Set it for one chunk of the plot |
| `/lcdev plot setlevel <level> <key> <value>` | Set it for one level of the plot |
| `/lcdev plot clear <key>` | Remove a key from this plot |
| `/lcdev plot show` | Draw where each level starts, on the walkway |
| `/lcdev plot hide` | Rub those markers out |
| `/lcdev mark <key> <value>` | Attach a palette key to the block you are looking at |
| `/lcdev export <name> [-f]` | Compile the workshop into a datapack |
| `/lcdev import <worldstyle> [keep] [run]` | Paste a loaded pack into the workshop |

## On a server

Safe to use, with three things worth knowing.

| | |
|---|---|
| **A client does not need the mod** | The mod declares `IGNORE_ALL_VERSION`, so a vanilla client can join a server running it. Only the Lost Cities menu fixes are client-side, and those are guarded to the client, so a dedicated server never loads them |
| **Output goes to whoever asked** | Command replies are not broadcast to other operators, so two people can work without filling each other's chat |
| **Two people editing one plot** | The settings are files, written per command with no locking, so the last write wins. Different plots are fine; the same plot at the same moment is not |

`build`, `export` and `import` do their work in one go on the server thread, so a
large catalogue is a visible pause rather than a hang. The workshop is one shared
dimension like any other, so two people building in it see each other's work.

## The three words that are not obvious

These three appear across `plot resolve`, `plot setchunk` and `plot setlevel`, and
none of them mean what a coordinate usually means.

| Argument | It is **not** | It **is** | Example |
|---|---|---|---|
| `dx` | A world X coordinate | Chunks **east** from this plot's own corner, starting at 0 | On a 2x3 plot, `dx` is 0 or 1 |
| `dz` | A world Z coordinate | Chunks **south** from this plot's own corner, starting at 0 | On a 2x3 plot, `dz` is 0, 1 or 2 |
| `level` | A Y coordinate | A building level. `0` is the ground floor, `-1` is the first cellar, `2` is the second floor above ground | `-32` to `128` are accepted |

A plot's corner is its lowest x and lowest z chunk, which is the corner nearest the
origin for the building rows and the far corner for the infrastructure rows, since
those grow west. `/lcdev workshop here` prints the corner so you never have to work
it out.

So the command that prompted this page:

```
/lcdev plot resolve 1 1 1
```

reads as **"on the plot I am standing on, show me the settings that apply to the
chunk one east and one south of its corner, on the first floor above ground"**. It
changes nothing. It answers the question "which of my four overlapping settings
actually wins here".

## How settings fold together

A plot can say something once and have it apply everywhere, or say it again for one
chunk or one level. Four scopes, and **the most specific wins**:

```
plot                        every chunk, every level
  plot.levels[n]            every chunk, that level
    chunks[dx,dz]           that chunk, every level
      chunks[dx,dz].levels[n]   that chunk, that level
```

Each scope stores only what differs from the one above it, so the common case, every
building in a 2x2 block sharing a floor count so the whole thing generates as one
structure, is what you get by saying it once.

| To say | Use |
|---|---|
| This building is 4 storeys | `/lcdev plot set floors 4` |
| The north-east chunk of it is 6 | `/lcdev plot setchunk 1 0 floors 6` |
| The ground floor everywhere uses a different palette | `/lcdev plot setlevel 0 palette part` |
| Which of those applies to chunk 1,0 on the ground floor | `/lcdev plot resolve 1 0 0` |

## The workshop

### Getting there

```
/lcdev workshop build
/lcdev workshop go
```

`build` paints the catalogue floors and is safe to run repeatedly: the same
catalogue produces the same plots in the same colours, so it repaints rather than
duplicating. `go` teleports you in.

`/lcdev workshop leave` brings you back. It returns you to where you ran `go`,
recorded on the player before the teleport, so it survives a logout. Running `go`
again while already in the workshop does not overwrite that, which means you cannot
strand yourself by using it twice. With nothing recorded, because you reached the
workshop some other way, it sends you to world spawn rather than to a respawn point:
a respawn point is a bed that may have been broken since.

### Finding your way around

`/lcdev workshop rows` lists every row that is laid out, grouped by family, each one
a **clickable teleport** to its first plot. `/lcdev workshop here` describes the plot
under your feet: its corner, which variation of its row it is, how many variations
that row allows, and whether it compiles into a city style or the world style.

### Adding plots

There is nothing to add. **Every type of plot the format supports already has a
row**, generated from the codec keys the target version declares, so a type you
cannot find is a type Lost Cities does not have. What you add is *more plots of a
type you already have*:

```
/lcdev workshop grow building/1x1 24
/lcdev workshop grow multibuilding/4x6 6
```

Rows start at eight plots. Growing one lays out more and repaints, and an import
grows whatever it needs by itself. Rows only ever get longer, because shortening one
would move every plot after it and orphan whatever was built there.

Two rows behave differently on purpose:

| Row | Behaviour | Why |
|---|---|---|
| The three `monorail/` rows | Stay at one plot, and `grow` refuses | Their codec takes a single name, so a list there is a load error rather than a longer row |
| `multibuilding/` above 3x3 | Declared with no plots until grown | A row reserves its band whether or not it holds plots, so growing one moves nothing that already exists. What an empty row does not have is a painted floor, and laying out every footprint up to 10x10 would paint several thousand chunks of it for shapes most packs never use |

### How large a multibuilding can be

Ten chunks square, and that is Lost Cities' limit rather than the DevTool's. The
world style tiles the world into squares of `areasize` chunks and places each
multibuilding inside one, using `random(areasize - dimx + 1)`. A footprint wider
than its area makes that bound zero or negative and **the mod throws**, so
`areasize` is the ceiling. The shipped world style uses `10`, which is where the
catalogue stops.

[`multisettings` on the World Style page](../reference/worldstyle.md#multisettings)
has the full table. Two of its keys are easy to misread: `minimum` and `maximum` are
**how many** multibuildings are attempted per area, not how large one may be, so
raising them puts more buildings in the world and does nothing about their size.

An export whose largest footprint is wider than the default area widens `areasize`
in the world style it writes. With the catalogue stopping at 10 that never triggers
today, and it is there so a larger catalogue cannot quietly produce a pack that
throws.

### Starting again

An import fills the plots its pack needs and leaves every other plot alone, because
somebody may have built on those by hand. That has a consequence worth knowing:
**importing a second city on top of a first leaves the first one's plots where they
were**, so the workshop holds both and an export writes both into one pack. The
import counts those plots and says so.

```
/lcdev workshop clear
```

On its own this reports what emptying would cost, in plots and blocks, and changes
nothing. Adding `confirm` writes a full backup pack to
`config/lostcitiesdevtool/backups/<timestamp>/` and then empties every plot.

What counts as a plot worth emptying is what is standing on it, read from the world
rather than from its settings file. A plot holding blocks and no settings is still
cleared, and a build taller than its settings describe is cleared to the top of the
build rather than to the top of the asset.

The backup is a real pack, so `/lcdev import` puts it back once it is installed as a
datapack. If the backup cannot be written, the wipe stops rather than going ahead
without one; `clear confirm anyway` is the way past that, and it is two words deep
on purpose.

Two things survive a wipe. The **core settings**, because the namespace and pack name
are yours rather than any imported city's, and the **palette ledger**, so the next
export letters the same blocks the same way instead of producing a whole-file diff.
Rows an import grew go back to their catalogue size.

## Settings on a plot

`/lcdev plot keys` is the one to remember: it lists every setting **that plot**
accepts with an explanation of each, and the list differs by plot. A street plot has
no `factor`, because the codec behind it picks uniform random and has nowhere to put
a weight. A monorail plot has no variation index worth setting. The same text is
what tab completion shows and what is written as a comment into the settings file,
so the three cannot drift apart.

```
/lcdev plot set name tower
/lcdev plot set floors 3
/lcdev plot set tops 4,6
/lcdev plot set citystyles mycity,othercity
/lcdev plot clear tops
```

A list value is comma separated. `/lcdev plot get` with no key prints everything the
plot has; with a key it prints that one. `/lcdev plot file` gives you the path to the
file, which is the truth and is safe to edit by hand.

`name` is the one setting every plot has, because it names every file that plot
compiles into. **Two plots cannot share it**, and an export says so rather than
letting the second quietly replace the first. An import keeps the namespace off the
name, so `mypack:tower` becomes `tower`, unless two packs both call something
`tower`: then both keep their namespace, as `mypack_tower` and `otherpack_tower`,
and the import says which ones it had to rename.

### Seeing where the compiler will cut

```
/lcdev plot show
/lcdev plot hide
```

Levels are stacked, and the roof variations are stacked above them, which saves a
great deal of room and hides where one thing ends and the next begins. `show` draws
that in stained glass **on the walkway around the plot, never inside it**, so a
preview can never overwrite what you built. `hide` removes it.

### Marking a single block

```
/lcdev mark loot minecraft:chests/simple_dungeon
```

Attaches a palette key to the block you are looking at, so that one position becomes
its own palette entry. Accepts `damaged`, `torch`, `variant`, `loot`, `mob` and
`frompalette`.

!!! warning "Marks do not survive a round trip yet"
    An export writes them. An import does not read them back into settings, so a
    marked block returns from `/lcdev import` as the plain block.

## Compiling and opening

```
/lcdev export mypack
/lcdev export mypack -f
```

Writes a complete datapack to `config/lostcitiesdevtool/exports/<name>/`, with the
profile beside it rather than inside it, because a profile is config and not
datapack. An existing export of the same name is an error unless you pass `-f`.

Nothing is written until the whole pack has passed the same checks the mod runs on a
datapack at load time, so a pack that would fail in a world fails here instead,
where the message can name the plot.

```
/lcdev import lostcities:standard
/lcdev import mypack:main keep
```

Pastes a loaded pack into the workshop. The pack has to be loaded with the world,
which is what makes this work with nothing to point at: the mod's own content and
every datapack in the world are equally importable.

| Argument | Meaning |
|---|---|
| `<worldstyle>` | A world style name. A bare name is looked for under `lostcities:` first, then in any single pack that has it. `/lcdev import` with no argument lists what is loaded |
| `keep` | Leave block conversions alone. Without it they run backwards, so a placeholder an export turned into a real block comes back as the placeholder |
| `run` | Let pasted command blocks fire. Without it they arrive holding their command but unable to run |

Both flags may be given together, in either order.

### Blocks that carry NBT

A palette entry may hold a `tag`, a raw NBT compound, and Lost Cities places the
block already carrying it. That is the mechanism behind the command-block technique:
the block arrives holding its command and, with `auto` set, runs where it lands and
turns itself into whatever it was there to place. A pack built that way is mostly
command blocks.

An import carries the tag, and so does an export, so a command block keeps its
command, a chest keeps its loot table and a spawner keeps its mob.

**A pasted command block is left unable to fire unless you ask.** A workshop is not a
world, and forty spawn commands going off while you are looking at a building is not
useful. `run` pastes them live.

### A building whose middle repeats

A building may name several parts for the same level, and a band written as
`range: "9,12"` twice is the pack asking the generator to pick between them on every
level in that band. An import cannot roll dice, so it steps through the candidates by
level. That shows what the building is made of, and does the same thing every time,
so a pack always imports the same way.

!!! note "What an import will not claim"
    Street parts that no city style names are pasted so you can see the roads, and
    marked `skip` so an export leaves them out. A pack falling back to an asset is
    not a pack containing it, and writing them back out would copy Lost Cities' own
    roads into your namespace.

## Asking about characters and blocks

```
/lcdev report
/lcdev char #
/lcdev block minecraft:gold_block
/lcdev in lostcities:building1 char #
```

`report` describes the chunk you are standing in: profile, world style, city style,
building, floor and cellar counts, and the part used on each level. `char` and
`block` look a palette up in both directions, after the merge, so the answer is what
the world will actually place rather than what one file says.

`char` and `block` search every asset the server has loaded, so on a modpack they
can match a great many. They print the first twelve and count the rest, and name up
to five assets that could not be built before counting those too. `in <asset>` is
how you ask about one of them on its own.

`in <asset>` asks the same question of one named asset instead of your surroundings,
which is how you check a building you are not standing in.

!!! tip "The asset comes before the character"
    `/lcdev in <asset> char <c>`, not the other way round. The character argument is
    greedy so that a character can be anything, including a space, which means it has
    to be the last thing on the line.

## Why completion is fast on a big pack

Completing an asset or a world style name means listing what is loaded, and a client
asks for that after every character typed. Doing the listing per keystroke on a
server holding 911 Lost Cities assets cost 99 ms each time, which is close to two
seconds to type one name.

The listing is read once per datapack load and reused, so the same completion costs
a fraction of a millisecond. It is tied to the load rather than to a timer, so
editing a file and running `/reload` rebuilds it and completion sees the change
immediately.

## Profile keys

```
/lcdev key cityChance
```

Prints the section the key belongs to, its type, its range, its default and what it
does, read out of the mod's own config declarations. **The section matters**: a
profile key written in the wrong section is not an error and is not reported, it is
simply never read, and the setting silently does nothing. `cityChance` lives in
`cities`, not in `lostcity`.

## See also

- [Testing and Debugging Commands](commands.md), for Lost Cities' own `/lostcities`
- [Editing and Tooling](editing.md), for the in-world part editor
- [Error Messages](../troubleshooting/errors.md)
