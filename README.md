# Tidebound: Caribbean Pirates — Version 16

A top-down Caribbean sailing adventure built with Python and Pygame.

## Install and run

```bash
python -m pip install -r requirements.txt
python main.py
```

Run from this directory so the game can find the `missions/` folder.

## World and navigation

The sea chart contains five island regions, 23 inhabited ports, and 16 uninhabited cays scattered between the main island chains:

- **Old Caribbean** — Port Royal, Tortuga, Havana; the starting region.
- **Windward Reach** — Isla Verde, Saint Brigid, Lantern Bay, Port Azure, Pelican's Rest.
- **Leeward Expanse** — Blackwater Reach, San Telmo, Mariner's Rest, Puerto Cielo, Cormorant Quay.
- **Spanish Main** — Nueva Esperanza, Crown's Fall, Sugarhook, Port de Lune, Santa Isabela.
- **Outer Antilles** — Mermaid's Rest, Stormhaven, Redoubt, Saint's Refuge, Last Light.

The port islands are scattered in irregular diagonals and loose arcs rather than repeated rows or trapeziums. Smaller uninhabited cays break up long empty stretches, including the lower-left waters that were previously almost vacant. The regional island shapes vary in size, shoreline and orientation. Port approaches are kept clear of neighbouring land. The Port Royal departure water remains open, with the east, south and west sailing arcs clear of nearby islands. There is no world-edge collision or invisible sailing boundary: leave the charted regions and the ocean continues. Hold and drag the mouse to pan, use the wheel to zoom around the pointer, press **C** to return to ship-follow mode, and press **M** to open the full atlas. The minimap follows nearby waters and points toward distant objectives.

## Stories, side adventures and introduction

There are **51 authored narrative missions** in `missions/`:

- **1 introductory voyage** — *An Old Captain's Farewell*. At Port Royal, retiring Captain Elias Ward offers a natural first job: take his sea chest and letter to his old quartermaster in Tortuga. During the conversation he explains sailing, oars, docking, harbour work, treasure maps, cannon broadsides, escort commands, shipyards, the atlas and the traffic on the sea. The first main-story job is unlocked after this short voyage.
- **40 main-story missions** — the first eleven resolve Captain Vane's threat and establish the Free Captains' Code. The next twenty-nine follow the Meridian Company and Commodore Silas Ashcombe, uncovering an attempt to seize the trade routes and culminating in **A Sea Without Masters**.
- **10 optional side adventures** — self-contained stories about islanders, working sailors, a doctor, a sailmaker's apprentice, a lighthouse, a whaling family and a small raider. They offer modest rewards and do not block the main campaign.

The main story no longer forces every chapter to begin at the port where the previous voyage ended. Several new leads send you to a different harbour, and the character who closes the previous chapter mentions who is waiting there and why. These are personal recommendations and local rumours, not a mechanical instruction to "continue the storyline". The journal records each lead, and you can take repeatable harbour jobs or side adventures before following it.

At a port, choose **Ask whether there is work for a captain** to browse available main and side adventures. When several are posted, the harbourmaster presents a selectable list with their descriptions and rewards. You can accept one narrative mission at a time, while continuing to carry several repeatable day jobs at once.

Mission files are plain text. They support categories (`intro`, `main`, `side`), prerequisites, natural follow-up leads, conversations, choices, labels, branches, port voyages, named combat fleets, visit/debrief scenes and rewards.

## Other game systems

- Wind- and momentum-based sailing, plus rowers and oars (**O**).
- Broadside cannon combat (**hold Z** for port, **hold X** for starboard): the opening battery volley is synchronized, then each cannon reloads and fires independently with randomized timing. Hostile ships use distinct hull silhouettes too.
- Working sea traffic: merchantmen, fishing boats, naval patrols, mail packets and whalers sail between ports, with their own ship types and paint schemes.
- Ships physically collide and rebound. Player ships, escorts, pirates and civilian traffic separate rather than passing through one another; newly hired escorts are assigned spaced formation berths immediately.
- Pirate pressure grows with your assets: a valuable flagship, upgrades, escorts, relics and gold shorten the interval between pirate sightings and can attract larger groups. Roaming pirates are no longer capped at two, so surviving raiders remain at sea until dealt with.
- Story offers include a measured route note in chart miles. Combat missions measure the full route via the battle area and onward to the debrief port.
- Personal escort fleets with no fixed ship-count cap: **F** fight, **H** hold fire, **G** gather, **V** follow.
- Shipyards (**B** while docked) for buying hulls, refits, customisation, fleet hiring, and repairs.
- Treasure bottles, hidden islands, maps, riddles, and buried chests (**R** to interact, **T** to view charts).
- A harbour job board with five simultaneous offers per port: compare destinations and pay, select one or several (the keyboard focus is outlined), and carry multiple jobs at once. Repeatable work includes cargo, letters, passengers, and rescues (**Q** at a harbour, then choose the job board; **R** for rescue).
- Captain's journal (**J**) and help overlay (**F1**).

## Controls

| Key | Action |
|---|---|
| W / S | Set or reef sails |
| A / D | Steer |
| O | Deploy / stow oars |
| Hold Z / X | Fire port / starboard batteries; cannons reload independently |
| E | Dock / cast off |
| Q | Harbour office; choose the job board in the conversation |
| Job board | Up / Down move, Space tick jobs, Enter accept selected; or click rows and Accept |
| B | Open shipyard while docked |
| F / H / G / V | Fleet: fight / hold fire / gather / follow |
| R / T | Interact / view treasure maps |
| M | Full world atlas |
| J / F1 | Journal / help |
| F5 | Save a named voyage |
| Esc / F9 | Pause menu: resume, save, load, main menu, quit |
| Mouse wheel | Zoom toward pointer |
| Mouse drag | Pan camera |
| C | Recenter camera on ship |

## Project layout

- `main.py` — launcher.
- `tidebound/game.py` — game setup and main loop.
- `tidebound/config.py` — world, ships, region and port data.
- `tidebound/models.py` — game data models.
- `tidebound/geometry.py` — movement, collision and propulsion helpers.
- `tidebound/dialogue.py` — branching conversation runner.
- `tidebound/mission_system.py` — parser for the editable mission format.
- `tidebound/mixins/` — separate systems for controls, camera, sailing/combat, rendering, missions, day work, treasure, shipyard/fleets, ambient shipping and save/load.
- `missions/` — 51 authored narrative mission files (1 introduction, 40 main-story missions, 10 optional side adventures).
- `saves/` — created automatically; stores one human-readable `.tide` file per named voyage.


## Saving and loading voyages

Tidebound now opens with a main menu. Choose **New Voyage**, **Load Voyage**, or **Quit**. Press **F5** while playing to save a named voyage. The game writes a readable `.tide` text file in the `saves/` directory. These files are indented JSON with named sections for the captain, ship, last berth, story, treasure, fleet, ships at sea and day work; they can be opened in any text editor.

Press **Esc** or **F9** to open the pause menu. From there you can resume, save, load another voyage, return to the main menu, or quit. Multiple named saves are supported. A save records the last harbour you docked at. When loaded, your flagship is berthed there and your escorts are placed in formation nearby, even if you saved while sailing elsewhere.
