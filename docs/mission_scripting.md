# Mare Liberum mission and event scripting

Mission files remain plain-text `.mission` files in `missions/`. The existing mission files and JSON save format remain the source of truth. New mission features extend that format; they do not require a second mission or save format.

This is a maritime adaptation of the mission-system patterns in Endless Sky. Keywords that depend on a star-system galaxy, planet economy, equipment inventory, or boarding simulation are not copied literally when Mare Liberum has no equivalent gameplay object.

## Mission declaration and fields

```text
mission "The Missing Soundings"
    name "The Missing Soundings"
    category "side"
    description "Find the surveyor's markers around Saint Elmo Cay and report back."
    source "Port Royal"
    destination "Port Royal"
    reward 260
    offer_at "anywhere"
    offer_expression "island_known('Saint Elmo Cay')"
    objective explore "Saint Elmo Cay"
    deadline 1800
    repeatable false
```

Supported top-level fields include:

- `name`, `description`, `category`, `source`, `destination`, `reward`, `speaker`, and section-specific `speaker offer`, `speaker complete`, etc.
- `offer_at`, `offer_expression`, `to offer`, `to show`, `to display`, `to accept`, `to start`, `to fail`, and `to complete`.
- `objective`, `enemy`, `battlefield`, `waypoint`, and `stopover`.
- `ambient`, `repeatable` / `repeat`, `cooldown`, `max_triggers`, `deadline`, `priority`, and `kind`.
- Existing presentation/directive tokens such as `landing`, `minor`, `invisible`, `non-blocking`, `job`, and `passengers` are parsed and retained. A retained directive is not automatically a promise that every Endless Sky meaning is implemented; see the limitations section.

## Offers away from a harbour

`offer_at` controls where an offer or ambient scene is eligible to appear:

| Value | Meaning |
| --- | --- |
| `port` | While docked at the mission's source port (the default). |
| `sea` | While sailing, not docked. |
| `anywhere` | At sea or in port. |
| `near:Port Name` | Within the local approach radius of a named port. |
| `near_ship` | Near a living traffic or pirate vessel. |
| `near_wreck` | Near a shipwreck that has not been fully salvaged. |
| `region:Region Name` | While the player is in the named sea region. |

Use `offer_expression` for a further condition. `ambient true` marks a scene as ambient rather than a regular commission. Ambient scenes can occur independently of the harbourmaster's special-job list and can run while another mission is active. Autonomous non-ambient offers use `offer_at` but are held while another mission is active.

```text
mission "A Sailor's Warning"
    category "ambient"
    ambient true
    offer_at "sea"
    repeatable true
    cooldown 300
    max_triggers 3
    priority 5
    offer_expression "at_sea and speed > 5 and ships_nearby(900) > 0"
    on offer
        conversation
            `A boat draws close enough for its crew to hail you. The helmsman has a warning about the waters ahead.`
            choice
                `Ask what they have seen.`
                `Thank them and keep your course.`
                    close
```

## Conditions and expressions

Mission conditions use a restricted expression language. Python code, attribute access, imports, and arbitrary function calls are not permitted.

Basic values include:

`gold`, `time`, `world_time`, `at_sea`, `docked`, `docked_port`, `region`, `ship_class`, `hull`, `hull_percent`, `wind_strength`, `wind_angle`, `sail_setting`, `sail_percent`, `oars_deployed`, `speed`, `fleet`, `escorts`, `fleet_power`, `jobs`, `relics`, `unique_items`, `cargo_load`, `cargo_free_space`, and `nearby_ships`.

Functions include:

- `flag('flag_name')`, `has_flag('flag_name')`
- `mission('Mission Name')`, `has_mission('Mission Name')`, `event('event_id')`
- `standing('Faction')`, `visited('Port Name')`, `visits('Port Name')`
- `upgrade('upgrade_name')`, `cargo('cargo_id')`
- `near_port('Port Name')`, `distance_to_port('Port Name')`
- `near_island('Island Name')`, `island_known('Island Name')`
- `near_wreck('Wreck ID or name')`, `wreck_known('Wreck ID or name')`
- `ships_nearby(radius)` or `ships_nearby(radius, 'Faction')`

Use `and`, `or`, `not`, parentheses, and comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`). For compatibility, indented condition blocks using `has`, `not`, `random`, and `distance` are also understood.

```text
to offer
    has "The First Chart: done"
    or
        at_sea
        and distance "Port Royal" > 1200
```

`to show` and `to display` are visibility filters for mission lists and ambient scenes. `to accept` is checked again when the player accepts, so an offer can be visible before the player has met its final condition. `to fail` is checked while a mission is active. `to complete` is checked while it is active and begins the mission's `on complete` conversation when true. `to start` automatically accepts an available mission when its expression becomes true. `to offer` controls eligibility in addition to the mission's location.

## Objectives, routes and deadlines

Existing port calls, kill objectives and ordered waypoint routes continue to work. The additional maritime objectives are:

- `objective explore "Island Name"` — reach the island's charted centre.
- `objective discover_wreck "wreck_id or name"` — discover the named wreck.
- `objective salvage "wreck_id or name"` — complete surface and deep salvage of the named wreck.
- `objective visit_port "Port Name"` — visit the named port.
- `objective event "event_id"` — complete the named world event.

`waypoint "Port Name" "purpose text"` adds an ordered stop. `stopover "Port Name"` adds an ordered required call without a separate purpose string. `deadline 900` gives an active mission a 900-second in-world deadline. The remaining deadline is saved with the existing game save.

## Conversation language

The conversation language supports `conversation`, `choice`, `label`, `goto`, `branch`, and `action` blocks. `branch label` evaluates the indented conditions and jumps to the label when they are true. `action` runs its nested commands in sequence.

```text
on offer
    conversation
        branch already_charted
            has "island_discovered: Saint Elmo Cay"
        `The chartmaker asks whether you have seen the island.`
        choice
            `I have.`
                goto already_charted
            `Not yet.`
        label already_charted
        `The chartmaker nods and waits for your report.`
        action
            set_flag "chartmaker_met" true
            log "Spoke with the chartmaker about Saint Elmo Cay."
```

Conversation commands include `accept`, `decline`, `defer`, `close`, `launch`, `depart`, `flee`, `log`, `set_flag`, `clear_flag`, and the Endless Sky-style `set` / `clear` aliases. `set "flag" ++` and `set "flag" --` increment or decrement a numeric world flag. Dialogue `action` blocks can group these commands in sequence. They also include `give_gold`, `adjust_relation`, `schedule_event`, `reveal_island`, `reveal_wreck`, `set_wind`, and `set_sea_state`. Harbour and service navigation commands include `offers`, `intro_mission`, `mission_offer`, `day_jobs`, `accept_day_job`, `decline_day_job`, `news`, `shipyard`, and `curiosities`.

Mission sections `on offer`, `on accept`, `on decline`, `on defer`, `on abort`, `on visit`, `on waypoint_N`, `on waypoint`, `on stopover`, `on enter`, `on depart`, `on leave`, `on kill`, `on provoke`, `on encounter`, `on timeup`, `on complete`, and `on fail` can contain dialogue and actions. `on enter` runs when the player makes port; `on depart` (or `on leave` as a fallback) runs when casting off; `on stopover` runs after a required route stop; `on kill` runs after a mission target is sunk; `on provoke` runs when player fire turns a previously neutral vessel or pirate into a hostile; `on encounter` runs the first time a living traffic or pirate vessel comes within encounter range during the active mission; and `on timeup` runs instead of `on fail` when a deadline expires (falling back to `on fail` if absent).

## World events

An event is a `.mission` file with an `event` trigger expression. It is loaded by the same mission loader but is not offered as a contract.

```text
mission "Squall off the Banks"
    event at_sea and speed > 10 and wind_strength < 0.3
    event_delay 30 75
    event_pause_while_docked true
    event_max_triggers 1
    event_action set_sea_state rough 180
    event_action toast "A squall is building to windward." 5
    event_action journal "A sudden squall crossed the ship's course."
```

Event configuration fields include `event_delay`, `event_cancel_if`, `event_pause_while_docked`, `event_repeatable`, `event_max_triggers`, `event_cooldown`, `event_faction`, `event_attitude`, `event_ship_types`, `event_ship_name`, `event_announcement`, `event_journal_entry`, `event_complete_flag`, `event_complete_text`, and `event_repelled_text`.

Available `event_action` operations:

- `spawn_fleet "Fleet Name" "Commander" min max hard_max strength_ratio distance "Sloop" "Brig"`
- `spawn_island "Island Name" offset_x offset_y radius`
- `reveal_island "Island Name"`, `reveal_wreck "wreck_id or name"`
- `set_port_faction "Port Name" "Faction"`
- `set_wind angle strength duration`, `set_sea_state calm|swell|rough|storm duration`
- `toast`, `journal`, `give_gold`, `set_gold`, `set_flag`, `add_flag`, `remove_flag`, `adjust_relation`, `set_mission_state`
- `schedule_event`, `enable_event`, `disable_event`, `retreat_fleet`, `add_cargo`, and `remove_cargo`

The event engine stores trigger counts, cooldowns, delayed activations, random rolls, active fleet identities, and completion state in the existing save data. The current world model supports spawned island landforms and spawned ship fleets. Sea-state changes currently act through wind strength and the sea-state flag; they do not yet create wave physics or storm damage.

## Current limits and non-applicable Endless Sky systems

The reference archive contains many systems that have no direct gameplay counterpart in Mare Liberum. The current engine does not claim support for Endless Sky's full star-system/hyperlane galaxy, planet orbit/economy model, ship outfit inventory and outfit scanning, asteroid/minable resource simulation, wormholes, or full ship boarding and capture. The parser may retain some familiar presentation directives, but these systems need dedicated game mechanics before their original keywords can be considered implemented.

Likewise, NPC fleets are maritime vessel groups, not a general-purpose clone of every Endless Sky NPC personality, escort, boarding, or fleet-command directive. The event and ambient systems are a foundation for adding those behaviours incrementally.

## Authoring and validation

- Keep mission and event scripts in `missions/*.mission`.
- Use descriptive, unique mission titles and event names.
- Prefer `offer_expression` and the documented maritime functions for location-aware logic.
- Use `event` plus `event_action` for world changes that do not need a conversation.
- Use `ambient true` for incidental scenes that are not jobs.
- Run `python -m unittest discover -s tests -v` and `python -m compileall -q main.py tidebound tests` after editing scripts or parser code.
