# 1.0.1

First release. For Minecraft 1.20.1, Forge, and The Lost Cities 7.4.12.

## Where to install it

- **Dedicated server.** Everything that matters runs here: reading `.json5` files,
  checking your files as they load, the improved error messages, and all `/lcdev`
  commands.
- **Client.** Only the Lost Cities menu fixes are client-side. Installing it on the
  client is optional, and a client without it can still join a server that has it.
- **Singleplayer.** One install covers both.

## Better error messages

- When a building is broken, the error now names **that building and its chunk**,
  instead of naming whichever nearby chunk happened to ask about it. On a test pack
  with three broken buildings, that turned 78 similar-looking failures into three
  named ones.
- Each caught error gets a second line with the profile, world style, city style,
  building, and floor and cellar counts.
- A missing palette character is reported with its character code and official name,
  so you can identify symbols a console cannot print.

## Your files are checked before the world loads

Nine checks run as your files load, and anything that will fail is listed with a file
name and a line number. They cover floor ranges that leave a level with nothing to
build, conditions that can never match, invalid block names, weighted lists that do
not add up, layers that are the wrong size, and more.

Nothing is blocked from loading. You are told, and the game carries on.

## Comments in your files

- Comments and trailing commas now work in Lost Cities files and in profiles.
- Files can be named `.json5`, which stops your editor underlining comments as errors.
- If a `.json` and a `.json5` of the same name both exist, the `.json5` is used and
  you are told which file was ignored.

## New commands

- `/lcdev report` shows what Lost Cities selected for the chunk you are standing in,
  including which part was chosen on each level.
- `/lcdev char` shows what a palette character turns into, and `/lcdev block` shows
  which characters produce a given block.
- `/lcdev in <file> char` or `block` asks a specific file instead of your current
  chunk, so it works anywhere, with tab completion.
- Characters can be entered as `U+0047` when you cannot type them into chat.

## Sphere worlds no longer crash on a broken file

Normal Lost Cities worlds log a failed chunk and carry on. Sphere worlds had no such
protection, so the same mistake could take the server down. On `spheres`,
`cavernspheres` and `space`, those errors are now logged instead.

Tested with the same pack and seed: 21 crashes and a dropped connection before, none
after, with all 338 errors logged and the server still running. The world generates
identically either way.

## Optional fixes, off by default

These change world generation, so they are opt-in. Enable them individually in
`config/lostcities_devtool-common.toml`.

- **`belowpart`** now checks the part below, as the name suggests. It currently
  behaves identically to `inpart`, so a building using it fails every chunk it stands
  in.
- **`streetblocks.parts.full`** can now actually be selected. It was never chosen
  before, so a `full` street shape placed nothing.

## Menu fixes, on by default

These cannot change world generation.

- Right-clicking the profile button steps backwards through the list, so overshooting
  the profile you wanted no longer means cycling all the way around.
- The Cities button stays where it belongs when you resize the window.
- Pressing Customize after playing a world no longer crashes the game.

## Known issue in Lost Cities itself

The palette `lostcities:bricks_desert_redsand` contains an old-style block name,
`minecraft:red_sandstone@2`, which is not valid in modern Minecraft. The whole palette
fails to load as a result, not just that one entry.

Nothing in Lost Cities 7.4.12 uses that palette, so this only affects you if you point
at it yourself. DevTool's file check reports it with the file name and line number.
