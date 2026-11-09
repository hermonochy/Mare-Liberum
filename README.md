# Mare Liberum
### A Caribbean life under sail — Version 32

Take command of a small sailing ship and make your name across a living Caribbean. Trade, explore, hunt for buried treasure, take work from harbourmasters, build a fleet, or become the captain that every admiral fears. The sea carries on whether you are watching it or not: merchants cross between ports, pirate squadrons hunt prizes, and naval commanders fight battles of their own.

Mare Liberum is a single-player, top-down sailing adventure made with Python and Pygame.

## Getting started

You will need **Python 3.10 or newer**.

1. Extract the downloaded game folder.
2. Open a terminal or command prompt in that folder.
3. Install the required game library:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the game:

   ```bash
   python main.py
   ```

On some systems, use `python3` instead of `python`.

The game opens at the main menu. Choose **New Voyage** to begin, **Load Voyage** to continue one of your saved captains, or open the **Captain's Guide** for a short in-game guide to sailing, combat, navigation, ports and saving. The guide is also available from the pause menu while you play.

## Your first voyage

Your adventure begins at Port Royal in a modest sloop. An old captain at the harbour has one last favour to ask. Hear him out: his conversation introduces sailing, rowing, harbour work, treasure, cannon fire and the other ways to make a living at sea.

You do not have to follow the main story every time you reach port. Speak with people, look over the local work, visit the shipyard, or simply cast off and see what lies beyond the next island.

## Sound and atmosphere

Mare Liberum includes an original soundscape: offshore wind and rolling waves, flapping canvas, broadside cannon fire and cannonball impacts, plus a low harbour murmur. The current sound mix deliberately leaves out seabirds, wooden hull creaks, port-activity noise and important-encounter music. Sound starts automatically when the voyage begins; the game will still run if the computer has no available audio device.

Cannon discharges now push the firing vessel back slightly. A small, short-lived powder puff appears at each individual gun muzzle, rather than blooming from one fixed point on the ship. The recoil is subtle but visible in the ship's movement, especially during a full broadside.


## Comfort and presentation settings

Open **Text & Sound Settings** from the main menu to adjust the text size, cannon and other sound effects, and the sea ambience independently. Changes are remembered automatically between launches. You can move through the options with Up and Down, adjust the selected level with Left and Right, or click the left half of a setting row to lower it or the right half to raise it. Choose **Reset defaults** at any time to restore the original levels. Setting a sound level to 0% mutes that category without disabling the rest of the game.

When a story voyage is active, a small course indicator near the top of the screen shows the current target, approximate chart distance, compass direction and a pointer relative to your ship's heading. When there is no story voyage active, it can guide you toward the nearest unfinished harbour job instead. The Captain's Orders help panel has also been made more compact so it covers less of the sailing view; press **F1** to hide or show it.

## Reefs and safe navigation

The chart now marks real coral reefs and rocky shoals with translucent red warning patches. These are navigational hazards, not decoration: sailing across a reef scrapes and damages your hull, and remaining in the shallows can wreck a ship. Give the red areas a wide berth and plan a route around them. Merchantmen, patrols, pirates and your own escorts also try to steer around reefs, although close-quarters fighting or a badly chosen course can still put an NPC vessel in danger. Ships are kept clear of reef patches when they spawn, and harbour approaches and berths remain navigable.

## A world with its own affairs

Explore a vast Caribbean chart with six island regions, 33 ports, remote cays, 20 marked reefs and genuinely long open-water passages. The world chart is now 2.5 times wider and taller than the V25 chart. The four principal multi-port islands now have distinct proportions, from a more compact island chain to broad sprawling landmasses. Secondary islands also vary substantially: some are modest cays, while others are large enough to dominate a local stretch of sea and support their own harbour. The ports are divided among the British Crown, Spanish Crown, French Crown, Merchant League, Pirate Brotherhood and independent settlements. Each harbour displays its faction colours on the world map and its flag. The chart extends beyond its island chains, so you can sail out into the blue rather than run into an invisible edge. Ports have their own character, local rumours and people to meet. Their expanded quays have nine shared alongside berths, and merchantmen or patrol ships may stop briefly in harbour instead of simply sailing through. When you press **E** near a pier, your ship takes the open berth nearest to its current position; no slot belongs permanently to the player. If all nine are occupied, wait offshore and try again after a ship leaves. Their flags and atlas markers show which power controls each harbour: the British Crown, Spanish Crown, French Crown, Merchant League, Pirate Brotherhood or independent communities.

New faction strongholds include Black Flag Anchorage (Pirate Brotherhood), King's Sounding (British Crown), Puerto Escondido (Spanish Crown), La Compagnie (French Crown), St Anne's Exchange (Merchant League), and Free Sailors' Haven (Independent). Each has its own local atmosphere and appears in the chart under its faction colours.

The world is active even when your ship is safely berthed:

- Merchantmen, fishing boats, mail packets, whalers and naval patrols travel between ports.
- Some ships sail alone; others gather into merchant convoys, naval squadrons or pirate bands.
- NPC fleets can find enemies, coordinate attacks, exchange broadsides, lose ships and retreat without the player taking part.
- Coastal batteries defend ports against nearby pirate vessels. Pirate Brotherhood harbours do not automatically fire on ships flying the black flag unless your standing with the Brotherhood has turned hostile.
- Named admirals, pirate captains and merchant commanders develop reputations through victories, losses and retreats. Open the **Admirals' & Captains' Ledger** with **N** to follow their careers.
- The six factions remember your conduct. Harbours and NPC fleets can regard you as friendly, neutral or hostile, and named commanders can develop personal grudges of their own.

## Stories, rumours and people

The campaign includes an introductory voyage, a long original Caribbean storyline, a sequel about a lost expedition and the Drowned Kingdom, and optional side adventures. The stories involve rival powers, pirate captains, naval officers, merchants, scholars and island communities.

Some contracts now involve **multi-port voyages** rather than a single passage. You may be asked to collect passengers or cargo at several intermediate harbours before making the final delivery. The course indicator, gold chart marker and Captain's Log always identify the next required stop. Port calls must be made in order; reaching the final harbour early will not complete the contract. Each completed stop is recorded immediately and is preserved in your save. Examples include *The Bell Family's Passage* (collect relatives in Havana and Tortuga before delivering them to San Telmo) and *The Last Chartmaker's Errand* (restore a chart at Wreckers' Moon and Gallows Key before delivering it to San Aurelio).

Not every conversation is a mission. Depending on the person and place, talking may let you:

- Hear a rumour or learn the name of someone worth seeking out.
- Discover a hidden location, shipwreck, old chart or piece of local history.
- Buy a rare keepsake or unusual piece of equipment.
- Meet a useful contact or uncover a new lead.
- Take a chance on a dubious bargain — some sellers are honest, and some are not.
- Accept a story adventure or ordinary harbour work.

The journal keeps track of important discoveries and leads.

## Make your fortune

There is more than one way to earn a living:

- **Harbour work:** carry cargo, deliver letters, transport passengers or rescue stranded sailors. Several ordinary jobs can be active at once.
- **Side adventures:** take on self-contained stories when you want a change from the main campaign.
- **Treasure hunting:** find bottles and charts, interpret riddles, locate hidden cays and dig up buried chests.
- **Trade and salvage:** buy low, sell where demand is strong, and make use of opportunities you discover.
- **Combat:** defend yourself, fight pirates, or take part in story battles.


## Trading, cargo and the island economies

Every harbour has its own market. Press **Y** while docked to open it. Fifteen commodities are traded, from sugar, rum, coffee and salt fish to ship timber, sailcloth, iron tools, gunpowder, silver and contraband. Prices are not fixed: each port has its own stocks, local production and demand. Stocks are replenished or consumed as the world economy turns, and prices respond when you or other market activity change local supply. A warehouse full of a commodity usually offers a lower price; a scarce good wanted by the settlement can command much more.

Use the market to compare the **buy** and **sell** prices before committing your gold. Select a commodity with Up and Down, choose a quantity with Left and Right (1, 5 or MAX), then press **B** or **Enter** to buy, or **S** to sell. You can also click a commodity and the market buttons. The market's route suggestions compare prices at other ports and estimate a per-unit return after an allowance for voyage distance. They are forecasts, not guarantees: supply, demand and prices continue to change while you sail.

Cargo takes up space in your ship's hold. Different hulls carry different loads: a sloop has a modest hold, a schooner or brigantine carries more, and the frigate trades some cargo room for its fighting role. The **Expanded cargo hold** refit in the shipyard adds 12 units per level, up to three levels. The HUD and market screen show how much space is occupied and how much remains. A shipyard will not let you exchange into a smaller vessel if your cargo will not fit aboard.

Trade also changes the fortunes of the factions. Buying from a harbour brings income to its trade network but can leave its warehouses short. Selling a wanted cargo can ease shortages and improve local prosperity; delivering a scarce shipment can also improve your standing with that faction. Large contraband sales in British, Spanish or French ports attract customs attention. Faction prosperity and shortages are tracked in the diplomacy ledger, and prosperous markets draw more merchant traffic while trade-strained factions see less activity. Your cargo, average purchase costs, realised profits, port markets and faction economies are all retained in your `.tide` save.

## Shipwrecks and salvage

Eighteen explorable shipwrecks lie in the open-water routes between islands. They become visible as you sail close enough to recognise the broken spars and hulls; discovered wrecks are recorded in your journal and marked on the mini-map and world atlas.

Bring your ship close and press **R** to investigate. Most wrecks offer two separate opportunities: recover floating cargo and useful fittings from the surface, then decide whether to send a salvage party into the flooded hull. The safer surface recovery is modest but dependable. Deeper salvage can yield substantially more gold and, occasionally, a rare keepsake or historical discovery.

Wrecks are not all alike. Some are relatively safe coastal craft; others carry unstable gun decks, powder stores, tangled rigging or dangerous currents. A hazardous dive can damage your flagship and reduce the amount of cargo recovered. Each stage can be attempted only once, so choose carefully. Discovery, recovered cargo and rare finds are preserved in your voyage save.

## Sailing and combat

Sailing uses wind, momentum and steering rather than instant movement. Set your sails with **W** and **S**, steer with **A** and **D**, and deploy oars with **O** when the wind is against you.

Cannons fire in broadsides. Hold **Z** to fire the port battery or **X** to fire starboard. The first volley is together; after that, individual guns reload and fire on their own timing. Keep your distance, watch your heading and avoid letting an enemy sit on your unprotected side. Take care with your aim: a cannonball from your flagship or escort fleet that strikes a normally friendly vessel makes that ship—and its surviving squadron, if it has one—hostile to you. It will turn and fire back, and the vessel's faction will remember the attack. Repeated incidents can sour relations across that faction.

## Factions and diplomacy

Open the **Ledger of Flags & Treaties** with **I**. It shows your standing with the British Crown, Spanish Crown, French Crown, Merchant League, Pirate Brotherhood and Independent settlements. Standing ranges from -100 to +100: at +30 or above a faction is **friendly**; from -29 to +29 it is **neutral**; at -30 or below it is **hostile**.

Your actions matter. Completing work and story contracts improves relations with the people who commissioned or received the work. Sinking pirate vessels earns goodwill with several trading and naval powers, but makes the Pirate Brotherhood less forgiving. Firing on a merchantman, patrol ship or pirate vessel damages relations with its faction; sinking it makes matters worse. Named fleet commanders can also remember attacks on their own ships.

Friendly ships will not treat you as an enemy. Neutral traffic generally leaves you alone, while hostile faction vessels may attack when encountered. Neutral and friendly pirate captains do not attack you unless you or your fleet have personally provoked them; a captain you personally attack remembers the insult, even before the whole Brotherhood turns hostile. Harbours belonging to a hostile faction refuse ordinary docking, and their batteries may warn you away if you approach too closely.

Diplomacy offers ways to repair a damaged relationship. Sail close to a hostile harbour and open the diplomacy ledger; select its faction and press **P** to pay reparations for safe conduct (the amount reflects how badly relations have deteriorated). While docked at a faction's harbour, select that faction and press **G** to present a 150-gold gift, improving its standing by 8 points. Safe conduct restores the faction to neutral, but individual captains you personally wronged may still remember you.

Ships collide and push one another apart. A damaged ship can be repaired at a shipyard.

## Your ship and fleet

Visit a shipyard while docked to buy ships, repair your flagship, improve its hull, guns, rigging and rudder, and change its name or colours. Recruit escorts and build a personal fleet. There is no fixed escort-count limit.

Give your escorts orders:

- **F** — Fight
- **H** — Hold fire
- **G** — Gather around the flagship
- **V** — Follow in formation

Your wealth and growing fleet can attract attention. A well-equipped flagship, valuable cargo, gold, relics and numerous escorts may bring more pirate interest.

## Controls

| Key | Action |
|---|---|
| **W / S** | Set sails / reef sails |
| **A / D** | Steer |
| **O** | Deploy / stow oars |
| **Hold Z / X** | Fire port / starboard cannons |
| **E** | Take the nearest available harbour berth / cast off |
| **Q** | Speak with the harbour office while docked |
| **B** | Open the shipyard while docked |
| **Y** | Open the port market while docked |
| **F / H / G / V** | Command your escort fleet |
| **R** | Interact with people, treasure, shipwrecks and salvage sites |
| **T** | View treasure charts |
| **M** | Open the world atlas |
| **C** | Return the camera to your ship |
| **Mouse wheel** | Zoom toward the pointer |
| **Mouse drag** | Pan the camera |
| **J** | Open the captain's journal |
| **N** | Open the Admirals' & Captains' Ledger |
| **I** | Open the faction relations and diplomacy ledger |
| **F1** | Show help |
| **F5** | Save your voyage |
| **Esc / F9** | Open the pause menu |

In harbour conversations, read the available choices carefully. Some are introductions, rumours or purchases rather than jobs. The job board lets you select and accept multiple ordinary jobs.

## Save your voyage

Choose **Load Voyage** from the main menu to browse your named saves. During play, press **F5** to create a save. You can keep multiple voyages, each with its own name.

A save records the last port and the actual quay slot where you docked. You can save while out at sea; when you load that save, your flagship returns safely to that same berth, with your escorts nearby. At each harbour, press **E** while close to the pier and moving slowly; the ship takes the unoccupied slot nearest its current position. No berth is permanently reserved for the player. If every slot is full, circle the harbour and try again after another vessel leaves. Your story progress, ship, gold, fleet, cargo manifest, market prices, faction economies, treasure, jobs, discoveries, faction standings, harbour attitudes and commanders' personal opinions are preserved.

Text size is adjustable, and the interface now scales or fits labels to their panels so enlarged text stays within its allotted space. The game also remembers your text-size preference automatically. Existing V31 and earlier supported `.tide` saves can be loaded; older voyages receive fresh markets and an empty cargo hold. V31 saves that do not record a berth slot load into the traditional centre position, with any NPC occupying it moved to another open slot. The game migrates older ship positions and job destinations to the expanded chart; active multi-port contracts also retain their completed port calls; saves without diplomacy records receive sensible initial faction standings. From the main menu, open **Text & Display Settings** and choose **Smaller text** or **Larger text**. The setting is retained the next time you play.

## A note for captains

Mare Liberum is an adventure about making your own way. Follow the story, chase rumours, build a trading fleet, hunt treasure, or sail beyond the known routes. You are not expected to take every job or fight every battle. Sometimes the most interesting thing in port is simply the person sitting quietly by the window.
