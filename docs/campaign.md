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

It also notices, logs and shows at the top what happens by itself:

- a named man's death, on the march, in camp, of wounds or sickness: what he died of and his force;
- a man of the team taken prisoner;
- sickness breaking out in a force: the first cases of a disease (battle wounds are the fight's news,
  not sickness; wound fever is); once the force is clear of it, a new outbreak is news again;
- a force out of rations, water, medical stores or ammunition (news again once refilled and out
  again);
- a man's new rank (a rank first seen is only noted);
- the end of a day on the travel map: one line for the day or days that ended, with the weather
  and each side's forces, men and sick;
- the end of a season in the team builder (experience, rank and age rolled), which moves it to
  **Downtime**.

Each is noticed once. A new campaign takes what the pages already hold as old news, not news to
follow.

**Where things stand** shows the team (and its losses and prisoners), the named men (with a force,
sick or mending, dead), the map and its day, and the fight, waiting or under way.

## Run the march

In the **March** phase the console shows the travel map's clock (the day, the time, the date, the
end of the day's marching) and its forces: what each is doing (marching to where, halted, making or
in a camp, resting, with another's column), where it is, how many are fit, and its fatigue.

**Orders** on a force opens its orders, as the travel map gives them:

- **March to** a place on the map or an enemy force: **Set the route** replaces its route, **Add as a
  waypoint** adds to it. Only places it can reach on today's ground are offered; a route it cannot
  take is refused, and the old route stands.
- **Clear the route**, **Halt** or **March on its route**, and **Rest until next morning**.
- **Make camp**, with what the chosen camp costs here (the hours, the man-hours of its works, and
  where the timber comes from), or why it cannot be made here.

A force marching in another's column takes that force's orders; leaving a column, joining one,
and the force's own settings (its load, its men and horses, hygiene, foraging and the rest) are
still set on the travel map. Each order starts from the saved day, is saved, and goes into the log.

**Until something happens** moves the map's clock on exactly as the travel map's button of that name
does: every force with a march order marches until one arrives, forces of different sides meet, or
a camp is finished, and the nights pass on the way with their rest, food, water, supplies, sickness,
incidents and the named men's feet, keep and kit. When the day's marching is done the button reads
**Pass the night**. What happened goes into the campaign's log. When forces meet, the console says
so and puts the travel map in the frame with the force selected.

**Fights on offer** lists every fight that can be set up where enemies are within reach, as the
travel map's **Fight here** would set it up: who attacks whom (and who stands with the defender),
where, when, who will miss it, and the odds of surprise. Each has the page to fight it on (the
roller, the field map on open ground, or a battlefield drawn up nearby, chosen by default as the
travel map chooses), and **Attack now** and **Wait for the camp** when the defender's camp is not yet
finished. Sending one rolls the surprise, writes the handoff the roller or the field map reads, logs
it, moves the console to the **Fight** and opens that page.

In the **Aftermath**, when the field map has sent a battle's result back, **Take the battle's result
into the travel map** applies it from the console: the dead come off, the wounded go to the camp,
ammunition is as the units left it, and the forces' clocks move on to the battle's end. The travel
map still takes it itself if it is opened first; either way it is taken once.

The console never keeps the day itself: each press starts from what the travel map last saved and
saves the result, and the page in the frame is reloaded to show it. A travel map open in another
tab follows too: when the day changes elsewhere it takes the new one and says so, rather than save
the day it had over it. (The roller and the team builder in another tab do not yet: reload them.)

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

- It gives routes, orders and camps, runs the march's clock, sets up fights and takes a battle's
  result back; columns, the forces' own settings, adding forces and painting the map are on the
  travel map, and the fights are fought on the roller and the field map.
- The pages' own state is still per page; a campaign's whole state exists only as a save file.

## Tests

`node tools/campaign/test.js` checks the console's reading of the pages: the status, what it
notices (fights, deaths, prisoners, outbreaks and supplies out over and back, ranks, the end of
days and of a season), and save files. `python3 tools/campaign/loop.py` follows a campaign round the loop in a
headless browser over the real pages, served by a local web server: the team rolled in the frame,
a force's route given from the console, the clock run from it until the forces meet, a long
march across nights, a fight set up from the console where the forces met,
a battle's result taken in from the console, the end of the days logged by itself, the end of a
season moving it to downtime, a fight sent from the travel map, a winner marked on the
roller, notes, and a save, clear and load. `python3 tools/travel/parity.py` (in CI) also checks the
console's way into the day with no page: the summary changes nothing, a press moves on and saves,
a meeting is reported, orders (routes, march and halt, camp and rest) are given and saved and a
refused route changes nothing, the fights on offer are sent as Fight here sends them, and a battle's result
is taken in once.
