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

Run both gates before opening a pull request. CI runs the same two and blocks the
deploy on them:

```bash
mkdocs build --strict
```

```bash
python docs/examples/validate.py docs/examples/first-city
```

`--strict` turns a broken link or anchor into a failure. The validator checks three
separate things:

- the example datapack still satisfies every rule the wiki documents, and any page
  that inlines a whole example file still matches it byte for byte
- every key in the reference tables exists in `docs/examples/mod-keys.json`, which
  holds the keys the mod's own codecs declare, and every Required column agrees
  with the codec
- every key the version pages attribute to a reference page actually appears there

If you add a key to a reference table, it has to exist in the mod. That is the
point.

## Writing

Read [STYLE.md](STYLE.md) first. The wiki uses one approved term per concept and a
deliberately plain register, so a correct change written in a different voice still
needs rewriting before it can be merged. Sending the fact and letting a maintainer
word it is completely fine.

Two rules that catch people:

- **No em dashes.** Use a full stop, a colon, or brackets.
- **Say what a value does, not what a key is called.** A table cell that only names
  the topic is treated as a defect. `avoidWater` is not "replace water with air", it
  is "if `true`, any liquid a part places becomes air instead, and water already in
  the world is not affected".

## Testing a claim in a world

Two datapacks in this repo exist to check the wiki against a running game, and both
are documented on [Claim Tests](docs/examples/claim-tests.md):

| Pack | For |
|---|---|
| `docs/examples/wiki-test/` | Positive claims. Do this, and that happens. |
| `docs/examples/wiki-fail/` | Failure modes. Two of its profiles are meant to fail. |

If you want to test something the wiki asserts and nobody has run, adding a probe to
one of these is the best possible contribution. Every test that came back wrong so
far has found either a documentation error or a bug in the mod.

## Scope

This wiki documents the **datapack asset system**, which starts at mod version
5.3.29. Versions before that load their content from files inside the jar and are
out of scope. See [Versions](docs/versions/index.md).

## Licence

[CC0 1.0](LICENSE). Contributions are accepted on the same terms: no rights
reserved, no attribution required.
