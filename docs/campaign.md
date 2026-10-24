# The campaign page

`dist/campaign.html` is the GM's console over the other pages. It knows the phase the campaign is in,
says what to do in it, shows where things stand, keeps the campaign's log, and shows the page for the
step below it. The pages are unchanged: each keeps its own state in the browser and hands pieces to
the others, as before, and each still works on its own. The console reads what they hold and follows.

## The loop

| Phase | Page | What happens |
| --- | --- | --- |
| Muster | Team builder | Make the team; **Send to the roller** makes them named men the other pages know. |
| March | Travel map | The campaign's map, the team's force on it, each named man **With** it (on his roller card); route, march, camp; the day's weather, food, sickness and incidents. |
| Fight | Roller or field map | **Fight here** on the travel map sends a skirmish to the roller or a battle to the field map. On the roller, **Run the fight** and **Play online** work as on their own. |
| Aftermath | Roller and travel map | First aid, **After the fight** (deeds, loot, prisoners), **To camp**; the battle's result and the wounded reach the travel map's camp. |
| Downtime | Team builder | Work, kit, the end of the season's rolls, replacements. Then back to the march. |

**Done: on to …** moves to the next phase and opens its page; the phase buttons jump to any phase.
The console also follows the pages by itself, and says so at the top:

- a fight sent from the travel map (to the roller or the field map) moves it to the **Fight**;
- a battle's result sent back from the field map, or a winner marked on the roller, moves it to the
  **Aftermath**.

Each is noticed once. A new campaign takes what the pages already hold as old news, not news to
follow.

**Where things stand** shows the team (and its losses and prisoners), the named men (with a force,
sick or mending, dead), the map and its day, and the fight, waiting or under way.

## Run the march

In the **March** phase the console shows the travel map's clock (the day, the time, the date, the
end of the day's marching) and its forces: what each is doing (marching to where, halted, making or
in a camp, resting, with another's column), where it is, how many are fit, and its fatigue.

**Until something happens** moves the map's clock on exactly as the travel map's button of that name
does: every force with a march order marches until one arrives, forces of different sides meet, or
a camp is finished, and the nights pass on the way with their rest, food, water, supplies, sickness,
incidents and the named men's feet, keep and kit. When the day's marching is done the button reads
**Pass the night**. What happened goes into the campaign's log. When forces meet, the console says
so and puts the travel map in the frame with the force selected, to set up the fight with **Fight
here**; the console then follows the fight as before.

The console never keeps the day itself: each press starts from what the travel map last saved and
saves the result, and the page in the frame is reloaded to show it. Routes, camps, orders and the
fight's set-up are still given on the travel map. If the travel map is also open in another tab,
reload it before using it: it still shows the day it had, and would save that over the console's.

## The log

Each phase the campaign moves to, and why, goes into the campaign's log at the travel map's day,
with the GM's own notes (for everyone, or ticked **GM only**). It is the same kind of log as the
roller's event log, with the same idea of who may see what, ready for players online.

## Saving the game

**Save the game to a file** writes every page's state (the team, the named men, the maps, the
fights, experience, purses, the campaign's log) as one `.json` file, to back up, move to another
computer or share. **Load a saved game** replaces every page's state in this browser with the
file's, after asking. The narrator's settings stay out of save files and are left alone by a load:
they may hold a service key, and they belong to the browser, not the game.

## What it does not do yet

- It runs the march's clock (Run the march), but not the rest: orders, routes, camps and the
  fight's set-up are given on the travel map, and the fights on the roller and the field map.
- It notices fights sent and fights won; it does not yet notice the end of a march day, the end of a
  season, a man's death or a camp's sickness by themselves (the GM moves on with **Done**).
- The other pages do not link back to it; open it from the start page.
- The pages' own state is still per page; a campaign's whole state exists only as a save file.

## Tests

`node tools/campaign/test.js` checks the console's reading of the pages: the status, what it
notices, and save files. `python3 tools/campaign/loop.py` follows a campaign round the loop in a
headless browser over the real pages, served by a local web server: the team rolled in the frame,
the travel map's forces given routes and the clock run from the console until they meet, a long
march across nights until a force arrives, a fight sent from the travel map, a winner marked on the
roller, notes, and a save, clear and load. `python3 tools/travel/parity.py` (in CI) also checks the
console's way into the day with no page: the summary changes nothing, a press moves on and saves,
and a meeting is reported.
