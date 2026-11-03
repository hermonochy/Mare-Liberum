# Tidebound: Caribbean Pirates

A top-down Caribbean pirate sailing game built with Python and Pygame. All scenery, ships, ports, and interface graphics are drawn in code; no external art or sound files are required.

## Run

```bash
python -m pip install -r requirements.txt
python main.py
```

## Controls

- `W` / `S`: raise or reef the sails
- `O`: deploy or stow the oars; rowers provide steady forward power in a headwind
- `A` / `D` or `Left` / `Right`: steer with the rudder
- `E`: dock at a nearby port or cast off
- `Q`: speak with the harbourmaster while docked
- `B`: open the shipyard while docked
- `F`: order the fleet to fight and hunt nearby pirates
- `H`: order the fleet to hold fire while keeping formation
- `G`: order the fleet to gather in a close formation around your flagship
- `V`: order the fleet to follow in its regular formation
- `R`: recover a nearby bottle or search a mapped beach
- `T`: open the treasure charts
- `Z`: fire the port-side broadside
- `X`: fire the starboard-side broadside
- Mouse wheel: zoom in or out centred on the pointer
- Left-, right-, or middle-mouse drag: pan the chart
- `C`: recenter the chart on your ship
- `-` / `=`: zoom in or out around the screen centre
- `J`: captain's log
- `F1`: show or hide the help overlay
- `Esc`: close a conversation or panel, or quit

Begin at Port Royal. Sail with the wind when you can, but you are not helpless when it turns against you: press `O` to ship the oars and put your rowers to work. The oars add forward thrust whatever direction the wind blows, with a visible rowing animation on your flagship. Press `O` again to ship the oars. The number of rowers depends on your ship class, and oars are automatically stowed when you dock. Carry momentum through turns, and approach piers slowly. Pirates manoeuvre to bring their broadsides to bear and fire back. The early game starts quietly with one distant raider; reinforcements are spaced out and capped at two active enemy ships so new captains can learn to sail and fight before the larger campaign battles.

## Rowers and oars

Every flagship carries a bank of oars and a crew trained to use them. Press `O` at sea to deploy or stow the oars. Deployed oars add a steady pulse of forward thrust regardless of wind direction, making it practical to beat out of a harbour or continue a voyage when sailing directly into a headwind. Rowing works alongside whatever sail you have set, so a following breeze can still carry you at full sailing speed. The deck animation shows the rowers at their benches and the oars moving through the water. Larger ships carry larger rowing crews and produce more rowing power. Oars are stowed automatically when you dock.

## Shipyards, ships and personal fleets

Every harbour has a shipwright's yard. While docked, press `B` to open it, or speak to the harbour office with `Q` and choose to visit the shipwright.

The yard has five pages:

- **Flagship:** buy a different hull to replace your current vessel. Available classes are Sloop, Cutter, Schooner, Brigantine, and Frigate. Each hull changes durability, speed, turning and broadside strength. Your old flagship is traded in; your personal escorts remain with you.
- **Refits:** install up to three levels each of Long Guns, Reinforced Hull, Fine-cut Rigging, and Balanced Rudder. These improve broadside count and reload, maximum hull, sailing power and top speed, or turning response.
- **Fleet:** hire as many escort ships as you can afford: Sloops, Cutters, Schooners, or Brigantines. They sail in formation and fire their own side-mounted cannon broadsides according to your current fleet order. There is no escort limit. Use **F** to Fight, **H** to Hold Fire, **G** to Gather around your flagship, and **V** to Follow in formation. These are direct orders, not a cycling menu. You can also select the same orders on the Fleet page of the shipyard.
- **Repairs:** restore your flagship or all surviving escorts for gold. Escorts can be damaged by enemy cannonballs and disabled if their hull reaches zero; return to a yard to repair them.
- **Name & Colours:** rename your flagship and choose from five hull, trim and sail liveries.

Use the arrow keys to move through a shipyard page, Enter to purchase or install the selected item, and Left / Right to switch pages. Press `B` or `Esc` to leave the yard. At sea, fleet orders are assigned directly: `F` sends escorts to hunt and attack nearby pirates; `H` makes them hold fire while maintaining formation; `G` gathers them into close rings around your flagship; and `V` restores their wider following formation. Follow mode allows escorts to defend the fleet when pirates come close. Hire as many escorts as you can afford; the fleet has no fixed size cap. The shipyard Fleet page also offers all four direct orders.

## The campaign

The camera can be freely panned by dragging with any mouse button. Mouse-wheel zoom keeps the point beneath the pointer fixed on screen; press `C` to return to ship-follow mode. Interface, dialogue, and journal text have also been enlarged for readability.

The story follows an eleven-mission Caribbean campaign. It begins with a missing cartographer and a chart through the Devil's Teeth, then uncovers a corrupt governor's secret payments to Captain Vane. The player helps free captured crews, discovers a hidden shipyard and anchorage, joins Commodore Anne Bonny's free captains, and leads the attack that breaks Vane's fleet. The final voyage carries a charter for a new Free Captains' Code to Port Royal.

Missions are stored in `missions/*.mission`, separate from the game code. The indentation-based language is inspired by Endless Sky and supports:

- mission title, description, source port, destination port, reward, and objective metadata
- prerequisites with `to offer` and `has "Mission Name: done"`
- separate `on offer`, `on accept`, `on visit`, and `on complete` sections
- dialogue lines, branching `choice` blocks, `label` and `goto`
- explicit `accept`, `decline`, and `close` commands
- journal entries with `log`
- port-to-port voyages and ship-sinking objectives with `objective kills N`
- event-specific speakers with `speaker offer`, `speaker visit`, and `speaker complete`

At a port, press `Q`, ask for work, listen to the story, and choose whether to accept or decline. Declined offers remain available. Completing a mission unlocks the next chapter when its prerequisites are satisfied.

## Treasure hunting

Three drifting green-glass bottles can be recovered while sailing with `R`. Each contains a separate treasure chart with a sea clue and a beach riddle. Press `T` to study charts you have recovered. The charts lead to three hidden cays: Gannet Cay, Widow's Key, and Dead Man's Cay. Hidden islands appear as you approach them (or sooner when you have their chart), and then become solid land with beaches and palm trees. Come close to the marked beach and press `R` to examine the buried chest. Choose the right answer to the island's riddle to open it. A wrong answer is harmless; study the chart and try again. Each chest pays out gold and a unique keepsake.

Treasure controls:

- `R`: recover a nearby bottle or search a nearby mapped beach
- `T`: open or close the treasure chart collection
- `J`: open or close the captain's journal

## Project layout

- `main.py`: game loop, sailing physics, camera, world, ports, combat, shipyards, fleet AI, treasure hunting, pirate reinforcements, and interface
- `mission_system.py`: mission parser and dialogue node definitions
- `missions/`: eleven connected, editable story missions
- `requirements.txt`: Pygame dependency

## Campaign chapters

1. A Map in the Bottle
2. Black Sails at Dawn
3. Clear the Cutlass Shoals
4. The Governor's Ledger
5. The Price of Silence
6. The Gallows Tide
7. The Shipwright's Secret
8. The Compass of Dead Man's Cay
9. The Black Fleet Rises
10. The Last Broadside
11. A Free Caribbean

## Camera and readability

- Hold and drag any mouse button to pan freely around the sea chart, with no map-edge limits.
- Areas beyond the charted islands remain open ocean with procedurally drawn wave marks.
- Use the mouse wheel to zoom around the pointer location.
- Press `C` to return to a camera that follows your ship.
- Interface, help, journal, and dialogue type have been enlarged again, with expanded panels for readability.
- The game begins with one distant pirate ship. Reinforcements arrive slowly, and no more than two enemy ships pursue you at once; active combat missions bring reinforcements in sooner.
