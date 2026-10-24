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
- in a skirmish on the roller, a named man (one with a team-builder sheet) down or out of the
  fight, with the round, and a side whose morale breaks;
- in a battle on the field map, a unit broken or fled, with the exchange;
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

## The fight

In the **Fight** phase, with the wound roller in the frame, the console shows the roller's fight
as it stands: the round, whose turn it is and who plays him, each side (who plays it, broken or
not) with each man's Blood and whether he is down or out, and the fight's last events. Its buttons
work the roller's **Run the fight**: turn it on (the sides with no player go to the GM's script),
**Step**, **Play to my turn**, **Undo the script**, and **End his turn** when it is a person's turn
(he moves and strikes on the roller below). When one side still stands, **Mark … the winner** marks
it as **After the fight** does, and the console moves on to the aftermath.

With the field map in the frame, the panel is the battle's: a battle sent from the travel map
waiting to be set up (**Set it up**), the exchange and which side moves, each side's units still
standing and men, who moves each side (the GM, or the commander attacking or holding), and the
battle's last lines. **Start the battle**, **Next**, **Run** (when the commander has both sides),
**End the battle**, and **Send the result to the travel map**, which leaves the result as **Back to
the travel map** does without leaving the page; the console then moves to the aftermath, where
**Take the battle's result** applies it. Placing and ordering units by hand is on the field map.

The console asks; the roller or the field map does it, as its own buttons would, and tells the console how the fight
stands after every change (by the browser's messages between a page and the page in its frame;
each answers only the page that holds it, and a player's page joined online never). The
moves, strikes, first aid and the rest are still made on the roller.

## Players online

**Players online** on the console gives each player one link for the session (copy and paste, as
on the roller: no server yet). The GM adds a player, ticks the named men he plays (one or more; it
can be changed at any time), and sends him the link; his page (the campaign page, opened from the
link) gives a reply code the GM pastes back. His page then shows:

- **Your men**: each of his named men, how he is (well, sick, his wounds mending, dead), the force
  he is with, and his purse;
- **Your force**: the map's day and hour, and each force his men are with (its orders, where it is,
  how many are fit, its fatigue, its route and its own log of the march);
- **News**: the campaign's log as he hears it: the public lines, not the GM's notes, and not the
  march clock's word on every force (his own force's comes in its own log).

The console draws his screen and sends him only that, whole the first time and then only what
changed (`NET.screenPart` in `templates/net.js`); nothing of another side's forces or named men
reaches his page. Who plays whom is kept with the campaign (its record, so in saves and slots);
the connections are not. If his page reloads it shows his last screen and rejoins; if he is lost,
or the console reloads, the GM presses **Invite again** and sends a new link, which he opens or
pastes into **Rejoin**.

**His fights come through the same link.** When the roller is in the console's frame and one of his
named men is among its fighters (matched by the travel map's id or the team builder's), the roller
gives that man's side to him, as **Play online** would, and draws his side's screen for him; the
console passes it on, and his page shows it under **Your fight**, where he moves, strikes, gives
first aid and ends his turn as on the roller's own player page. The roller checks every choice is
his to make. When the roller leaves the frame the fight goes from his page. The roller's own **Play
online** still works for a fight run without the console. (A fight set up from the travel map
fills the roller with the forces' men; his named men join it when the GM adds the team.)

Not yet: his proposed orders for his force (the GM accepts or declines them), room codes in place
of copy and paste, and the travel and field maps on his page.

## The log

Each phase the campaign moves to, and why, goes into the campaign's log at the travel map's day,
with the GM's own notes (for everyone, or ticked **GM only**). It is the same kind of log as the
roller's event log, with the same idea of who may see what: a player online hears the public lines.

## Saving the game

**Save the game to a file** writes every page's state (the team, the named men, the maps, the
fights, experience, purses, the campaign's log) as one `.json` file, to back up, move to another
computer or share. **Load a saved game** replaces every page's state in this browser with the
file's, after asking. The narrator's settings stay out of save files and are left alone by a load:
they may hold a service key, and they belong to the browser, not the game.

**Campaigns in this browser** keeps several campaigns side by side (in the browser's IndexedDB,
which holds far more than its ordinary storage). Each is every page's state, as a save file holds
it, under the campaign's name:

- it is kept by itself as the campaign moves on (each new phase, each day's end), and **Keep it
  now** keeps it at once; each of those moments is also a snapshot, the last eight kept;
- **Roll back to** a snapshot puts every page back as it was then;
- **Start another campaign** keeps this one and starts with every page empty;
- **Switch to it** keeps this one and brings another back whole: its team, map, fights, phase and
  log; **Delete** removes another (never the one in play).

The pages keep working on the browser's ordinary storage; switching swaps it all. A team builder or
roller open in another tab notices that the game changed under it and starts again from the new
one, rather than write the old one back (a roller hosting players online leaves that to the GM).
A save file is still the way to move a campaign to another computer.

## What it does not do yet

- It gives routes, orders and camps, runs the march's clock, sets up fights, runs the roller's
  script and marks the winner, runs a battle's moves on the field map and sends its result, and
  takes it back; columns, the forces' own settings, adding forces and painting the map are on the
  travel map, a person's moves and strikes on the roller, and placing and ordering units by hand on
  the field map.
- The pages' own state is still per page; a campaign's whole state exists only as a save file.

## Tests

`node tools/campaign/test.js` checks the console's reading of the pages: the status, what it
notices (fights, named men felled, units broken, deaths, prisoners, outbreaks and supplies out
over and back, ranks, the end of days and of a season), and save files. `python3 tools/campaign/loop.py` follows a campaign round the loop in a
headless browser over the real pages, served by a local web server: the team rolled in the frame,
a force's route given from the console, the clock run from it until the forces meet, a long
march across nights, a fight set up from the console where the forces met,
the roller's fight run from the console (Run the fight, Step, a player's turn ended, Undo, the
winner marked), a battle's result taken in from the console, the end of the days logged by itself, the end of a
season moving it to downtime, a fight sent from the travel map, a winner marked on the
roller, notes, and a save, clear and load, on dice seeded from its argument (CI runs it with seed 1,
in the browser workflow, on every pull request that changes the pages). `python3 tools/travel/parity.py`
(in CI) also checks the
console's way into the day with no page: the summary changes nothing, a press moves on and saves,
a meeting is reported, orders (routes, march and halt, camp and rest) are given and saved and a
refused route changes nothing, the fights on offer are sent as Fight here sends them, and a battle's result
is taken in once. `python3 tools/net/console.py` (in CI, with the other browser tests) connects the
console and a player's page in browser profiles of their own: his men, his force and the public
news shown and nothing of the enemy's or the GM's notes, the march followed by changes only, the
men he plays changed, his page and the console each reloaded and joined again, and his fight on the
console's roller played from his page on the same link.
