"""Run with .venv/Scripts/python.exe -m unittest -v.

The exhaustive oracle deliberately does not use the solver, its level bound,
its ranking helper, or its verifier to decide the expected optimum.
"""

import _thread
from contextlib import redirect_stdout, redirect_stderr
import io
from itertools import combinations, product
from pathlib import Path
import subprocess
import sys
from threading import Event, Timer
import unittest
from unittest.mock import patch

from ortools.sat.python import cp_model

import artifact_engine as engine
import calculator


# Public source growth table, transcribed as fixed fixtures rather than
# recomputing the very formula under test.
AP_TABLE = (
    1, 2, 3, 4, 6, 7, 8, 9, 10, 12,
    13, 14, 15, 16, 18, 19, 20, 21, 22, 24,
    25, 26, 27, 28, 30, 31, 32, 33, 34, 36,
    37, 38, 39, 40, 42, 43, 44, 45, 46, 48,
    49, 50, 51, 52, 54, 55, 56, 57, 58, 60,
    61, 62, 63, 64, 66, 67, 68, 69, 70, 72,
)
COUNT_TABLE = (3,) * 9 + (4,) * 10 + (5,) * 10 + (6,) * 10 + (7,) * 10 + (8,) * 10 + (9,)


def exhaustive_three():
    """Enumerate all 5^3 * C(12,3) labeled level/option assignments."""
    best_by_cost = {}
    for levels in product(range(1, 6), repeat=3):
        cost = sum((0, 1, 3, 5, 8)[value - 1] for value in levels)
        for extra in combinations(range(12), 3):
            totals = [0] * 12
            for value, options in zip(levels, ((0, 1, 2), (3, 4, 5), extra)):
                for option in options:
                    totals[option] += value
            totals = tuple(min(value, 10) for value in totals)
            if totals[0] != 10:
                continue
            key = (sum(totals), *totals[1:], -cost)
            best_by_cost[cost] = max(best_by_cost.get(cost, key), key)
    return {
        budget: max((rank for cost, rank in best_by_cost.items() if cost <= budget), default=None)
        for budget in range(25)
    }


class EngineTests(unittest.TestCase):
    def test_all_60_resource_rows(self):
        for level, expected in enumerate(zip(AP_TABLE, COUNT_TABLE), start=1):
            with self.subTest(level=level):
                self.assertEqual(engine.resources(level), expected)

    def test_invalid_inputs(self):
        for value in (0, 61, -1, 1.2, "20", True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                engine.resources(value)
        for budget, count in ((-1, 5), (1.5, 5), (True, 5), (24, 2), (24, 10), (24, 5.0)):
            with self.subTest(budget=budget, count=count), self.assertRaises(ValueError):
                engine.solve(budget, count)

    def test_exhaustive_three_all_budgets(self):
        for budget, expected in exhaustive_three().items():
            with self.subTest(budget=budget):
                actual = engine.solve(budget, 3)
                if expected is None:
                    self.assertEqual(actual.status, "infeasible")
                else:
                    self.assertEqual(actual.status, "optimal")
                    self.assertEqual(actual.metrics.rank, expected)

    def test_original_example_and_priority(self):
        original = (
            engine.Crystal(4, (0, 1, 2)), engine.Crystal(5, (3, 4, 5)),
            engine.Crystal(4, (1, 2, 6)), engine.Crystal(3, (0, 3, 4)),
            engine.Crystal(3, (0, 5, 6)),
        )
        metrics = engine.verify(original, 24, 5)
        self.assertEqual((metrics.used_ap, metrics.level_sum, metrics.total), (24, 19, 57))
        optimized = engine.solve_level(20)
        self.assertEqual(optimized.metrics.total, 57)
        self.assertEqual(optimized.metrics.effective, (10, 10, 10, 9, 9, 9, 0, 0, 0, 0, 0, 0))
        self.assertGreater(optimized.metrics.rank, metrics.rank)

    def test_total_beats_priority_and_overflow_is_excluded(self):
        r = engine.solve_level(21)
        self.assertEqual((r.budget, r.count), (25, 5))
        self.assertEqual(r.metrics.total, 58)
        self.assertEqual(r.metrics.effective, (10, 8, 8, 8, 8, 8, 8, 0, 0, 0, 0, 0))
        self.assertEqual((r.metrics.level_sum, r.metrics.raw[0], sum(r.metrics.overflow)), (20, 12, 2))

    def test_level_60_minimizes_ap_after_full_effects(self):
        r = engine.solve_level(60)
        self.assertEqual((r.budget, r.count), (72, 9))
        self.assertEqual(r.metrics.effective, (10,) * 12)
        self.assertEqual(r.metrics.used_ap, 59)
        self.assertLess(engine.solve(58, 9).metrics.total, 120)
        self.assertEqual(engine.verify(r.crystals, 72, 9), r.metrics)

    def test_group_expansion_degree_sequences(self):
        # Exhaust every valid degree vector over six columns, 1~4 rows.
        # This checks reconstruction beyond the one-free-crystal oracle.
        for size in range(1, 5):
            for degrees in product(range(size + 1), repeat=6):
                if sum(degrees) != 3 * size:
                    continue
                expected = [*degrees, *([0] * 6)]
                rows = engine._expand_group(4, size, expected)
                self.assertEqual(len(rows), size)
                actual = [0] * 12
                for row in rows:
                    self.assertEqual(len(set(row.options)), 3)
                    for option in row.options:
                        actual[option] += 1
                self.assertEqual(actual, expected)

    def test_verifier_rejects_bad_results(self):
        good = (engine.Crystal(5, (0, 1, 2)), engine.Crystal(1, (3, 4, 5)), engine.Crystal(5, (0, 1, 2)))
        bad_rows = (
            good[:-1],
            (engine.Crystal(6, (0, 1, 2)), *good[1:]),
            (engine.Crystal(5, (0, 0, 2)), *good[1:]),
            (engine.Crystal(5, (0, 1, 3)), *good[1:]),
            (*good[:2], engine.Crystal(5, (0, 1, 12))),
            (*good[:2], engine.Crystal(4, (0, 1, 2))),
        )
        for rows in bad_rows:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                engine.verify(rows, 16, 3)
        with self.assertRaises(ValueError):
            engine.verify(good, 15, 3)

    def test_unknown_and_late_infeasible_are_not_reported_as_proof(self):
        for status in (cp_model.UNKNOWN, cp_model.FEASIBLE, cp_model.MODEL_INVALID):
            with self.subTest(status=status), patch.object(engine, "_solve_interruptibly", return_value=status):
                with self.assertRaises(engine.SolveIncomplete):
                    engine.solve(16, 3)
        native = engine._solve_interruptibly
        calls = 0

        def later_failure(solver, model):
            nonlocal calls
            calls += 1
            return native(solver, model) if calls == 1 else cp_model.INFEASIBLE

        with patch.object(engine, "_solve_interruptibly", side_effect=later_failure):
            with self.assertRaises(engine.SolveIncomplete):
                engine.solve(16, 3)

    def test_interrupt_stops_worker_and_propagates(self):
        started, stopped, finished = Event(), Event(), Event()

        class SlowSolver:
            def solve(self, model):
                started.set()
                stopped.wait(5)
                finished.set()
                return cp_model.UNKNOWN

            def stop_search(self):
                stopped.set()

        def interrupt():
            started.wait(2)
            _thread.interrupt_main()

        timer = Timer(0.05, interrupt)
        timer.start()
        try:
            with self.assertRaises(KeyboardInterrupt):
                engine._solve_interruptibly(SlowSolver(), None)
        finally:
            stopped.set()
            timer.join()
        self.assertTrue(finished.is_set())


class InterfaceTests(unittest.TestCase):
    def test_repeated_input_defaults_and_validation(self):
        result = engine.Result("infeasible", 1, 3)
        with patch("builtins.input", side_effect=["", "0", "61", "2.5", "abc", "1", "", "q"]), \
                patch.object(engine, "solve_level", return_value=result) as solve, \
                redirect_stdout(io.StringIO()) as output:
            self.assertEqual(calculator.main([]), 0)
        self.assertEqual([call.args[0] for call in solve.call_args_list], [1, 1])
        self.assertEqual(output.getvalue().count("1~60의 정수를 입력하세요"), 5)

    def test_interrupted_calculation_can_be_followed_by_new_input(self):
        with patch("builtins.input", side_effect=["20", "1", "q"]), \
                patch.object(engine, "solve_level", side_effect=[KeyboardInterrupt, engine.Result("infeasible", 1, 3)]), \
                redirect_stdout(io.StringIO()) as output:
            self.assertEqual(calculator.main([]), 0)
        self.assertIn("최적해·불가능 판정은 하지 않았습니다", output.getvalue())
        self.assertIn("아티팩트 Lv.1", output.getvalue())

    def test_errors_are_not_infeasibility(self):
        with patch.object(engine, "solve_level", side_effect=RuntimeError("test error")), \
                redirect_stderr(io.StringIO()) as output:
            self.assertEqual(calculator.calculate(20), 1)
        self.assertIn("계산 오류", output.getvalue())

    def test_cli_utf8_and_invalid_level(self):
        path = str(Path(__file__).with_name("calculator.py"))
        invalid = subprocess.run([sys.executable, path, "--level", "61"], capture_output=True)
        self.assertEqual(invalid.returncode, 2)
        low = subprocess.run([sys.executable, path, "--level", "1"], capture_output=True)
        self.assertEqual(low.returncode, 2)
        self.assertIn("조건 충족 불가능", low.stdout.decode("utf-8"))

    @unittest.skipUnless(sys.platform == "win32", "Windows launcher")
    def test_launcher_from_another_working_directory(self):
        launcher = Path(__file__).with_name("Run-ArtifactCalculator.cmd").resolve()
        run = subprocess.run(
            ["cmd.exe", "/d", "/c", str(launcher)], input=b"20\nq\n", capture_output=True,
            cwd=launcher.parents[2], timeout=30,
        )
        self.assertEqual(run.returncode, 0, run.stderr.decode("utf-8", errors="replace"))
        output = run.stdout.decode("utf-8")
        self.assertIn("최적해 확정", output)
        self.assertIn("실제 효과 레벨 총합: 57 / 120", output)


if __name__ == "__main__":
    unittest.main()
