# Licences in a Pack

!!! note "This page documents the companion mod, not Lost Cities"
    Lost Cities reads no licence file and has no opinion about one. Everything here is a convention [The Lost Cities - DevTool](https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/releases/latest) follows, described as of **3.0.0**. Nothing here is a claim about Lost Cities' behaviour, so it carries no verification chips, for the same reason [The DevTool Commands](lcdev.md) carries none.

!!! tip "TL;DR"
    Terms go in `data/<namespace>/lostcities/license.txt`, spelled exactly that way. An import reads it and reports what it found. An export carries what it found into the pack it compiles, one heading per namespace. A namespace that states nothing is reported as **nothing found**, which is not a finding of all rights reserved.

## Where the file goes

| | Path |
|---|---|
| **Primary** | `data/<namespace>/lostcities/license.txt` |
| Fallback | The pack root, beside `pack.mcmeta` |

The primary path is not the root, and one case decides it. A pack living in
`kubejs/data/<namespace>/lostcities/` has no root of its own, and neither does one
shipped inside a mod jar: the root there belongs to KubeJS or to the mod. Under `data/`
is the only place that travels with the assets in every shape a pack is distributed in.

!!! danger "Under `data/`, no other spelling works"
    Anything under `data/` is a resource location, so every path segment is validated
    against `[-._a-z0-9]+`. `LICENSE.txt`, `License.txt` and `licence.txt` are therefore
    invalid paths, and the loader reports `Invalid path in datapack ... ignoring` rather
    than anything mentioning a licence.

    A **zip** pack is not checked that way, so the identical file is readable there and
    not in the folder pack beside it. Nothing announces that difference. The lowercase
    American spelling is the one that works in both.

    The pack **root** is not a resource location, so the fallback finds `LICENSE.txt`,
    `COPYING` and `Licence.md` there without trouble.

## One statement per namespace

A namespace is one author's asset set, so one statement covers it. Per folder was
considered and answers a question nobody has: terms differ between authors, not between
a building and the palette it resolves through.

The file is free text and there is no schema. A `.txt` that somebody pastes MIT into is
the version that gets adopted.

## What an import shows

`/lcdev import` reports, for each namespace whose assets became plots:

| | |
|---|---|
| How much | The first **three non-blank lines**, with leading blanks and centring stripped first, or Apache and the GPL show two empty lines and a run of spaces |
| The rest | **Counted, not elided.** "19 more lines" says whether this is a permissive licence or the whole GPL. An ellipsis says neither |
| Line width | Each line is cut to the chat width, because a licence written as one paragraph satisfies a line count and defeats it |
| File size | The read stops at 64 KB. This is a file from an untrusted pack, read on every import, to show three lines of |

**The namespaces reported are those whose assets became plots**, not every namespace the
walk touched. A city style or a world style is configuration; the buildings and the parts
are the authored content, and they are what an export writes back out. That keeps the
import message and the export behaviour saying the same thing.

## What it says when it finds nothing

Not "all rights reserved" as a finding, and not the word illegal.

A missing file is weak evidence. Plenty of packs state their terms on a project page and
ship nothing, and a legal determination printed by a tool is one that can be wrong with
the author's name attached to it. So the message names **both** places it looked, then
says how to proceed: copyright is automatic, so treat the work as all rights reserved
unless the author says otherwise, and ask before redistributing.

Naming both paths is the part that earns its place. Where somebody does have a licence
and it is not being found, that line is the only thing that says why.

!!! note "Importing the mod's own pack reports nothing found"
    `/lcdev import lostcities:standard` is what everybody runs first, and it reports
    `lostcities` as stating nothing. That is literally true: the Lost Cities jar carries
    no licence file at its pack root or under `data/lostcities/lostcities/`.

    It is also pessimistic. The project is MIT, stated in its repository. The message
    names no namespace as special, including that one, because a datapack can override
    any namespace and content under `lostcities` may be somebody else's overrides under
    different terms.

## What an export carries

An export writes the statements it holds into `lostcities/license.txt` in the pack it
compiles, one heading per namespace. A pack compiled out of somebody else's content does
not ship with the credit stripped out.

`/lcdev export <name> plot` carries them too, and carries **only that plot's**, which is
exactly the moment attribution should follow: lifting one building out of somebody's
pack.

Three things about how that works are worth knowing.

| | |
|---|---|
| **The text is copied into the world at import** | It lands under `<world>/lostcitiesdevtool/licences/`. Reading it again at export would be less state and would lose the statement exactly when it matters, because a workshop outlives the packs it was filled from and a pack removed from the world would take its author's terms with it, silently |
| **A plot records where it came from** | In the [`source` setting](lcdev.md#source-the-namespace-a-plot-came-from). Without per-plot provenance a fragment lifted out of a three-pack workshop would ship all three authors' terms, and terms attached to work that is not in the file are a false statement rather than an over-cautious one |
| **Carrying is idempotent** | A pack compiled out of an imported pack that was itself compiled from an import would otherwise nest one heading inside another and label the first author's terms with the second author's namespace, accumulating every round trip. A notice carrying a notice passes its blocks through instead |

`/lcdev workshop clear confirm` forgets the statements, after the backup pack it writes
first has already carried them.

## What this does not do

**Prevention was never the goal.** Nothing here can stop somebody reading files they
already have, and a flag that refused an unlicensed import would bind only the people
already being careful while leaving pack authors falsely confident. Attribution is the
target.

**A notice can be forged.** Nothing distinguishes a notice this mod wrote from a file
whose first line happens to match. Refusing to unwrap one would bring back the nesting
that mislabels the first author's terms, which is the worse failure of the two.

**The number of blocks shown is not capped**, only what is inside each one. Reaching a
problem would take about a hundred namespaces inside one world style.

## See also

- [The DevTool Commands](lcdev.md), for `import`, `export` and the `source` setting
- [Namespaces](../getting-started/namespaces.md), for what a namespace is and why a pack has one
