# Mare Liberum

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
- **Main-story missions** — the first eleven resolve Captain Vane's threat and establish the Free Captains' Code. The next twenty-nine follow the Meridian Company and Commodore Silas Ashcombe, uncovering an attempt to seize the trade routes and culminating in **A Sea Without Masters**.
- **Optional side adventures** — self-contained stories about islanders, working sailors, a doctor, a sailmaker's apprentice, a lighthouse, a whaling family and a small raider. They offer modest rewards and do not block the main campaign.

The main story no longer forces every chapter to begin at the port where the previous voyage ended. Several new leads send you to a different harbour, and the character who closes the previous chapter mentions who is waiting there and why. These are personal recommendations and local rumours, not a mechanical instruction to "continue the storyline". The journal records each lead, and you can take repeatable harbour jobs or side adventures before following it.

At a port, choose **Ask whether there is work for a captain** to browse available main and side adventures. When several are posted, the harbourmaster presents a selectable list with their descriptions and rewards. You can accept one narrative mission at a time, while continuing to carry several repeatable day jobs at once.

Mission files are plain text. They support categories (`intro`, `main`, `side`), prerequisites, natural follow-up leads, conversations, choices, labels, branches, port voyages, named combat fleets, visit/debrief scenes and rewards.

## Other game systems

- Wind- and momentum-based sailing, plus rowers and oars (**O**).
- Broadside cannon combat (**hold Z** for port, **hold X** for starboard): the opening battery volley is synchronized, then each cannon reloads and fires independently with randomized timing. Hostile ships use distinct hull silhouettes too.
- Working sea traffic: merchantmen, fishing boats, naval patrols, mail packets and whalers sail between ports, with their own ship types and paint schemes.
- Independent NPC fleet battles: pirates raid merchantmen and challenge naval patrols; navy patrols hunt pirates; armed merchants defend themselves when threatened. Ships manoeuvre for broadsides, exchange cannon fire, take hull damage and can be sunk without the player taking part. NPC victories and losses do not count as player combat mission kills or bounty credit.
- Named NPC fleet commanders develop persistent records. Victories improve standing, lost ships damage it, and destroyed squadrons are recorded as defeats. Pirate captains build notoriety through successful raids; commanders who withdraw are remembered for their retreats. Press **N** for the Admirals' & Captains' Ledger.
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
| N | Admirals' & Captains' Ledger |
| F5 | Save a named voyage |
| Esc / F9 | Pause menu: resume, save, load, main menu, quit |
| Mouse wheel | Zoom toward pointer |
| Mouse drag | Pan camera |
| C | Recenter camera on ship |

## Living harbours and coastal defence

The sea remains active while the captain is berthed. Merchantmen, fishing boats, mail packets, patrols and whalers continue on their routes while you are docked or using harbour conversations, the journal, job board or shipyard. Pirates also continue to sail in the region; they can approach and circle a harbour, but will not fire directly on a ship protected by the quay.

Every port has visible coastal guns. When a pirate enters the harbour's defensive waters (590 world units from the port), the battery automatically fires a three-shot salvo and reloads before firing again. Port cannonballs damage pirate ships. Sinking a raider with harbour artillery does not award the captain a bounty or count as a personal mission kill. Coastal battery reload timers are saved in `.tide` voyage files.

## Independent naval battles

The living sea now has its own combat. Pirate captains select nearby merchantmen or navy patrols as targets and manoeuvre to bring their broadsides to bear. Naval patrols actively search for pirates and carry a heavier four-gun salvo; armed merchantmen return fire when raiders threaten them. Fishing boats, mail packets and whalers generally avoid combat.

These engagements happen while you are sailing, docked, or using harbour conversations and shipyard screens. NPC cannonballs damage the intended opposing ship group: pirate fire can sink merchant and naval traffic, while merchant and navy fire can sink pirates. NPC kills are recorded as world events but do not award the player a bounty or advance a player-fired combat mission. Ship combat targets and reload timers are included in named `.tide` saves.


### NPC Fleet Command
NPC vessels may sail alone or in named formations. Merchant convoys, naval squadrons and pirate bands have named commanders, maintain loose sailing stations, coordinate target selection and can withdraw when their remaining hull strength falls below the command threshold. These are autonomous world-simulation behaviours; the player need not join the engagement.


### Commander Reputation & Notoriety
NPC fleet commanders build a public record independently of the player. Victories and captures raise standing; losses and destroyed squadrons damage it; retreats are noted. Pirate captains gain notoriety for successful attacks and become known by increasingly fearful titles. Press **N** to open the Admirals' & Captains' Ledger. 