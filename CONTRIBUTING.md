# Contributing

Corrections are welcome. A correction backed by something you observed is the most
useful thing you can send, and it does not need to be polished.

## The one rule

**Every behaviour claim on this wiki has to be traceable to the mod.** Either to the
code that implements it, or to a world where someone watched it happen.

That is the whole reason this site exists, so a plausible-sounding claim with no
source behind it will be removed even if it is probably right.

## Reporting something wrong

Open an issue with:

| | |
|---|---|
| **What you observed** | What the world actually did, or the exact log line |
| **Which mod version** | `7.4.12`, `7.5.1`, `8.4.1` and so on. Behaviour differs between them |
| **What the page says** | A link is enough |

You do not need to work out why. "This page says X, my world does Y" is a complete
and valuable report. Several of the corrections already on this site started exactly
that way.

Log lines are worth more than descriptions. Note that a single mistake in a datapack
can fail thousands of chunks, and the JVM stops recording stack traces for a
repeatedly thrown exception, so **the earliest errors in the file are the useful
ones**.

## Sending a change

Run the gates before opening a pull request. CI runs the same six and blocks the
deploy on them:

```bash
mkdocs build --strict
```

```bash
python docs/examples/validate.py
```

```bash
python docs/examples/check_claims.py
```

```bash
python docs/examples/key-coverage.py
```

```bash
python docs/examples/check_pages.py
```

```bash
python docs/examples/check_render.py
```

`--strict` turns a broken link or a missing nav target into a failure. It does not
check the fragment after a `#`, nor whether a table still rendered as a table, which
is what `check_render.py` reads the built HTML for. Both faults are silent: a label
that stops resolving is a claim that looks cited and is not, and a table with
anything inserted between its rows renders as one run-on paragraph.

`check_claims.py` requires every block that asserts something to carry a label, and
every label to point at an entry that exists. `key-coverage.py` requires every key
the mod declares to appear in an example pack, and `check_pages.py` requires every
key the mod declares to be named on the reference page that documents its type.

The validator checks three separate things:

- the example datapack still satisfies every rule the wiki documents, and any page
  that inlines a whole example file still matches it byte for byte
- every key in the reference tables exists in `docs/examples/mod-keys.json`, which
  holds the keys the mod's own codecs declare, and every Required column agrees
  with the codec
- every key the version pages attribute to a reference page actually appears there

If you add a key to a reference table, it has to exist in the mod. That is the
point.

## Wording is not your problem

There is no style guide to read. The wiki is written in a narrow, deliberately plain
register, and keeping it that way is the maintainer's job, not yours.

Send the fact in whatever words come out. A correction that is right and roughly
worded is worth more than one that never gets sent because matching a house voice
looked like work. It will be edited before it merges, and that is not a criticism of
how you wrote it.

The only thing that gets a change rejected on content is the rule above: a claim with
nothing behind it.

## Testing a claim in a world

Two datapacks in this repo exist to check the wiki against a running game, and both
are documented on [Claim Tests](docs/examples/claim-tests.md):

| Pack | For |
|---|---|
| `docs/examples/wiki-test/` | Positive claims. Do this, and that happens. |
| `docs/examples/wiki-fail/` | Failure modes. Two of its profiles are meant to fail. |
| `docs/examples/behaviour/` | Features that place themselves: cellars, highways, railways, city spheres. Each one paired with a control that turns it off. |
| `docs/examples/matcher-test/` | Whether a biome matcher gates the entry it is attached to. |
| `docs/examples/every-key/` | Every key the codecs declare, in a pack that still generates. |

A pack that measures something the generator places needs a **control**: a second
profile differing by one key, with the feature off. Without it a count cannot tell
"the feature worked" from "the pack happened to put one there". Two of the five
controls in `behaviour/` came back non-zero, and both were findings.

If you want to test something the wiki asserts and nobody has run, adding a probe to
one of these is the best possible contribution. Every test that came back wrong so
far has found either a documentation error or a bug in the mod.

You do not have to set a server up by hand. `testrig/` does it:

```bash
python testrig/rig.py doctor
```

It tells you which jars and which Java to fetch, installs the server, runs a pack
and prints what the world actually built. It works on every Lost Cities version from
2.0.22 to 10.0.1. See [testrig/README.md](testrig/README.md).

## Scope

This wiki's reference section documents the **datapack asset system**, which starts
at mod version 5.3.29. Versions before that load their content from files inside the
jar, and they have their own section rather than being out of scope: see
[The File-Asset Era](docs/file-era/index.md). Which pages apply to which release is
on [Versions](docs/versions/index.md).

## Licence

[CC0 1.0](LICENSE). Contributions are accepted on the same terms: no rights
reserved, no attribution required.
