# Version 16 – Saving and Loading

- Added a keyboard-accessible main menu with New Voyage, Load Voyage and Quit.
- Added a pause menu (Esc / F9) with resume, save, load, main menu and quit.
- Added multiple named save slots using readable `.tide` files.
- Save files are indented JSON text with a Tidebound-specific format identifier and named game-state sections.
- Saves remember the most recently docked port. Loading always berths the flagship at that port and arranges escorts in a nearby formation.
- Saves preserve captain funds, ship class/name/livery/upgrades/hull, fleet, campaign progress, treasure discoveries, day jobs, journal, pirate traffic and civilian traffic.
- F5 opens the save-name prompt while sailing or docked.
