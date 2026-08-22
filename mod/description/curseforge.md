<h1 align="center">The Lost Cities - DevTool</h1>

<p align="center">
  <b>A companion mod for <a href="https://www.curseforge.com/minecraft/mc-mods/the-lost-cities">The Lost Cities</a>.</b><br>
  Build a pack by building it in Minecraft, open a pack you already have by walking
  around inside it, and find the mistake in the one you are writing.
</p>

<p align="center">
  <span style="color:#2f8a4e"><b>It adds no blocks, items, mobs or structures to your world,
  and nothing it does changes world generation unless you switch on one of the two
  optional fixes.</b></span>
</p>

<hr>

<table>
<tr><td><b>Minecraft</b></td><td>1.20.1</td></tr>
<tr><td><b>Forge</b></td><td>47+</td></tr>
<tr><td><b>The Lost Cities</b></td><td><span style="color:#d64545"><b>7.4.12, required</b></span></td></tr>
<tr><td><b>Java</b></td><td>17 or newer</td></tr>
<tr><td><b>Licence</b></td><td><a href="https://opensource.org/license/0bsd">0BSD</a></td></tr>
</table>

<h2><span style="color:#ad6c19">What it does</span></h2>

A custom city is a lot of small files, and when one of them is wrong, Lost Cities
usually tells you in a way that does not name the file.

<ul>
  <li>Builds a whole pack out of what you build in game, and opens a pack you already have</li>
  <li>Names the building that caused a generation error, and where it is</li>
  <li>Checks your files as they load and reports the file and line number</li>
  <li>Lets you write comments and trailing commas in your JSON</li>
  <li>Shows which building, part and floor the generator picked for a chunk</li>
  <li>Looks up palette characters and blocks, in both directions</li>
  <li>Keeps a broken file from crashing sphere worlds</li>
</ul>

<h2><span style="color:#ad6c19">Build a pack by building it</span></h2>

The workshop is a dimension laid out as a catalogue, with a plot for every shape a
pack can hold: 138 rows covering streets, highways, railways, monorails, parks,
fountains, bridges, stairs, fronts, rail dungeons, buildings, and every
multibuilding footprint up to the 10x10 that is as wide as one can be. Each plot
sits on chunk boundaries and is floor marked in its own colour. Rows start at eight
plots and grow as far as you want.

<pre>
/lcdev workshop build     lay the catalogue out
/lcdev workshop go        travel there
/lcdev workshop here      what the plot you are standing on compiles into
/lcdev workshop rows      every row, each one a place to click
</pre>

Build in the plots with whatever you normally build with. Then compile the lot:

<pre>
/lcdev export mypack
</pre>

That writes a complete datapack and the profile that goes with it, ready to drop
into a world. A pack made this way generated a city with
<span style="color:#ad6c19"><b>10,672 gold blocks</b></span> in it.

<h2><span style="color:#ad6c19">Open a pack you already have</span></h2>

Point it at a pack that is loaded and it pastes that pack into the workshop, so you
can walk around it and edit it:

<pre>
/lcdev import lostcities:standard
</pre>

The Lost Cities default pack comes in as
<span style="color:#ad6c19"><b>42 assets on 42 plots, 714,240 blocks</b></span>, streets
included, even though nothing in that pack names a street part. Change one building
and compile the whole thing back out.

A building that names several parts for the same level comes in showing all of them
rather than the first one repeated. A palette entry's <code>tag</code> is carried
both ways, so command blocks keep their commands, chests keep their loot tables and
spawners keep their mobs. Command blocks arrive unable to fire, because forty spawn
commands going off while you are looking at a building is not useful.
<code>/lcdev import mypack:main run</code> pastes them live instead, so they fire and
resolve into whatever they place.

Importing a second city leaves the first one's plots alone, since an import only
fills what its own pack needs. It says how many it left behind, and
<code>/lcdev workshop clear</code> empties the workshop when you want to start again,
writing a full backup pack before it does.

Every plot has a settings file beside your world, with the meaning of each key in a
comment above it, so a file you open six months later still says what it does.
Floors, cellars, roof variations, spawn weights, distance windows, city style
membership, and an escape hatch for anything the settings do not name yet.

<h2><span style="color:#ad6c19">Find out what actually went wrong</span></h2>

One broken building makes Lost Cities produce errors from every chunk that asked
about it, and none of them say which building it was. DevTool says it directly:

<pre>
<span style="color:#d64545">Misconfiguration!</span> Floor were generated for a building where no part condition matches!
  <span style="color:#7d7d7d">[building mypack:tower at chunk 10,8, levels 0 to 6 inclusive.
   Every chunk that queries this one fails the same way]</span>
</pre>

On a test pack with three broken buildings, 78 similar looking failures became
<span style="color:#ad6c19"><b>three named ones</b></span>. Missing palette characters
are reported the same way, with the character's code and name when it cannot be
printed.

<h2><span style="color:#ad6c19">Your files are checked as they load</span></h2>

<pre>
Lost Cities asset check: <span style="color:#d64545">2 errors</span>, <span style="color:#ad6c19">1 warning</span>
  <span style="color:#d64545">ERROR</span>  mypack:lostcities/buildings/tower.json:10  levels [3] match no part
         <span style="color:#7d7d7d">Levels run -0 to 3 INCLUSIVE, so 'maxfloors': 3 is a 4-storey building</span>
  <span style="color:#d64545">ERROR</span>  mypack:lostcities/palettes/test.json:72  'loot': "minecraft:chests/simple_dungeon"
         <span style="color:#7d7d7d">looks like an ID, but 'loot' names a Condition</span>
  <span style="color:#ad6c19">WARN</span>   mypack:lostcities/buildings/tower.json:13  range "0,2,9" has more than two numbers
         <span style="color:#7d7d7d">The mod reads the first two and discards the rest, silently</span>
</pre>

It catches floor ranges that leave a level with nothing to build, conditions that can
never match, invalid block names, weighted lists that do not add up, layers that are
the wrong size, and two faults that otherwise pass in silence: a monorail part
written as a list, which stops a world style loading, and an inline palette written
as a bare list, which loads perfectly and generates an empty building.

<b>Nothing is blocked from loading.</b> The check tells you what is wrong and lets the
pack run.

<h2><span style="color:#ad6c19">Ask why a chunk generated the way it did</span></h2>

<pre>
/lcdev report                     profile, world style, city style, building, and the part on each level
/lcdev key <i>name</i>                   what a profile key means, its section, type, range and default
/lcdev char <i>G</i>                     what a palette character resolves to here
/lcdev block <i>minecraft:gold_block</i>   which characters produce that block here
/lcdev in <i>mypack:mystyle</i> char <i>G</i>    the same lookup inside one named asset
</pre>

<code>in</code> lets you inspect a named file without finding a generated city first,
which is the difference between testing a condition and waiting to see whether it
worked.

Tab completion does not read every loaded file on every keystroke. On a server
holding 911 Lost Cities assets that cost
<span style="color:#d64545"><b>99 ms a character</b></span>, close to two seconds to type
one name; it is <span style="color:#2f8a4e"><b>0.1 ms</b></span> now. A lookup that
matches hundreds of assets prints the first dozen and counts the rest, rather than
answering with a reply too large to carry.

<h2><span style="color:#ad6c19">Comments in your files</span></h2>

JSON does not allow comments. DevTool does:

<pre>
// The tower at the centre of the city
{
  "filler": "#",
  "parts": [
    { "part": "mypack:origin" }, // used on every level
  ],
}
</pre>

Trailing commas work too. Files can be named <code>.json</code> or <code>.json5</code>,
and where both exist the <code>.json5</code> one wins. This applies to your datapacks
and to your Lost Cities profiles.

<h2><span style="color:#ad6c19">Where it goes, and where your files can live</span></h2>

Your Lost Cities files can stay where you already keep them: the world's
<code>datapacks</code> folder, a global datapack loader, or <code>kubejs/data</code>.

Everything that matters runs on the server. The workshop, export and import, reading
<code>.json5</code>, the load-time check, the better error messages and every
<code>/lcdev</code> command all live there. Only the Lost Cities menu fixes are client
side, so a client install is optional and a client without the mod can still join a
server that has it. In single player, one install covers both.

<span style="color:#d64545"><b>The machine loading the pack does need it.</b></span>
Without DevTool, Lost Cities cannot read a <code>.json5</code> file at all, and a
<code>.json</code> file with comments or trailing commas fails to load.

Every <code>/lcdev</code> command needs permission level 2, which means <code>op</code>
on a server and cheats enabled in single player. It teleports between dimensions,
writes tens of thousands of blocks and writes files beside your world, so it is a tool
for building a pack rather than a feature for players.

<h2><span style="color:#ad6c19">Optional fixes</span></h2>

Two fixes correct bugs in Lost Cities itself. Both are
<span style="color:#d64545"><b>off by default</b></span>, because turning one on changes
what a seed generates, and each is switched separately in
<code>config/lostcities_devtool-common.toml</code>.

<ul>
  <li>A <code>belowpart</code> condition that checks the part below it, as its name says</li>
  <li>A <code>streetblocks.parts.full</code> option that can actually be selected</li>
</ul>

Two more are on by default and touch only the Lost Cities menus, so they cannot change
a world. Right-clicking the profile button walks back through the list, so overshooting
the profile you wanted no longer means cycling all the way around. The Cities button
also stays where it is when you resize the window.

<h2><span style="color:#ad6c19">Sphere worlds do not crash on a broken file</span></h2>

Some Lost Cities world types take the server down when a chunk fails to generate.
Measured on the same pack and seed: <span style="color:#d64545"><b>21 crashes</b></span>
before, <span style="color:#2f8a4e"><b>none</b></span> after, with all 338 errors
logged instead. The broken chunk still fails, and nothing about the fault is hidden or
changed. This is on by default, can be turned off, and covers
<code>spheres</code>, <code>cavernspheres</code> and <code>space</code>.

<h2><span style="color:#ad6c19">Try it before you write anything</span></h2>

Three example datapacks are
<a href="https://github.com/RinkyDinkyNooble/the-lost-cities-wiki/tree/main/docs/examples/json5-test">in the wiki repository</a>.
They build the same small city three different ways, so you can see how the files fit
together before starting your own.

Every command, argument and flag is written up in
<a href="https://rinkydinkynooble.github.io/the-lost-cities-wiki/tooling/lcdev/">The DevTool Commands</a>,
and the rest of the
<a href="https://rinkydinkynooble.github.io/the-lost-cities-wiki/">Lost Cities Wiki</a>
covers the format itself with examples.

<h2><span style="color:#ad6c19">Credits and licence</span></h2>

The Lost Cities is created by <b>McJty</b>. The Lost Cities Discord answered questions
that no documentation covered.

DevTool is an unofficial companion mod and is
<b>not affiliated with or endorsed by McJty or The Lost Cities.</b>

Released under <a href="https://opensource.org/license/0bsd">0BSD</a>.
