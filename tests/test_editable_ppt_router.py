from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
ROUTER_PATH = REPO / ".agents" / "skills" / "editable-ppt-pipeline" / "scripts" / "editable_ppt.py"
SPEC = importlib.util.spec_from_file_location("editable_ppt_router", ROUTER_PATH)
assert SPEC and SPEC.loader
ROUTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROUTER)


class EditablePptRouterE2E(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name)
        self.source = self.workspace / "source.png"
        self.source.write_bytes(b"fixture")
        self.editable = self.workspace / "reconstructed_editable.pptx"
        self.editable.write_bytes(b"fixture")
        self.paper = self.workspace / "paper.pdf"
        self.paper.write_bytes(b"fixture")
        self.plan_file = self.workspace / "revision_plan.json"
        self.plan_file.write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_router(self, *arguments: str):
        return ROUTER.dispatch(["--workspace", str(self.workspace), *arguments])

    def start_project(self) -> str:
        plan, code = self.run_router("--source", str(self.source), "--message", "做成可编辑的")
        self.assertEqual(code, 0)
        self.assertEqual(plan["stages"], ["editable-ppt-reconstruct"])
        self.run_router("--record-reconstruction", str(self.editable))
        return plan["project_id"]

    def record_review_and_versions(self) -> str:
        project_id = self.start_project()
        self.run_router("--record-review", str(self.plan_file))
        self.run_router(
            "--record-version", f"A={self.workspace / 'A.pptx'}",
            "--record-version", f"B={self.workspace / 'B.pptx'}",
            "--record-version", f"C={self.workspace / 'C.pptx'}",
        )
        return project_id

    def load_state(self, project_id: str) -> dict:
        path = self.workspace / "projects" / project_id / "project_state.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_1_first_single_image_asks_once_then_choice_1_runs(self) -> None:
        first, code = self.run_router("--source", str(self.source))
        self.assertEqual(code, 0)
        self.assertEqual(first["status"], "needs_single_choice")
        self.assertIn("1）", first["question"])
        self.assertIn("2）", first["question"])
        self.assertIn("3）", first["question"])
        self.assertNotIn("4）", first["question"])
        self.assertEqual(first["question"].count("？"), 1)

        second, code = self.run_router("--message", "1")
        self.assertEqual(code, 0)
        self.assertEqual(second["stages"], ["editable-ppt-reconstruct"])
        self.assertTrue(second["comparison_required"])
        self.assertEqual(second["question"], "")

        _, code = self.run_router(
            "--record-reconstruction", str(self.editable),
            "--comparison", str(self.workspace / "before_after.png"),
        )
        self.assertEqual(code, 0)
        state = self.load_state(first["project_id"])
        self.assertEqual(state["active_baseline"], str(self.editable.resolve()))
        self.assertEqual(len(state["comparison_outputs"]), 1)

    def test_2_paper_upload_is_auto_associated_after_reconstruction(self) -> None:
        project_id = self.start_project()
        plan, code = self.run_router("--literature", str(self.paper))
        self.assertEqual(code, 0)
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["stages"], ["editable-ppt-content-review"])
        self.assertEqual(plan["question"], "")
        state = self.load_state(project_id)
        self.assertIn(str(self.paper.resolve()), state["literature_files"])
        self.assertEqual(plan["active_deck"], str(self.editable.resolve()))

    def test_3_feedback_merges_with_review_and_routes_to_three_versions(self) -> None:
        project_id = self.start_project()
        self.run_router("--record-review", str(self.plan_file))
        message = "第二页压缩文字，第三页改成机制流程，第五页加入论文中的主要数据，整体保持原来的配色。"
        plan, code = self.run_router("--message", message)
        self.assertEqual(code, 0)
        self.assertEqual(plan["stages"], ["editable-ppt-iterate"])
        self.assertTrue(plan["comparison_required"])
        self.assertEqual(plan["focus_slides"], [2, 3, 5])
        state = self.load_state(project_id)
        self.assertEqual(state["latest_revision_plan"], str(self.plan_file.resolve()))
        self.assertTrue(any(item["text"] == message for item in state["user_feedback_history"]))

    def test_4_all_three_rejected_starts_new_round_without_question(self) -> None:
        project_id = self.record_review_and_versions()
        plan, code = self.run_router("--message", "三个都不满意，再来三个。")
        self.assertEqual(code, 0)
        self.assertEqual(plan["stages"], ["editable-ppt-iterate"])
        self.assertEqual(plan["question"], "")
        self.assertIn("started_next_round_without_question", plan["events"])
        state = self.load_state(project_id)
        self.assertEqual(len(state["rejected_versions"]), 3)
        self.assertEqual(state["iteration_round"], 2)
        latest = state["round_history"][-1]
        self.assertTrue(latest["must_avoid_prior_design_signatures"])
        self.assertTrue(latest["color_only_change_forbidden"])
        self.assertGreaterEqual(latest["minimum_strategy_dimensions_changed"], 4)

    def test_5_reasoned_rejection_becomes_next_round_constraints(self) -> None:
        project_id = self.record_review_and_versions()
        message = "A 太拥挤，B 的逻辑可以，但图太小，C 改得太激进。再来三个。"
        plan, code = self.run_router("--message", message)
        self.assertEqual(code, 0)
        self.assertEqual(plan["question"], "")
        state = self.load_state(project_id)
        actions = {item["action"] for item in state["round_history"][-1]["next_round_constraints"]}
        self.assertEqual(
            actions,
            {"reduce_density", "preserve_B_narrative_logic", "enlarge_core_visuals", "limit_structural_change"},
        )

    def test_6_select_B_makes_B_active_and_focuses_slide_4(self) -> None:
        project_id = self.record_review_and_versions()
        plan, code = self.run_router("--message", "用 B 继续，第四页重新做。")
        self.assertEqual(code, 0)
        expected = str((self.workspace / "B.pptx").resolve())
        self.assertEqual(plan["active_deck"], expected)
        self.assertEqual(plan["comparison_baseline"], expected)
        self.assertEqual(plan["focus_slides"], [4])
        self.assertEqual(plan["stages"], ["editable-ppt-iterate"])
        state = self.load_state(project_id)
        self.assertEqual(state["active_baseline"], expected)

    def test_7_reenter_workspace_reads_active_project_and_continues(self) -> None:
        project_id = self.record_review_and_versions()
        plan, code = self.run_router("--message", "继续上次那个 PPT，再来三个。")
        self.assertEqual(code, 0)
        self.assertEqual(plan["project_id"], project_id)
        self.assertEqual(plan["stages"], ["editable-ppt-iterate"])
        self.assertEqual(plan["question"], "")
        self.assertEqual(plan["missing"], [])
        state = self.load_state(project_id)
        self.assertEqual(state["iteration_round"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
