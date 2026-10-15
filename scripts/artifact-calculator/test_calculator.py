"""Run with .venv/Scripts/python.exe -m unittest -v.

The exhaustive oracle deliberately does not use the solver, its level bound,
its ranking helper, or its verifier to decide the expected optimum.
"""

import _thread
from contextlib import redirect_stdout, redirect_stderr
import io
from itertools import combinations, combinations_with_replacement, product
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
            key = (sum(totals[:6]), *totals[1:6], sum(totals), *totals[6:], -cost)
            best_by_cost[cost] = max(best_by_cost.get(cost, key), key)
    return {
        budget: max((rank for cost, rank in best_by_cost.items() if cost <= budget), default=None)
        for budget in range(25)
    }


class EngineTests(unittest.TestCase):
    def test_representative_levels_follow_core_first_policy(self):
        fixtures = {
            20: ((10, 10, 10, 9, 9, 9, 0, 0, 0, 0, 0, 0), 24),
            21: ((10, 10, 10, 9, 9, 9, 0, 0, 0, 0, 0, 0), 24),
            23: ((10,) * 6 + (0,) * 6, 27),
            25: ((10,) * 6 + (0,) * 6, 27),
            30: ((10,) * 7 + (5, 0, 0, 0, 0), 35),
        }
        for level, (effects, cost) in fixtures.items():
            with self.subTest(level=level):
                progress = []
                result = engine.solve_level(level, progress.append)
                self.assertEqual(result.status, "optimal")
                self.assertEqual(result.metrics.effective, effects)
                self.assertEqual(result.metrics.used_ap, cost)
                self.assertEqual(result.metrics.total, sum(effects))
                self.assertEqual(len(progress), 14)
                self.assertIn("핵심 6종 합계", progress[0])
                self.assertIn("전체 효과 합계", progress[6])

    def test_all_levels_feasibility_and_reconstructed_allocations(self):
        # Horn cannot carry critical rate and can stay at level 1 for free.
        # Enumerate the levels of every other crystal independently of the
        # engine's candidate pruning; all can carry critical rate together.
        minimum_cost = {
            count: min(
                sum((0, 1, 3, 5, 8)[value - 1] for value in levels)
                for levels in combinations_with_replacement(range(1, 6), count - 1)
                if sum(levels) >= 10
            ) for count in range(3, 10)
        }
        for level, (budget, count) in enumerate(zip(AP_TABLE, COUNT_TABLE), 1):
            with self.subTest(level=level):
                result = engine.solve_level(level)
                possible = budget >= minimum_cost[count]
                self.assertEqual(result.status, "optimal" if possible else "infeasible")
                if possible:
                    metrics = engine.verify(result.crystals, budget, count)
                    self.assertEqual(metrics, result.metrics)
                    self.assertEqual(metrics.total, 3 * metrics.level_sum - sum(metrics.overflow))
                else:
                    self.assertIsNone(result.metrics)
                    self.assertEqual(result.crystals, ())

    def test_policy_hierarchy_with_controlled_candidates(self):
        # Artificial candidate metrics isolate policy ordering, not game
        # feasibility. Real allocations are covered by exhaustive/regression tests.
        core = (10, 10, 10, 9, 9, 9)
        cases = [
            ((10,) * 6 + (0,) * 6, 30, core + (10,) * 6, 20),
            (core + (0,) * 6, 30, (10, 9, 10, 10, 9, 9) + (10,) * 6, 20),
            ((10,) * 6 + (5, 10, 0, 0, 0, 0), 30, (10,) * 6 + (10, 0, 0, 0, 0, 0), 20),
            ((10,) * 6 + (10, 5, 0, 0, 0, 0), 30, (10,) * 6 + (5, 10, 0, 0, 0, 0), 20),
            ((10,) * 6 + (0,) * 6, 27, (10,) * 6 + (0,) * 6, 30),
        ]
        # Each adjacent effect must beat any gains in later effects at tied sums.
        for indexes in (range(1, 6), range(6, 12)):
            for earlier, later in zip(indexes, list(indexes)[1:]):
                preferred = [10] + [5] * 11
                other = preferred.copy()
                preferred[earlier] += 1
                other[later] += 1
                cases.append((tuple(preferred), 30, tuple(other), 20))
        for preferred, cost, other, other_cost in cases:
            with self.subTest(preferred=preferred, other=other, cost=cost):
                model = cp_model.CpModel()
                effects = [model.new_int_var(0, 10, f"e{j}") for j in range(12)]
                total = model.new_int_var(0, 120, "total")
                core_total = model.new_int_var(0, 60, "core_total")
                spent = model.new_int_var(0, 72, "spent")
                model.add(total == sum(effects))
                model.add(core_total == sum(effects[:6]))
                model.add_allowed_assignments(effects + [spent], [(*preferred, cost), (*other, other_cost)])
                problem = engine._AllocationModel(model, effects + [total, core_total, spent],
                                                  [], [], [], effects, total, core_total, spent)
                solver, proven = engine._optimize(problem, [], lambda _: None)
                self.assertEqual(tuple(solver.value(v) for v in effects), preferred)
                self.assertEqual(solver.value(spent), cost)
                metrics = engine.Metrics(cost, 0, preferred, preferred, (0,) * 12)
                alternative = engine.Metrics(other_cost, 0, other, other, (0,) * 12)
                self.assertEqual(metrics.objective_values, proven)
                self.assertGreater(metrics.rank, alternative.rank)

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
        self.assertEqual(optimized.metrics.core_total, 57)
        self.assertGreater(optimized.metrics.rank, metrics.rank)

    def test_overflow_is_excluded_from_both_effect_sums(self):
        rows = (
            engine.Crystal(4, (0, 1, 2)), engine.Crystal(4, (3, 4, 5)),
            engine.Crystal(4, (0, 1, 6)), engine.Crystal(4, (0, 2, 6)),
            engine.Crystal(4, (3, 4, 5)),
        )
        metrics = engine.verify(rows, 25, 5)
        self.assertEqual(metrics.effective, (10, 8, 8, 8, 8, 8, 8, 0, 0, 0, 0, 0))
        self.assertEqual((metrics.level_sum, metrics.raw[0], sum(metrics.overflow)), (20, 12, 2))
        self.assertEqual((metrics.core_total, metrics.total), (50, 58))

    def test_level_60_minimizes_ap_after_full_effects(self):
        r = engine.solve_level(60)
        self.assertEqual((r.budget, r.count), (72, 9))
        self.assertEqual(r.metrics.effective, (10,) * 12)
        self.assertEqual(r.metrics.used_ap, 59)
        self.assertLess(engine.solve(58, 9).metrics.total, 120)
        self.assertEqual(engine.verify(r.crystals, 72, 9), r.metrics)

    def test_output_explains_core_first_without_old_allstat_rule(self):
        result = engine.solve_level(25)
        with redirect_stdout(io.StringIO()) as output:
            calculator.display(25, result)
        text = output.getvalue()
        for expected in ("핵심 효과 우선순위", "전체 효과 합계", "핵심 6종 효과 합계: 60 / 60",
                         "올스탯 적용 레벨: 0 / 10", "실제 효과 레벨 총합: 60 / 120",
                         "사용 AP: 27 / 30 | 남은 AP: 3"):
            self.assertIn(expected, text)
        self.assertNotIn("확보할 수 없어 제외", text)

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
    def test_removed_comparison_flags_are_rejected(self):
        for flag, values in (("--compare", ["방무", "올스탯"]), ("--loss", ["0"]), ("--candidate", ["1"])):
            with self.subTest(flag=flag), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                calculator.main(["--level", "25", flag, *values])
            self.assertEqual(exc.exception.code, 2)
        with redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit):
            calculator.main(["--help"])
        self.assertNotIn("--compare", output.getvalue())

    def test_old_comparison_shortcut_is_now_invalid_level(self):
        with patch("builtins.input", side_effect=["c", "q"]), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(calculator.main([]), 0)
        self.assertIn("1~60의 정수를 입력하세요", output.getvalue())
        self.assertNotIn("후보 비교", output.getvalue())

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
