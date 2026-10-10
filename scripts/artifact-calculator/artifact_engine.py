"""Exact artifact allocation. No API calls, disk writes, or game interaction."""

from dataclasses import dataclass
from itertools import combinations_with_replacement
from threading import Event, Thread
from time import perf_counter
from typing import Callable

from ortools.sat.python import cp_model


# Order is also the lexicographic tie-break order (critical rate is mandatory).
EFFECTS = (
    "치확", "크뎀", "공마", "보공", "데미지", "방무",
    "올스탯", "드롭", "메획", "경험치", "벞지", "재사용",
)
COSTS = (0, 1, 3, 5, 8)
FIXED_OPTIONS = ((0, 1, 2), (3, 4, 5))
CRYSTAL_NAMES = ("주황버섯", "뿔버섯", "슬라임", "스텀프", "스톤골렘")


@dataclass(frozen=True)
class Crystal:
    level: int
    options: tuple[int, ...]


@dataclass(frozen=True)
class Metrics:
    used_ap: int
    level_sum: int
    raw: tuple[int, ...]
    effective: tuple[int, ...]
    overflow: tuple[int, ...]

    @property
    def total(self) -> int:
        return sum(self.effective)

    @property
    def rank(self) -> tuple[int, ...]:
        return (self.total, int(self.effective[6] > 0), *self.effective[1:], -self.used_ap)


@dataclass(frozen=True)
class Result:
    status: str
    budget: int
    count: int
    crystals: tuple[Crystal, ...] = ()
    metrics: Metrics | None = None
    elapsed: float = 0.0


class SolveIncomplete(RuntimeError):
    """A stopped/invalid solve is not an infeasibility or optimality proof."""


def _solve_interruptibly(solver, model):
    """Keep Python's main thread responsive while the native solver runs."""
    outcome = []
    finished = Event()

    def run():
        try:
            outcome.append(solver.solve(model))
        except BaseException as exc:
            outcome.append(exc)
        finally:
            finished.set()

    worker = Thread(target=run, daemon=True)
    worker.start()
    try:
        while not finished.wait(0.05):
            pass
    except KeyboardInterrupt:
        # Repeated stop requests also cover interruption before the native
        # solve wrapper has been created. Never leave a solve in the background.
        while not finished.is_set():
            try:
                solver.stop_search()
                finished.wait(0.05)
            except KeyboardInterrupt:
                continue
        raise
    worker.join()
    if isinstance(outcome[0], BaseException):
        raise outcome[0]
    return outcome[0]


def resources(level: int) -> tuple[int, int]:
    if type(level) is not int or not 1 <= level <= 60:
        raise ValueError("아티팩트 레벨은 1~60의 정수여야 합니다.")
    return level + level // 5, 3 + level // 10


def verify(crystals: tuple[Crystal, ...], budget: int, count: int) -> Metrics:
    """Recompute from actual rows, independently of solver variables."""
    if len(crystals) != count:
        raise ValueError("검산 실패: 크리스탈 수")
    raw = [0] * len(EFFECTS)
    used_ap = level_sum = 0
    for i, crystal in enumerate(crystals):
        if type(crystal.level) is not int or not 1 <= crystal.level <= 5:
            raise ValueError("검산 실패: 크리스탈 레벨")
        if len(crystal.options) != 3 or len(set(crystal.options)) != 3:
            raise ValueError("검산 실패: 서로 다른 옵션 3개 필요")
        if any(type(j) is not int or not 0 <= j < 12 for j in crystal.options):
            raise ValueError("검산 실패: 대상 밖 옵션")
        if i < 2 and set(crystal.options) != set(FIXED_OPTIONS[i]):
            raise ValueError("검산 실패: 고정 옵션 변경")
        used_ap += COSTS[crystal.level - 1]
        level_sum += crystal.level
        for j in crystal.options:
            raw[j] += crystal.level
    effective = tuple(min(value, 10) for value in raw)
    overflow = tuple(value - applied for value, applied in zip(raw, effective))
    if used_ap > budget or effective[0] != 10:
        raise ValueError("검산 실패: AP 예산 또는 치확 Lv.10 조건")
    if sum(effective) != 3 * level_sum - sum(overflow):
        raise ValueError("검산 실패: 총합 항등식")
    return Metrics(used_ap, level_sum, tuple(raw), effective, overflow)


def _level_candidates(budget: int, count: int) -> list[tuple[tuple[int, ...], int]]:
    """Safe bound from level multisets and the least possible critical overflow.

    Ignore other option-slot restrictions: this may overestimate the score,
    but can never exclude a valid optimum. An empty list proves infeasibility.
    """
    candidates = []
    for free in combinations_with_replacement(range(1, 6), count - 2):
        free_cost = sum(COSTS[level - 1] for level in free)
        if free_cost > budget:
            continue
        subsets = {0}
        for level in free:
            subsets |= {value + level for value in tuple(subsets)}
        for orange in range(1, 6):
            critical = [orange + value for value in subsets if orange + value >= 10]
            if not critical:
                continue
            waste = min(critical) - 10
            for horn in range(1, 6):
                cost = free_cost + COSTS[orange - 1] + COSTS[horn - 1]
                if cost <= budget:
                    bound = min(120, 3 * (orange + horn + sum(free)) - waste)
                    candidates.append(((orange, horn, *reversed(free)), bound))
    return candidates


def _possible_effects(levels: tuple[int, ...], effect: int) -> set[int]:
    base = sum(levels[i] for i in range(2) if effect in FIXED_OPTIONS[i])
    sums = {base}
    for level in levels[2:]:
        sums |= {value + level for value in tuple(sums)}
    return {min(value, 10) for value in sums}


def _expand_group(level: int, size: int, degrees: list[int]) -> list[Crystal]:
    """Realize a binary matrix with row sums 3 and the supplied column sums.

    0 <= degree[j] <= size and sum(degrees) == 3*size are sufficient here:
    take the three largest positive degrees at each step. Every column whose
    degree equals the remaining row count must be selected (there are <=3).
    The same conditions therefore hold after each row is removed.
    """
    if any(value < 0 or value > size for value in degrees) or sum(degrees) != 3 * size:
        raise ValueError("검산 실패: 옵션 배치 복원 조건")
    remaining = list(degrees)
    rows = []
    for _ in range(size):
        selected = sorted(range(12), key=lambda j: (-remaining[j], j))[:3]
        if any(remaining[j] <= 0 for j in selected):
            raise ValueError("검산 실패: 옵션 배치 복원")
        for j in selected:
            remaining[j] -= 1
        rows.append(Crystal(level, tuple(sorted(selected))))
    if any(remaining):
        raise ValueError("검산 실패: 복원 후 남은 옵션")
    return rows


def solve(
    budget: int,
    count: int,
    progress: Callable[[str], None] | None = None,
) -> Result:
    """Internal AP/count interface. Public CLI accepts artifact level only."""
    if type(budget) is not int or budget < 0:
        raise ValueError("AP 예산은 0 이상의 정수여야 합니다.")
    if type(count) is not int or not 3 <= count <= 9:
        raise ValueError("크리스탈 수는 3~9의 정수여야 합니다.")
    start = perf_counter()
    report = progress or (lambda message: None)
    candidates = _level_candidates(min(budget, 8 * count), count)
    if not candidates:
        return Result("infeasible", budget, count, elapsed=perf_counter() - start)
    upper = max(bound for _, bound in candidates)

    model = cp_model.CpModel()
    all_vars = []

    def integer(low, high, name):
        var = model.new_int_var(low, high, name)
        all_vars.append(var)
        return var

    levels = [integer(1, 5, f"fixed_level_{i}") for i in range(2)]
    costs = [integer(0, 8, f"fixed_cost_{i}") for i in range(2)]
    for i in range(2):
        model.add_element(levels[i] - 1, COSTS, costs[i])

    # Exchangeable free crystals are represented by counts at each level.
    # At a given level, degree[j] counts crystals carrying effect j. This
    # representation is exact; _expand_group constructs the individual rows.
    sizes = [integer(0, count - 2, f"size_{k}") for k in range(1, 6)]
    model.add(sum(sizes) == count - 2)
    degrees = []
    for k in range(5):
        row = [integer(0, count - 2, f"degree_{k + 1}_{j}") for j in range(12)]
        for j in range(12):
            model.add(row[j] <= sizes[k])
        model.add(sum(row) == 3 * sizes[k])
        degrees.append(row)

    spent = integer(0, 8 * count, "spent")
    model.add(spent == sum(costs) + sum(COSTS[k] * sizes[k] for k in range(5)))
    model.add(spent <= min(budget, 8 * count))
    effective = []
    for j in range(12):
        raw = integer(0, 5 * count, f"raw_{j}")
        value = integer(0, 10, f"effective_{j}")
        base = sum(levels[i] for i in range(2) if j in FIXED_OPTIONS[i])
        model.add(raw == base + sum((k + 1) * degrees[k][j] for k in range(5)))
        model.add_min_equality(value, [raw, 10])
        effective.append(value)
    model.add(effective[0] == 10)
    total = integer(10, upper, "total")
    model.add(total == sum(effective))
    has_allstat = integer(0, 1, "has_allstat")
    model.add(effective[6] >= 1).only_enforce_if(has_allstat)
    model.add(effective[6] == 0).only_enforce_if(has_allstat.Not())

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 0
    solver.parameters.catch_sigint_signal = False
    objectives = [("효과 총합 최대화", total, False, None)]
    objectives += [("최대 총합 유지: 올스탯 확보 가능 여부", has_allstat, False, None)]
    objectives += [(f"동점 비교: {EFFECTS[j]}", effective[j], False, j) for j in range(1, 12)]
    objectives += [("동점 비교: AP 최소화", spent, True, None)]
    proven = []
    for index, (label, objective, minimize, effect_index) in enumerate(objectives):
        report(f"[{index + 1}/{len(objectives)}] {label}")
        if minimize:
            model.minimize(objective)
        else:
            model.maximize(objective)
        status = _solve_interruptibly(solver, model)
        if status == cp_model.INFEASIBLE and index == 0:
            return Result("infeasible", budget, count, elapsed=perf_counter() - start)
        if status != cp_model.OPTIMAL:
            raise SolveIncomplete(f"{label}: {solver.status_name(status)} — 전체 최적해 미확정")
        optimum = solver.value(objective)
        proven.append(optimum)
        model.add(objective == optimum)
        # A score bound or a subset-sum impossibility eliminates an entire
        # level configuration without enumerating any option allocations.
        if index == 0 or effect_index is not None:
            remaining = [
                (values, bound) for values, bound in candidates
                if (bound >= optimum if index == 0 else optimum in _possible_effects(values, effect_index))
            ]
            if len(remaining) < len(candidates):
                allowed = [(values[0], values[1], *(values[2:].count(k) for k in range(1, 6))) for values, _ in remaining]
                model.add_allowed_assignments(levels + sizes, allowed)
                candidates = remaining
        model.clear_hints()
        for var in all_vars:
            model.add_hint(var, solver.value(var))

    rows = [Crystal(solver.value(levels[i]), FIXED_OPTIONS[i]) for i in range(2)]
    for k in reversed(range(5)):
        rows.extend(_expand_group(k + 1, solver.value(sizes[k]), [solver.value(var) for var in degrees[k]]))
    crystals = tuple(rows)
    metrics = verify(crystals, budget, count)
    if (metrics.total, int(metrics.effective[6] > 0), *metrics.effective[1:], metrics.used_ap) != tuple(proven):
        raise ValueError("검산 실패: 최적화 단계별 값과 실제 배치 불일치")
    return Result("optimal", budget, count, crystals, metrics, perf_counter() - start)


def solve_level(level: int, progress: Callable[[str], None] | None = None) -> Result:
    return solve(*resources(level), progress=progress)
