# Tidebound V10 — Clearer Missions and Reliable Battle Fleets

This update fixes mission guidance, completion feedback, campaign routing, and scripted combat encounters.

## Clear objectives and navigation

- The active voyage card now states exactly what to do: sail to a named destination or named battle waters, sink a visible number of mission targets, or return to port for the debrief.
- The sea chart shows a gold route from the player to the current mission waypoint.
- A gold marker is drawn in the world at the mission port or battle area; named mission ships are highlighted on the chart and with a ring in the world.
- The captain's log and harbourmaster repeat the same current instruction.

## Clear completion

- Combat objectives no longer silently finish as soon as the last ship sinks.
- After all named targets are sunk, the HUD changes to **RETURN TO [PORT]**.
- Docking at that port triggers a debrief conversation, then the reward and a visible **VOYAGE COMPLETE** banner.
- Completion is recorded in the captain's log, with the reward shown on screen.

## Scripted mission fleets

Combat missions now define their own target ships with `battlefield` and `enemy` entries in their `.mission` files. Accepting the mission spawns those named ships at safe sea positions around the marked area. They are highlighted on the mini-map, actively pursue the player, and only those mission-specific targets count toward that mission's kill objective. Ordinary roaming pirates no longer accidentally satisfy a story battle objective. Ambient reinforcements are paused during authored combat missions so the named fleet remains the focus.

## Campaign route flow

Every authored chapter now hands off at a port that is the next chapter's source. The four combat missions have a clear middle leg between their start and return port:

- Clear the Cutlass Shoals: Havana → Cutlass Shoals → Havana.
- The Gallows Tide: Tortuga → the prison flotilla south of Tortuga → Tortuga.
- The Black Fleet Rises: Port Royal → the Outer Cays → Port Royal.
- The Last Broadside: Port Royal → Dead Man's Cay → Tortuga.

This avoids the feeling that a mission simply starts and ends at the same location without an intermediate objective.

## Mission file additions

Combat mission files can now contain:

```text
    objective kills 2
    battlefield "Cutlass Shoals" 1860 760
    enemy "The Red Gull"
    enemy "The Sea Viper"
```

The `battlefield` line contains a readable area name and world coordinates. Each `enemy` line adds one named mission target. The number of enemy entries should match `objective kills N`.
