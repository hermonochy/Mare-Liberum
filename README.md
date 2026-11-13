# Mare Liberum

A top-down Caribbean sailing adventure built with Python and Pygame. Take command of a small vessel, cross a dangerous archipelago, and make your fortune among rival crowns, merchant leagues and pirate brotherhoods.

Sail between busy harbours and remote cays. Follow a long-running story, take on local work, trade goods between changing markets, hunt for treasure, explore shipwrecks, or build a fleet of your own. The sea is alive with merchant convoys, naval patrols and pirate squadrons—and they have business with one another whether you are nearby or not.

## Getting started

### Requirements

- Python 3.10 or newer
- Pygame 2.5 or newer

### Install

Download or clone the project, then open a terminal in the project directory.

Create and activate a virtual environment.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the game dependency:

```bash
python -m pip install -r requirements.txt
```

## Running the game

Start the game from the project directory:

```bash
python main.py
```

On systems where Python is invoked as `python3`, use `python3 main.py` instead.

The main menu lets you begin a new voyage, load a saved voyage, adjust display and sound settings, open the Captain's Guide, or quit.

## Your first voyage

You begin in Port Royal aboard a modest sloop. An introductory encounter with an old captain introduces the basics of sailing, harbour work, trading, treasure and combat through conversation. Speak with the harbour office to hear local news, meet people, find work and learn about the next leads in the story.

There is no single way to spend your time. Follow the main story, accept optional adventures, carry passengers between several ports, earn money through trade, salvage wrecks, or simply explore. Many conversations are not job offers: people may share rumours, introduce a useful contact, offer a rare item, or try to sell you something of questionable value.

## How to play

### Sailing and navigation

Your ship responds to wind, sail setting, momentum and steering. Use **W** to make sail and **S** to reduce sail. Turn with **A** and **D**. On oared craft such as launches, cutters, sloops, yawls and xebecs, deploy the oars with **O** when the wind is unfavourable. Oars provide slower, steady propulsion and can help you manoeuvre in tight approaches. Both banks row together in a synchronized stroke.

The compass points towards your current story objective or, when you have no active story mission, a useful nearby harbour task. Open the world atlas with **M** to inspect the chart. Use the mouse wheel or **+ / -** to zoom, drag to pan, and press **C** to centre the view on your ship.

Approach a harbour slowly and press **E** to take the nearest available berth. The nine quay slots are shared with visiting ships; no berth is permanently reserved for the player. If the harbour is full, wait for a vessel to leave and try again. Docking opens the port services screen automatically. Choose **Depart** to cast off; press **Esc** to close the screen and **E** to reopen it while still berthed.

Watch for reefs. Their warning areas are marked in translucent red on the chart and in the world. Crossing a reef damages the hull, with greater danger at speed. NPC ships try to steer around reefs, but a battle or a poor approach can still put them in danger.

### Ports, people and local work

The port services screen brings the harbour's activities into one place. Its navigation column links the port overview, trade market, job board, harbourmaster, shipyard, outfitter, repairs, fleet orders, diplomacy and captain's log. The overview presents local harbour information and news. The harbourmaster conversation still handles story contracts, rumours, unusual purchases, local secrets and scams. The job board offers repeatable tasks such as cargo deliveries, letters, passenger passages and rescues. Several routine jobs can be active at the same time.

Some authored missions have several required port calls. Follow the route in order: collect passengers, documents or other items at each waypoint, then continue to the final destination. The compass and journal show the next required stop. Visiting the final port early will not complete a mission if an intermediate call remains outstanding.

The **Shipyard** and **Outfitter** share a persistent **Your Ships** panel. Select either the flagship or any escort to inspect its class and hull condition, rename it, jump directly to its refits, or sell it from the same panel. The shipyard lets you commission a replacement flagship or add a new escort without leaving the screen. Selling the flagship transfers command to a surviving escort when one is available; the promoted vessel remains safely moored at the current berth. The outfitter offers eight fitting groups for each selected vessel: hull form, hull finish, sail design, sail type, flag, cannon type, cannon mounting and visual upgrades. Installations are charged per ship and persist in the existing voyage save. Repairs can be made to one vessel or to the entire fleet.

Hull forms change strength, speed, turning, cargo capacity and the silhouette of the vessel. Sail types affect speed and sail power, while sail designs change the canvas pattern and colours. Pirate captains can fly their colours on weathered canvas with a skull-and-crossbones mark, or commission the Black Jolly Roger Canvas at the shipyard. Choose from different ensigns, hull finishes and deck fittings such as carved figureheads, gilded rails, stern galleries, lanterns and reinforced bulwarks. Cannon types have distinct projectile speed, range, damage and reload characteristics: Long Nines reach farther, Demi-cannons hit harder, Carronades deliver heavy close-range damage and Swivel Guns reload quickly. Broadside batteries remain the standard installation; Bow & Stern Chasers add forward and aft shots, while Rotating Turrets automatically track nearby hostile ships. Mounting choices are restricted by ship size, so small craft cannot carry the heaviest turret installations. Chasers fire with **Q** (forward) and **E** (aft) while at sea; rotating turrets fire with **Z / X** and turn toward the nearest hostile target.

The ship catalogue ranges from small launches, cutters and sloops to xebecs, schooners, brigs, corvettes, frigates, merchantmen, galleons and ships of the line. Classes have distinct hull dimensions, handling, speed, cargo, strength, sail plans and refit limits. Cannon capacities are class-specific: a sloop can carry up to 10 guns, a frigate up to 30, and a ship of the line up to 48. Some light or cargo-focused vessels cannot take every kind of refit. Ship names are assembled from a large prefix-and-suffix pool, providing more than 12,000 combinations before the fallback naming system is needed.

### Trading and cargo

Choose **Trade & Cargo** in the port services screen to open the market. Fifteen goods are traded across the ports, including foodstuffs, spirits, tobacco, spices, ship supplies, tools, gunpowder, silver and contraband. Prices differ by harbour and change as local stock, demand, production, consumption and trade activity change.

Buy where goods are plentiful and sell where they are scarce. The market shows indicative trade-route opportunities and estimated returns, but a price forecast is not a promise: the market may move while you are at sea. Cargo occupies hold space, and each ship class has a different capacity. Cargo-hold refits increase that capacity. The market screen shows your manifest, remaining space and purchase costs.

Trading affects more than your purse. Supplying wanted goods can ease shortages and improve a faction's prosperity and its attitude towards you. Buying up scarce stock, selling contraband or disrupting a trade route can have the opposite effect. Prosperity and shortages also influence merchant activity around the islands.

### Combat and your fleet

Hold **Z** to fire the port-side battery or **X** to fire starboard. Standard batteries fire in broadsides; after the first volley, individual cannons reload independently. Rotating turrets instead track the nearest hostile vessel, and Bow & Stern Chasers fire forward with **Q** or aft with **E** while at sea. Cannon types change projectile range, damage and reload time. Cannon impacts leave visible scorch and splinter damage. Smoke puffs originate at the firing guns, and a broadside gives the ship a brief recoil.

Your escorts can fight alongside you. Give them orders with **F** to fight, **H** to hold fire, **G** to gather around the flagship, or **V** to follow in formation. Firing on a normally friendly vessel turns it hostile; its surviving squadron may join the fight, and the attack can damage your standing with its faction.

NPC fleets can form around named commanders. Merchant convoys, pirate bands and navy squadrons coordinate movement and attacks, may retreat when badly damaged, and build reputations through victories, losses and retreats. Pirates, merchants and naval ships can fight each other without the player's involvement. The world can also generate major scripted encounters independently of the main story. A growing escort fleet may attract a delayed, randomly timed armada whose ship count and combat strength scale against your own vessels.

Ships show progressive battle damage. A vessel that loses all its hull sinks, leaving floating wreckage that eventually disperses. Losing your flagship ends the current voyage. After the sinking sequence, load a saved voyage to continue; progress made since that save is lost. The game does not create a rescue save when your ship sinks.

### Factions and diplomacy

The six powers are the British Crown, Spanish Crown, French Crown, Merchant League, Pirate Brotherhood and Independent settlements. Tortuga, Wreckers’ Moon and Gallows Key are independent free harbours despite their pirate traffic and associations, so ordinary story visits do not automatically mean the harbour itself is at war with you. Open the diplomacy ledger with **I** to see your standing with each faction. Relationships range from hostile through neutral to friendly and are shaped by your actions: completing work, supplying scarce goods, attacking ships, sinking convoys and making gifts all have consequences.

Ports may refuse entry when their faction considers you hostile, and coastal guns can defend their approaches. You can offer a gift while docked at a faction's port or request safe conduct to repair a hostile relationship. Individual admirals and pirate captains can also remember personal encounters. Press **N** to inspect the Admirals' & Captains' Ledger.

### Treasure, wrecks and discoveries

Treasure maps lead to hidden cays and buried chests. Press **T** to review charts you have found, and use **R** when you reach a marked location to investigate or dig.

Eighteen shipwrecks lie along the sea routes. Approach a wreck and press **R** to investigate. Surface salvage is generally safer and yields more modest cargo; a dive into the flooded hull can bring greater rewards, rare keepsakes and historical discoveries, but unstable timbers, powder stores, rigging and currents can injure your ship or salvage party. Each salvage opportunity can only be attempted once.

The journal, opened with **J**, records story leads, discoveries and important events.

## Controls

| Action | Control |
| --- | --- |
| Set sails / reduce sail | **W / S** |
| Steer | **A / D** |
| Deploy / stow oars | **O** |
| Fire port / starboard cannons or rotating turrets | Hold **Z / X** |
| Fire bow / stern chasers (when fitted, at sea) | **Q / E** |
| Dock at nearest available berth / reopen port services | **E** |
| Depart from port services screen | **E** or choose **Depart** |
| Speak with harbour office | Choose **Harbourmaster** (or **Q** when the port screen is closed) |
| Open shipyard / trading | Choose **Shipyard** / **Trade & Cargo** (or **B / Y** when the port screen is closed) |
| Close port services screen | **Esc** |
| Escort fleet: fight / hold fire / gather / follow | **F / H / G / V** |
| Interact with jobs, treasure and wrecks | **R** |
| View treasure charts | **T** |
| Open world atlas | **M** |
| Centre camera on ship | **C** |
| Zoom in / out | Mouse wheel or **+ / -** |
| Pan camera | Drag with mouse |
| Open captain's journal | **J** |
| Open Admirals' & Captains' Ledger | **N** |
| Open diplomacy ledger | **I** |
| Show / hide Captain's Orders | **F1** |
| Save voyage | **F5** |
| Pause menu | **Esc / F9** |

## Saving your voyage

Choose **Load Voyage** from the main menu to browse your named saves. During play, press **F5** to create a new named save. You can keep multiple named voyages. The game also creates or replaces a rolling **Autosave** every time you successfully dock at a harbour; this records the safe port and berth you have just reached.

A save records your last harbour and the actual berth you occupied. You can save while sailing; loading returns your flagship safely to that last berth, with your fleet and voyage progress restored. Gold, ship and refits, cargo, markets, active and completed missions, intermediate mission stops, jobs, treasure, wreck discoveries, faction economies, diplomacy and commander records are all stored in the human-readable `.mare` save file.

Save regularly before a dangerous voyage. If your flagship sinks, load the most recent Autosave or another named voyage; unsaved progress since the last docking or manual save is lost. Mission-event timers, completed encounters, world flags and event fleets are saved as part of the voyage.

## Mission events

Story missions and world events use the same `.mission` syntax and the same `missions` directory. An event starts with a line such as `event escorts > 10 and random > 50`. Expressions support comparisons, `and`, `or`, `not`, and parentheses. Available values include escorts, total fleet size and power, gold, world time, hull percentage, completed jobs, relics, region, docked port, at-sea status, cargo and random. Function conditions include `standing("Pirate Brotherhood")`, `flag("black_armada_defeated")`, `visited("Tortuga")`, `visits("Tortuga")`, `mission("A Letter in the Main")`, `upgrade("cannons")`, `cargo("rum")` and `event("the_black_armada")`. A random value is rolled once when the other conditions first become true, so `random > 50` is a genuine 50% chance rather than a repeated roll every frame. `event_cancel_if` supplies a cancellation expression. Repeated `event_action`, `event_on_complete` and `event_on_repelled` lines can display notices, write journal entries, alter gold, relations, cargo or flags, change mission states, or schedule, enable, disable and retreat other events. Additional `event_` keywords configure timing, fleet composition, strength, announcements and outcomes.

Event missions can configure a random delay, docking pauses, one-time or repeatable triggers, cooldowns and completion or retreat outcomes. Their fleet declaration supports selected ship classes, minimum, normal and hard maximum sizes, a strength multiplier against the player's current fleet, a named commander and custom ship names. Fleet power scaling accounts for hull strength and broadside size; if the hard ship limit is reached, individual enemy vessels are strengthened to meet the requested power ratio.

The included `black_armada.mission` triggers when the player has more than ten living escorts and wins the 50% random check. After a random delay of 110–260 in-game seconds, it arrives with at least sixteen warships and is sized to exceed the estimated combat power of the player's fleet. Its ships distribute attacks across individual escorts and the flagship. Enemy broadsides fire more frequently and use the ship's gun count to determine the number of cannonballs in each volley. The event remains active until the armada is destroyed or its surviving ships withdraw. Event state and spawned fleets persist across saves.

## Settings

Open **Text & Display Settings** from the main menu or pause menu to adjust text size, sound effects and sea ambience. The preferences are saved automatically and apply the next time you play. Sound can be disabled or reduced independently for effects and ambience.

The Captain's Guide is available from the main menu and pause menu. It contains a shorter in-game reference for sailing, combat, charts, discoveries and harbour life.


The dockside interface uses the same dark nautical palette as the rest of the game. Conversations opened from the dock remain within that interface, and the harbourmaster is reserved for special mission commissions; ordinary local work remains on the job board.
