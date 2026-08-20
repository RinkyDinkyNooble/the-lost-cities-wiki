# The test rig

Every "run in a world" claim on this wiki was produced here. This runs the same
tests on your machine, against whichever Lost Cities version you care about.

You need Python 3.9 or newer and nothing else installed. The rig downloads nothing:
it tells you which files to fetch and where to put them.

## Start here

```bash
python testrig/rig.py doctor
```

It prints, for every version, what is present and what is missing:

```
7.4.12   forge 1.20.1-47.4.10, Minecraft 1.20.1, Java 17
  [  ok   ] java 17            testrig/java/17
  [MISSING] loader installer   testrig/downloads/forge-1.20.1-47.4.10-installer.jar
            get it from https://files.minecraftforge.net/...
  [MISSING] server installed   testrig/servers/forge-1.20.1-47.4.10
  [MISSING] mod jar            testrig/downloads/lostcities-1.20-7.4.12.jar
            get it from https://www.curseforge.com/minecraft/mc-mods/the-lost-cities/files
```

Fetch what it names. Two folders take everything:

| Put it in | What goes there |
|---|---|
| `testrig/downloads/` | Lost Cities jars and loader installers, exactly as downloaded |
| `testrig/java/<major>/` | An unzipped JDK. `testrig/java/17/` for Java 17, and so on |

Filenames are matched without case, and a `.zip` is accepted where a `.jar` is
expected, because that is what some browsers save. Unzipping a JDK leaves one
nested folder; the rig looks inside it, so you do not have to flatten it.

Already have a JDK elsewhere? Point at it instead:

```bash
LCRIG_JAVA_17=/usr/lib/jvm/temurin-17/bin/java python testrig/rig.py doctor
```

Then install and run:

```bash
python testrig/rig.py install 7.4.12 --accept-eula
python testrig/rig.py run 7.4.12 wiki-test10
```

`--accept-eula` is you accepting <https://aka.ms/MinecraftEULA>. The rig will not
write that file for you without it.

```
7.4.12  wiki-test10.json

  pass  full-gold                 512 blocks   every reference spelled in full: the tower generates
  pass  barepalette-diamond       512 blocks   a bare refpalette is never resolved when every part…
  pass  barepart-lapis            0 blocks     a part name written bare resolves to lostcities:ns_lapis
  pass  barepalette-only-emerald  0 blocks     bare refpalette with a part that has no palette of its own

  4 pass
  failed chunks:
      41x  caught: Error getting resource lostcities:ns_lapis!
       2x  caught: Error getting resource lostcities:test!
```

A run takes about a minute. Most of it is the server booting.

## Comparing versions

```bash
python testrig/rig.py matrix wiki-test10
```

runs the same pack everywhere it applies and prints the comparison:

```
probe                  6.2.2       7.4.12      7.5.1       8.2.2       8.4.1
full-gold              768 blocks  512 blocks  512 blocks  768 blocks  512 blocks
barepalette-diamond    768 blocks  512 blocks  0 blocks    768 blocks  0 blocks
barepart-lapis         0 blocks    0 blocks    0 blocks    0 blocks    0 blocks
```

`--md` emits that as a markdown table. `--only 7.4.12 8.2.2` limits which versions
run.

## The four results

| Result | Means |
|---|---|
| `pass` | Matched what this version is expected to produce |
| `fail` | Did not, **and nobody has explained why yet** |
| `n/a` | This version cannot do what the probe needs. Not a failure |
| `error` | The run did not finish: the server died, or a chunk never generated |

`n/a` matters. Lost Cities 6.0.3 loads a predefined city and then never places it,
so a pinning test there has not failed, it was never applicable. The rig knows which
versions can do what and skips those runs entirely rather than booting a server to
learn nothing.

`fail` is the interesting one. Expectations are written against **7.4.12**, the
version this wiki documents. When another version differs, that is a finding. Once
somebody works out why, the reason is recorded in the probe file and the cell turns
green carrying its explanation:

```json
"expect": {
  "8.2.2": { "min": 768, "max": 768,
             "why": "overrideFloors is not declared here, so the building is a floor taller" }
}
```

So a red cell always means *an unexplained difference*, never just *a difference*.

## The packs

The packs live in `docs/examples/` and are part of the wiki, not of the rig.

| Pack | Tests |
|---|---|
| `wiki-test10` | Namespace resolution, and what an unresolved reference does |
| `wiki-test11` | Building fronts and stuff objects |
| `wiki-test12` | Scattered structures |
| `wiki-test13` | A predefined sphere, and what its glass character resolves to |
| `every-key` | Every key the codecs declare, in a pack that still generates |
| `matcher-test` | Whether a biome matcher gates the world style entry it is on |
| `behaviour` | Cellars, `preferslonely`, highways, railways and city spheres |
| `file-era-test` | The pre-datapack asset system, on the 1.12.2 rig |

Every claim they check is written up on
[Claim Tests](../docs/examples/claim-tests.md).

## Adding a test

Write the pack under `docs/examples/`, then a probe file in `testrig/probes/`
naming it:

```json
{
  "pack": "wiki-test10",
  "profile": "wtten",
  "grid":  { "x0": 6, "z0": 6, "x1": 16, "z1": 16 },
  "anchor": [130, 72, 130],
  "probes": [
    { "id": "full-gold", "kind": "count",
      "claim": "every reference spelled in full: the tower generates",
      "requires": ["predefined_city"],
      "from": [128, 40, 128], "to": [143, 167, 143],
      "block": "minecraft:gold_block", "min": 512, "max": 512 }
  ]
}
```

`grid` is in **chunks**. `from` and `to` are in **blocks**.

For anything that places itself rather than sitting where the pack pinned it, use
`boxes` instead of `from`/`to`. It takes a list of `[from, to]` pairs and adds the
counts together:

```json
{ "id": "highway-built", "kind": "count",
  "claim": "the highway network places the parts the world style names",
  "boxes": [[[128, 40, 128], [143, 167, 143]],
            [[144, 40, 128], [159, 167, 143]]],
  "block": "minecraft:iron_block", "min": 1 }
```

One box per chunk is the usual shape, because of the size limit below.

| Probe kind | Answers |
|---|---|
| `count` | How many of one block are in a box |
| `block` | Is this exact block at this exact position. Use it for anything counting cannot see, such as rotation |
| `data` | Dump a block entity's NBT, optionally asserting `contains` |

`requires` names capabilities from `versions.json`: `predefined_city`,
`predefined_sphere`, `stuff`, `scattered`, `override_floors`, `front_chance`. A
version without them reports `n/a`.

A `count` box cannot exceed 32768 blocks. That is exactly one chunk footprint 128
levels tall, because counting is done with a filtered `/clone` and that is where
`/clone` stops. A box also cannot be wider or deeper than the rig's scratch area,
which is 32 by 32: `/clone` writes the source box's full extent starting at the
destination corner, so a box wider than the scratch fails with "That position is
not loaded" even when it is well under the size limit.

`/forceload add` refuses more than 256 chunks in one call, so a `grid` larger than
16 by 16 loads nothing and every probe then reads an empty world.

## Pair a test with its control

Anything that places itself where the generator decides needs two runs, not one.
A count on its own cannot tell "the feature worked" from "the pack happened to put
one there", and it cannot tell "the feature is off" from "the pack never built
anything". So each feature gets a profile that turns it on and a second that
differs by exactly one key and turns it off, both counting the same block over the
same boxes.

Every result in the `behaviour` pack is a pair, and two of the five off runs came
back non-zero. Neither was expected, and neither would have been visible without
the pairing.

## Options

| Flag | For |
|---|---|
| `--profile <name>` | Override the profile the probe file names |
| `--profile-patch '{"cities":{"cityChance":1.0}}'` | Merge JSON into the profile, to run one pack under several variants |
| `--also-pack <name>` | Install another pack beside the first, so two packs can claim one asset |
| `--keep-config` | Skip the config wipe. Needed to reproduce upgrade bugs |
| `--port <n>` | If something already holds 25575 |
| `--force` | Run even where no probe applies |

## When it does not work

Every one of these cost a wasted test round at least once.

| Symptom | Cause |
|---|---|
| Every probe reads an empty world | `/forceload` takes **block** coordinates, not chunk. The rig converts for you; hand-written commands often do not |
| A count returns 0 with "not loaded" | `/clone` needs its destination loaded. The rig force loads a scratch chunk for this |
| A count is suspiciously round, or zero on a big box | `/clone` caps at 32768 blocks and returns nothing rather than a partial answer |
| The city generates as ordinary terrain | The Lost Cities config section is `[profiles]`. Under any other name Forge rewrites the file to defaults, with no error, and points the dimension at `biosphere` |
| 8.4.1 will not boot after running 8.2.2 | 8.2.2 writes `selectedProfile = "<CHECK>"`, which 8.4.1 no longer understands. The rig wipes the config between runs, so this only bites if you use `--keep-config` |
| Nothing generates on 1.12.2 | The mod registers a world **type**. `level-type=lostcities` is required, and a profile alone does nothing |
| `UnsupportedClassVersionError` | Wrong Java. `doctor` checks a jar's class file version against the Java the version needs and warns before you get here |

Runs are reproducible because `server.properties` pins the seed to
`lostcitieswiki` and turns structures off. Change either and your counts will not
match the ones on the wiki.

## What the rig does and does not change

It copies your pack before running it and renames exactly one thing: the predefined
city folder, whose spelling differs between versions (`predefinedcities`,
`predefinedcites`, `predefinedcitites`). A folder the version did not compile in is
never scanned, so the pack would silently look empty.

It changes **nothing else**. In particular it never removes a key a version does not
declare, because that is exactly what several of these tests measure. A rig that
tidied packs up to suit each version would agree with itself and prove nothing.

## Layout

```
testrig/
  rig.py            the only entry point
  versions.json     everything that differs between versions
  rcon.py           minimal RCON client, no dependencies
  adapters/
    modern.py       Minecraft 1.18 and later
    legacy112.py    Minecraft 1.12.2, which has none of the commands the others use
  probes/           one file per pack
  downloads/        you put jars here
  java/             you put JDKs here
  servers/          installs land here
```

`downloads/`, `java/` and `servers/` are gitignored. Nothing in them is ours to
redistribute: the mod is McJty's, the loaders are Forge's and NeoForge's, and the
runtimes are Adoptium's.
