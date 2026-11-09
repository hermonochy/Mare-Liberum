Mare Liberum voyage saves are stored here. Each .tide file is a human-readable JSON document recording the last safe harbour, voyage progress, fleet state, faction standings, port attitudes and personal relations with named NPC commanders.

Version 8 is the current save format. Existing V25 version 6 saves and earlier supported TIDEBOUND_VOYAGE saves can be loaded and migrated automatically. The V26 migration scales saved NPC positions, velocities and harbour-job targets to the expanded chart, then reseats saved harbour traffic around the new nine-berth quays.

Version 27 adds static reefs to the world. V26 saves remain compatible; any saved NPC found inside a newly charted reef is automatically repositioned into nearby safe water on loading. The reef positions are generated deterministically and are not stored separately in each save.

Version 28 adds discovered shipwrecks, surface cargo recovery, deep-salvage attempts and rare-discovery flags to each .tide file. Existing V27 version 7 saves and earlier supported saves load normally; wreck sites begin undiscovered and unsalvaged in those older saves.
