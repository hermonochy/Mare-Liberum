import random
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from pathlib import Path

from tidebound.mission_expression import MissionExpression, MissionExpressionError, legacy_condition_to_expression
from tidebound.mission_events import load_mission_events, parse_event_expression
try:
    import pygame
except ModuleNotFoundError:
    sys.modules["pygame"] = types.ModuleType("pygame")
    from tidebound.mixins.mission_events import MissionEventsMixin
    from tidebound.mixins.missions import MissionMixin
    del sys.modules["pygame"]
    sys.modules.pop("tidebound.sail_rendering", None)
else:
    from tidebound.mixins.mission_events import MissionEventsMixin
    from tidebound.mixins.missions import MissionMixin
from tidebound.mission_system import BranchNode, CommandNode, MissionParser, TextNode, load_missions


class MissionExpressionTests(unittest.TestCase):
    def test_nested_and_or_conditions_keep_their_grouping(self):
        expression = legacy_condition_to_expression([
            (8, 'has "First Chart: done"'),
            (8, "or"),
            (12, "random < 20"),
            (12, 'has "Second Chart: done"'),
        ])
        parsed = MissionExpression(expression)
        result = parsed.evaluate(
            {"random": 10},
            {"mission": lambda name: "done" if name == "Second Chart" else "available"},
        )
        self.assertTrue(result)

    def test_expressions_support_sea_state_and_named_world_queries(self):
        expression = MissionExpression(
            "at_sea and speed > 10 and near_island('Saint Elmo Cay') and flag('charted')"
        )
        self.assertTrue(expression.evaluate(
            {"at_sea": True, "speed": 22},
            {"near_island": lambda name: name == "Saint Elmo Cay", "flag": lambda name: name == "charted"},
        ))

    def test_unsafe_python_operations_are_rejected(self):
        with self.assertRaises(MissionExpressionError):
            MissionExpression("__import__('os').system('echo unsafe')")

    def test_distance_condition_converts_to_port_distance_function(self):
        expression = legacy_condition_to_expression([(8, 'distance "Port Royal" > 900')])
        parsed = MissionExpression(expression)
        self.assertTrue(parsed.evaluate({}, {"distance_to_port": lambda name: 1200 if name == "Port Royal" else 0}))


class MissionLanguageTests(unittest.TestCase):
    def test_bare_repeat_keyword_is_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repeat.mission"
            path.write_text('mission "Repeatable Test"\n    repeat\n', encoding="utf-8")
            mission = MissionParser(path).parse()
        self.assertTrue(mission.repeatable)

    def test_parser_reads_lifecycle_location_and_unusual_objectives(self):
        text = '''mission "Script Test"
    category "side"
    offer_at "near_wreck"
    offer_expression "at_sea and near_wreck('wreck_01')"
    objective salvage "wreck_01"
    deadline 120
    repeatable true
    cooldown 45
    max_triggers 3
    priority 8
    stopover "Havana"
    to fail
        has "wanted"
    to start
        has "start_signal"
    to complete
        has "wreck_paid"
    to show
        has "chart_visible"
    to display
        has "chart_displayed"
    to accept
        has "accept_permission"
    on offer
        `A test.`
'''
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "script_test.mission"
            path.write_text(text, encoding="utf-8")
            mission = MissionParser(path).parse()
        self.assertEqual(mission.offer_at, "near_wreck")
        self.assertEqual(mission.objective_type, "salvage")
        self.assertEqual(mission.objective_target, "wreck_01")
        self.assertEqual(mission.deadline_seconds, 120)
        self.assertTrue(mission.repeatable)
        self.assertEqual(mission.cooldown_seconds, 45)
        self.assertEqual(mission.max_triggers, 3)
        self.assertEqual(mission.priority, 8)
        self.assertEqual(mission.waypoints[0].port, "Havana")
        self.assertTrue(mission.fail_expression)
        self.assertTrue(mission.start_expression)
        self.assertTrue(mission.complete_expression)
        self.assertTrue(mission.show_expression)
        self.assertTrue(mission.display_expression)
        self.assertTrue(mission.accept_expression)

    def test_visibility_expressions_are_evaluated_separately(self):
        mission = SimpleNamespace(show_expression="flag('visible')", display_expression="flag('listed')")
        game = SimpleNamespace(evaluate_mission_script_expression=lambda expression: expression == "flag('visible')")
        self.assertFalse(MissionMixin.mission_is_visible(game, mission))
        mission.display_expression = ""
        self.assertTrue(MissionMixin.mission_is_visible(game, mission))

    def test_acceptance_condition_blocks_contract_before_state_changes(self):
        mission = SimpleNamespace(accept_expression="flag('permission')")
        game = SimpleNamespace(
            evaluate_mission_script_expression=lambda expression: False,
            toast_message=lambda *args: None,
        )
        self.assertFalse(MissionMixin.accept_mission(game, mission))

    def test_branch_and_action_blocks_are_preserved_in_conversation_trees(self):
        text = '''mission "Branch and Action"
    on offer
        conversation
            branch charted
                has "chart_found"
            `You have not found the chart yet.`
            label charted
            `The chart is safely in your hands.`
            action
                set "scene_complete" true
                set "charts_recovered" ++
                clear "old_warning"
                log "The captain secured the chart."
    on enter
        `The harbour watch recognises your ship.`
    on depart
        `The harbour falls away astern.`
    on stopover
        `The required harbour call is complete.`
    on kill
        `The target has gone beneath the waves.`
    on provoke
        `The merchant convoy turns against you.`
    on timeup
        `The agreed hour has passed.`
'''
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "branch_action.mission"
            path.write_text(text, encoding="utf-8")
            mission = MissionParser(path).parse()
        nodes = mission.sections["offer"]
        self.assertIsInstance(nodes[0], BranchNode)
        self.assertEqual(nodes[0].label, "charted")
        self.assertIn("flag('chart_found')", nodes[0].expression)
        self.assertTrue(any(isinstance(node, CommandNode) and node.command == "set_flag" for node in nodes))
        self.assertTrue(any(isinstance(node, CommandNode) and node.command == "increment_flag" for node in nodes))
        self.assertTrue(any(isinstance(node, CommandNode) and node.command == "clear_flag" for node in nodes))
        self.assertTrue(any(isinstance(node, CommandNode) and node.command == "log" for node in nodes))
        self.assertIsInstance(mission.sections["enter"][0], TextNode)
        self.assertIsInstance(mission.sections["depart"][0], TextNode)
        self.assertIn("stopover", mission.sections)
        self.assertIn("kill", mission.sections)
        self.assertIn("provoke", mission.sections)
        self.assertIn("timeup", mission.sections)

    def test_offer_or_block_is_not_flattened_into_hard_requirements(self):
        text = '''mission "Either Route"
    to offer
        has "First Route: done"
        or
            random < 10
            has "Second Route: done"
'''
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "either_route.mission"
            path.write_text(text, encoding="utf-8")
            mission = MissionParser(path).parse()
        self.assertEqual(mission.requires_done, [])
        self.assertIn("or", mission.offer_expression)

    def test_event_actions_include_fleets_islands_and_weather(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "events.mission"
            path.write_text('''mission "Event Actions"
    event at_sea and speed > 10
    event_action spawn_fleet "The Shoal Dogs" "Captain Vale" 2 3 6 0.8 900 "Sloop" "Brig"
    event_action spawn_island "New Cay" 1500 800 300
    event_action set_wind 210 0.45 180
    event_action reveal_wreck "black_gull"
''', encoding="utf-8")
            mission = MissionParser(path).parse()
        actions = mission.event_config["actions"]
        self.assertEqual([item["type"] for item in actions], ["spawn_fleet", "spawn_island", "set_wind", "reveal_wreck"])
        self.assertEqual(actions[0]["ship_types"], ["Sloop", "Brig"])
        self.assertEqual(actions[2]["duration"], 180)

    def test_event_expression_supports_maritime_locations(self):
        for expression in (
            'near_island("Saint Elmo Cay")',
            'near_wreck("black_gull")',
            'port_faction("Port Royal") == "Independent"',
            'distance_to_port("Port Royal") > 800',
            'ships_nearby(600) > 0',
        ):
            self.assertIsInstance(parse_event_expression(expression), dict)

    def test_event_island_spawning_avoids_overlaps_and_is_recorded(self):
        game = SimpleNamespace(
            ship_x=5000.0,
            ship_y=5000.0,
            rng=random.Random(11),
            ports=[],
            land=[],
            treasure_sites=[],
            reefs=[],
            dynamic_islands=[],
            world_flags={},
            journal=[],
        )
        game.reef_clear_at = lambda x, y, clearance=75.0: True
        game.set_world_flag = lambda key, value=True: game.world_flags.__setitem__(key, value)
        game.add_journal = lambda value: game.journal.append(value)
        game.toast_message = lambda *args: None
        first = {"name": "New Cay", "offset_x": 1800, "offset_y": 900, "radius": 360}
        second = {"name": "Other Cay", "offset_x": 1800, "offset_y": 900, "radius": 360}
        self.assertTrue(MissionEventsMixin.spawn_event_island(game, first, "test_event", 1, 0))
        self.assertFalse(MissionEventsMixin.spawn_event_island(game, first, "test_event", 2, 0))
        self.assertFalse(MissionEventsMixin.spawn_event_island(game, second, "test_event", 2, 0))
        self.assertEqual(len(game.dynamic_islands), 1)
        self.assertTrue(game.world_flags["island_discovered:New Cay"])

    def test_active_mission_encounter_hook_triggers_once_per_vessel(self):
        mission = SimpleNamespace(mission_id="watch_the_channel", sections={"encounter": [TextNode("A vessel draws close.")]})
        vessel = SimpleNamespace(name="The Grey Gull", x=520.0, y=500.0, hull=10, dead=False)
        game = SimpleNamespace(
            conversation=None,
            ship_x=500.0,
            ship_y=500.0,
            traffic_ships=[vessel],
            pirates=[],
            world_flags={},
            encounters=[],
        )
        game.active_mission = lambda: mission
        game.set_world_flag = lambda key, value=True: game.world_flags.__setitem__(key, value)
        game.start_conversation = lambda selected, section: game.encounters.append((selected.mission_id, section))
        MissionEventsMixin.update_active_mission_encounters(game)
        MissionEventsMixin.update_active_mission_encounters(game)
        self.assertEqual(game.encounters, [("watch_the_channel", "encounter")])

    def test_aborting_active_mission_cleans_up_and_marks_failed(self):
        mission = SimpleNamespace(mission_id="abandon_me", name="Abandon Me", sections={"abort": [TextNode("The contract is abandoned.")]})
        target = SimpleNamespace(mission_id="abandon_me", objective_target=True)
        unrelated = SimpleNamespace(mission_id="other_event", objective_target=True)
        game = SimpleNamespace(
            active_mission_id="abandon_me",
            mission_states={"abandon_me": "active"},
            mission_kills=2,
            mission_waypoint_index=1,
            mission_returning=True,
            mission_completion_started=False,
            mission_fleet_spawned=True,
            mission_deadline_remaining=45.0,
            pirates=[target, unrelated],
            journal=[],
            notifications=[],
        )
        game.active_mission = lambda: mission
        game.add_journal = lambda value: game.journal.append(value)
        game.toast_message = lambda value, *args: game.notifications.append(value)
        result = MissionMixin.abort_active_mission(game, start_abort_dialogue=False)
        self.assertIs(result, mission)
        self.assertEqual(game.mission_states["abandon_me"], "failed")
        self.assertIsNone(game.active_mission_id)
        self.assertEqual(game.mission_deadline_remaining, 0.0)
        self.assertEqual(game.pirates, [unrelated])
        self.assertIn("Abandoned: Abandon Me", game.journal[0])

    def test_project_mission_ids_are_unique_and_stable_for_duplicate_titles(self):
        mission_dir = Path(__file__).resolve().parents[1] / "missions"
        missions = load_missions(mission_dir)
        ids = [mission.mission_id for mission in missions]
        self.assertEqual(len(ids), len(set(ids)))
        matching = [mission for mission in missions if mission.title == "The False Beacon"]
        self.assertEqual(len(matching), 2)
        self.assertEqual(matching[0].mission_id, "the_false_beacon")
        self.assertEqual(matching[1].mission_id, "the_false_beacon_67")

    def test_project_missions_and_events_load(self):
        mission_dir = Path(__file__).resolve().parents[1] / "missions"
        missions = load_missions(mission_dir)
        events = load_mission_events(mission_dir)
        self.assertGreaterEqual(len(missions), 85)
        self.assertGreaterEqual(len(events), 4)
        self.assertTrue(any(item.ambient and item.offer_at == "sea" for item in missions))
        self.assertTrue(any(item.objective_type == "salvage" for item in missions))
        self.assertTrue(any(action["type"] == "spawn_island" for event in events for action in event["actions"]))
        self.assertTrue(any(action["type"] == "spawn_fleet" for event in events for action in event["actions"]))


if __name__ == "__main__":
    unittest.main()
