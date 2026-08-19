---
claims: verified
---

---
status: in-progress
---

# Editing & Tooling

!!! info "The external converter section is still coming"
    The in-game editor below is fully traced and documented. A write-up of the schematic-to-JSON converter workflow lands here once that tool is ready to share.

Three ways to author parts, in rough order of how much hand-editing each involves: <!-- noclaim -->

| Approach | Good for | Cost | <!-- noclaim -->
|---|---|---|
| **Write JSON by hand** | small parts, quick edits, anything scripted | tedious past a few layers |
| **In-game edit mode** | shaping a part in place and seeing it immediately | needs a dedicated world, session is fragile |
| **Build normally, then convert** | large or detailed structures, reusing existing builds | needs an external tool |

Whichever you use, **keep the JSON as your source of truth.** Every in-game path exports to JSON eventually, and the export is lossy in one specific way documented below. <!-- noclaim -->

## In-game edit mode

Set `editMode: true` in your [profile](../reference/profile.md)'s `lostcity` section. [code review](../examples/claim-tests.md#ref-1){.v .v-c}

```json title="config/lostcities/profiles/myedit.json"
{
  "lostcity": {
    "worldStyle": "mycity:mycity",
    "editMode": true
  }
}
```

!!! warning "It has to be set before the world is created"
    Turning `editMode` on for an existing world does not work retroactively. Edit mode makes the generator record which part it placed at which position as it generates; a world built without it has no such record, and every editor command below will refuse with *"Could not find a part to edit in this chunk!"*

    Make a separate throwaway world for editing. That is the intended workflow, not a limitation to route around. <!-- noclaim -->

### The commands

All require op (permission level 1) and all refuse outright unless the world was created with `editMode: true`. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

| Command | What it does | [code review](../examples/claim-tests.md#ref-2){.v .v-c}
|---|---|
| `/lostcities createpart <name> <pos>` | Creates a new empty part at a position and starts editing it |
| `/lostcities editpart` | Edits the part you are standing inside. **Repaints it from the saved JSON first**, see below |
| `/lostcities resumeedit` | Re-attaches to the part you are standing inside **without** repainting |
| `/lostcities listparts` | Lists the parts recorded in your current chunk |
| `/lostcities locatepart <name>` | Finds where a given part generated |
| `/lostcities exportpart <file>` | Writes the current editing session out to JSON |

Both `editpart` and `resumeedit` find the part by looking at your Y position: they pick whichever recorded part's vertical range contains you. Stand at the wrong height and you will edit the floor above or below. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

### Three traps in the editor

!!! danger "`editpart` discards your unsaved in-world changes. `resumeedit` does not."
    The two commands look interchangeable and are not. `editpart` **overwrites the entire part volume with the contents of the saved JSON** before it hands control back, so anything you built and had not exported is gone with no confirmation prompt.

    `resumeedit` re-attaches to the same part and leaves the world exactly as it is. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    **Use `resumeedit` unless you specifically want to throw your changes away and start from the saved file.** <!-- noclaim -->

!!! danger "The editing session lives in server memory only"
    It is a map keyed by player UUID, held in RAM. It is not written to disk and does not survive a server restart, a world reload, or a crash. Restarting means re-running `resumeedit` to re-attach, and if you had been editing without exporting, the world still has your blocks but the mod no longer knows they belong to a part.

    **Export early and often.** `exportpart` is the only thing that makes work durable. <!-- noclaim -->

!!! danger "Export collapses two characters that map to the same block"
    `exportpart` works backwards from block states to characters using a reverse lookup, one block state to one character. If your palette deliberately maps two different characters to the same block, for example one plain and one carrying a `loot` table, a `mob`, or an NBT `tag`, the export cannot tell them apart and picks one.

    You lose the distinction silently, and the exported part looks correct. If your part depends on such a pair, re-apply it to the exported JSON by hand, or do not round-trip that part through the editor at all. [unverified](../examples/claim-tests.md#ref-3){.v .v-u}

### What export actually produces

`exportpart <file>` writes UTF-8 JSON to the given filename in the server's working directory, containing: [code review](../examples/claim-tests.md#ref-2){.v .v-c}

- `exportedpart`, the part itself, ready to drop into `parts/`
- `missingpalette`, only when it found block states not in the palette, listing them as ready-made palette entries with auto-assigned characters [code review](../examples/claim-tests.md#ref-2){.v .v-c}

That second key is genuinely useful: it means you can build with any blocks you like and the export tells you exactly what palette entries you still need. Characters are assigned from ASCII first, then Greek, then Cyrillic, skipping anything already taken. Same pool documented at [Which characters to actually pick](../reference/palette.md#which-characters-to-pick). [code review](../examples/claim-tests.md#ref-2){.v .v-c}

The output is not a drop-in file: you still need to move `exportedpart` into `data/<namespace>/lostcities/parts/<name>.json` and merge `missingpalette` into a real palette. <!-- noclaim -->

## Building normally, then converting

!!! warning "The mod cannot read a schematic, a structure block file, or an `.nbt`"
    There is no import command and no import path. The mod reads part JSON and nothing else. If you have a build you want to turn into a part, you have exactly two routes:

    1. **`/lostcities exportpart`**, which reads the blocks already in the world and writes part JSON for you. This is the only conversion the mod itself performs, and it needs a world created with `editMode: true`. It is covered above.
    2. **An external converter**, which reads your schematic and writes the JSON. Nothing about that path involves the mod. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

    A file named `.schem`, `.nbt` or `.litematic` will never be loaded by Lost Cities, whatever folder you put it in. [code review](../examples/claim-tests.md#ref-2){.v .v-c}

The workflow most large builds end up using: build the structure in creative with WorldEdit or similar, export a schematic, and convert that schematic into part JSON with an external tool. <!-- noclaim -->

This sidesteps every editor limitation above, since nothing round-trips through the mod. It also means you can use any editor and any workflow you already know. <!-- noclaim -->

Whatever tool you use has to get these right, and none of them are checked by the mod: [code review](../examples/claim-tests.md#ref-2){.v .v-c}

| Rule | Consequence of getting it wrong | [code review](../examples/claim-tests.md#ref-1){.v .v-c}
|---|---|
| Exactly 16×16, and 6 slices per floor level | Silent corruption, no error |
| Every row exactly `xsize` **UTF-16 code units** | Diagonal smear across the layer |
| One code unit per palette character, no emoji | Two different failures at once |
| A character for every distinct block state used | Crash during generation |

[`validate.py`](../examples/index.md#validatepy) checks all of these against a finished datapack, so it works as a post-conversion check regardless of which tool produced the files. <!-- noclaim -->

## See also

- [Building Part Reference](../reference/part.md) for the format you are producing
- [Palette Reference](../reference/palette.md) for characters and merge order
- [Testing & Debugging Commands](commands.md), including why `/reload` will not show your changes
- [Known Issues & Workarounds](../troubleshooting/known-issues.md) <!-- noclaim -->
