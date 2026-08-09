---
status: in-progress
---

# Editing & Tooling

!!! info "This page is still being written"
    A full write-up of the recommended authoring workflow is planned. What's here is accurate, just not complete yet.

Two ways to actually build content: edit in-game, or build in Minecraft normally and convert.

## In-game edit mode

Set `editMode: true` in your [profile](../reference/profile.md)'s `lostcity` section. This puts the world in a special editing state where you build directly and the mod has commands to save what you built back out to JSON. It has to be set **before the world is created**, it can't be turned on for an existing world and work retroactively.

!!! warning "Deliberately not documented here yet"
    The editor's behavior has been traced in the mod's code, and the workflow has some sharp edges worth knowing about before relying on it: the active editing session lives only in server memory and doesn't survive a restart, and the two commands for resuming an edit behave very differently (one silently discards your unsaved in-world changes before reopening). There's also a case where two palette characters that map to the same block get collapsed into one on export, losing a distinction you authored deliberately.

    None of that makes it useless, but it does mean a half-explained guide would cost people work. A proper write-up with the specific pitfalls is planned rather than a quick pointer. Until then, export early and often, and keep your JSON as the source of truth.

## Building normally, then converting

The more common workflow: build a structure normally in creative mode (with WorldEdit or similar for copy/paste), export it as a schematic, then convert that schematic into Lost Cities part JSON with an external tool.

!!! info "Recommended tool: coming soon"
    A write-up of the recommended conversion workflow is planned here once the tool is ready to share.

## See also

[Profile Reference](../reference/profile.md) for `editMode` and related flags.
