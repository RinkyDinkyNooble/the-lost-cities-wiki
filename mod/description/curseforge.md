<h1 align="center">The Lost Cities - DevTool</h1>

<p align="center">
  <b>A companion mod for <a href="https://www.curseforge.com/minecraft/mc-mods/the-lost-cities">The Lost Cities</a>, for people writing datapacks for it.</b>
</p>

<p align="center">
  <i>Adds no blocks, no items and no generation of its own.<br>
  Removing it leaves every world it touched loadable by vanilla Lost Cities.</i>
</p>

---

Lost Cities assembles a city from a chain of assets: a profile picks a world style,
which picks a city style, which picks buildings, which pick parts, which read
palettes. When something in that chain is wrong, the message you get names the chunk
that was being generated rather than the file that is broken, and you get one per
affected chunk.

This mod reports the file instead, checks what it can before the world loads, and lets
asset files carry comments.

<h2>Requirements</h2>

<table>
  <tr><td><b>Minecraft</b></td><td>1.20.1</td></tr>
  <tr><td><b>Forge</b></td><td>47+</td></tr>
  <tr><td><b>The Lost Cities</b></td><td>7.4.12, a <b>hard dependency</b></td></tr>
</table>

<p>The version range is deliberately narrow. This mod patches Lost Cities with mixins,
and a mixin is bound to the shape of the code it patches, so each target version needs
its own verification pass rather than a range bump.</p>

<h2>Comments in asset files</h2>

```json5
// the marker tower at the city centre
{
  "filler": "#",
  "parts": [
    { "part": "mypack:origin" },  // one part, no condition, covers every level
  ],
}
```

Comments and trailing commas, and files may be named <code>.json5</code> so your
editor stops underlining them. Both work for datapack assets under
<code>data/&lt;namespace&gt;/lostcities/</code> and for profiles in
<code>config/lostcities/profiles/</code>.

Where both <code>foo.json</code> and <code>foo.json5</code> exist the
<code>.json5</code> wins, and the shadowed file is named in the log and once in chat,
because two files that look interchangeable in an editor and are not is a bad
afternoon.

This is a <b>subset</b> of JSON5, not all of it. Unquoted keys and single quotes are
not accepted: they change what a valid file looks like without solving a problem an
author actually has.

<h2>Works wherever datapacks come from</h2>

<p>The hook sits on the resource manager rather than on a folder path, so <b>any</b>
datapack source is covered, not just <code>saves/&lt;world&gt;/datapacks</code>. That
includes <code>kubejs/data</code>, confirmed working with KubeJS: put your Lost Cities
assets there, comments and <code>.json5</code> and all, and they load.</p>

<p>The usual reason a pack in <code>kubejs/data</code> does not load is the
<b>namespace</b>. The folder directly under <code>data/</code> is the namespace, and
every reference has to use it:
<code>data/mypack/lostcities/buildings/tower.json5</code> is <code>mypack:tower</code>,
and a city style naming <code>tower</code> without the namespace will not find it.</p>

<p><span style="color:#c0392b">Without this mod installed, a pack written with
<code>.json5</code> does not load at all. The profile is not read and the game crashes
on world creation, which is the same result as the asset simply not existing.</span></p>

<h2>Faults reported against the file, not the chunk</h2>

<p>A fault raised while a chunk's information is built spreads to every neighbour that
queries it, and those queries chain. So one broken building produces a wall of
failures with coordinates that all point somewhere other than the problem.</p>

<p>The message is enriched where the building is still known:</p>

```
Misconfiguration! Floor were generated for a building where no part condition matches!
  [building mypack:tower at chunk 10,8, levels 0 to 6 inclusive.
   Every chunk that queries this one fails the same way]
```

<p>On a test pack with three broken buildings, that turned <b>78 undifferentiated
failures</b> across a 13 by 10 chunk area into <b>three named faults</b>.</p>

<p>For an unresolved palette character the report gives the code point and Unicode
name, which a console cannot render, and the four places to look for it.</p>

<h2>Checked before the world loads</h2>

<p>Every asset file is read when datapacks load, and what will fail is reported once,
with a file name and a line number:</p>

```
Lost Cities asset check: 2 errors, 1 warning
  ERROR  mypack:lostcities/buildings/tower.json:10  levels [3] match no part
         Levels run -0 to 3 INCLUSIVE, so 'maxfloors': 3 is a 4-storey building
  ERROR  mypack:lostcities/palettes/test.json:72  'loot': "minecraft:chests/simple_dungeon"
         looks like an ID, but 'loot' names a Condition
  WARN   mypack:lostcities/buildings/tower.json:13  range "0,2,9" has more than two numbers
         The mod reads the first two and discards the rest, silently
```

<p>Checked: level coverage, <code>inpart</code> and <code>belowpart</code> where
neither can ever match, a <code>range</code> that does not parse or carries a third
number, <code>loot</code> and <code>mob</code> holding an ID rather than a Condition
name, a <code>char</code> that is not one code unit, a block id that is not a legal
resource location, a weighted list that misses or overruns its 128 slots, and a
<code>slices</code> layer that is not <code>xsize</code> by <code>zsize</code>
characters.</p>

<p><b>Nothing is prevented from loading.</b> The check reports and steps aside.</p>

<h2>Commands</h2>

```
/lcdev report                                  what the generator decided for this chunk
/lcdev char G                                  a character, here and in every asset
/lcdev char U+0047                             the same, by code point
/lcdev block minecraft:gold_block              which characters produce this block
/lcdev in mypack:mystyle char G                one named asset, from anywhere
/lcdev in mypack:mystyle block minecraft:gold_block
```

<p><code>/lcdev report</code> names the profile, world style, city style, building,
and <b>the part chosen for each level</b>, which is the direct answer to any question
about which condition won. None of the mod's own commands report that, and unlike
<code>/lostcities debug</code> this writes to whoever asked rather than to the server
console.</p>

<p>The <code>in &lt;asset&gt;</code> forms tab complete over every palette, part and
building that carries a palette, and work from anywhere: outside a city, or in a
dimension with no Lost Cities profile at all. That is the state you are in while
actually editing a file.</p>

<h2>Optional repairs</h2>

<p><span style="color:#b9770e"><b>Off by default, one toggle each.</b></span> Each
changes what generates, so a world made with one enabled will not come out the same
without it. In <code>config/lostcities_devtool-common.toml</code>.</p>

<table>
  <tr><th>Repair</th><th>Measured, same seed, only the toggle changed</th></tr>
  <tr>
    <td><code>belowpart</code> tests the part below, as its name says</td>
    <td><b>off:</b> gold on both levels. <b>on:</b> gold on level 0, diamond on level 1</td>
  </tr>
  <tr>
    <td><code>streetblocks.parts.full</code> becomes reachable</td>
    <td><b>off:</b> 0 blocks placed, every chunk reports <code>NORMAL</code>. <b>on:</b> 256 blocks, chunks report <code>FULL</code></td>
  </tr>
</table>

<p>Both are off-by-one or wrong-field mistakes in compiled code that no datapack can
reach. The wiki traces each one to the line.</p>

<p><span style="color:#1e8449"><b>Two client fixes default to on</b></span>, because
they change nothing about generation: the Cities button keeps its position when the
window is resized, and pressing Customize after having played a world no longer
crashes the game. Right-click on the profile button also cycles backwards, which it
previously could not do at all.</p>

<h2>Sphere worlds survive a broken datapack</h2>

<p><code>LostCityFeature</code> wraps generation in a catch, which is what makes a
datapack mistake survivable: the chunk fails, a line is logged, generation continues.
<code>LostCitySphereFeature</code> has no such catch anywhere in the class, so on
<code>landscapeType</code> <code>spheres</code>, <code>cavernspheres</code> or
<code>space</code> the same fault escapes instead.</p>

<p>Measured on the same pack, profile and seed, with only that toggle changed:</p>

<table>
  <tr><th>Toggle</th><th>Faults escaping</th><th>Faults logged</th><th>Server</th></tr>
  <tr><td>off</td><td>21</td><td>0</td><td>connection dropped mid-run</td></tr>
  <tr><td><b>on</b></td><td><b>0</b></td><td>338</td><td>ran to completion</td></tr>
</table>

<p>Nothing about what generates changes. A chunk that would have failed still fails
and is left in the same state. Only the survivability changes.</p>

<h2>Try it without writing anything</h2>

<p>Three datapacks and two profiles, generated from one definition so they cannot
drift apart, are in the wiki repository under
<a href="https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/docs/examples/json5-test">docs/examples/json5-test</a>.
All three build the same three towers, and one of them needs no mod at all so you can
see the control first.</p>

<h2>More detail</h2>

<p>Everything above is traced and tested on
<a href="https://rinkydinkynooble.github.io/the-lost-cities-wiki/">the Lost Cities Wiki</a>,
which is what this mod implements the findings of. The
<a href="https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/blob/main/mod/README.md">mod's own README</a>
covers every setting and the evidence behind it.</p>

<h2>Credits and licence</h2>

<p>The Lost Cities is by <b>McJty</b>, and the Lost Cities Discord answered questions
no documentation covers. This is an unofficial companion mod, <b>not affiliated with
or endorsed by either</b>.</p>

<p>Released under <a href="https://opensource.org/license/0bsd">0BSD</a>. No rights
reserved, no attribution required. Take any of it.</p>
