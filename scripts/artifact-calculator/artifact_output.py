"""Korean result rendering; no solving or interactive input."""

import unicodedata


def table(headers, rows):
    def width(text):
        return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)

    rows = [tuple(map(str, row)) for row in [headers, *rows]]
    widths = [max(width(row[i]) for row in rows) for i in range(len(headers))]
    for index, row in enumerate(rows):
        print(" | ".join(text + " " * (size - width(text)) for text, size in zip(row, widths)))
        if index == 0:
            print("-+-".join("-" * size for size in widths))


def display(level, result):
    from artifact_engine import CRYSTAL_NAMES, COSTS, EFFECTS

    print(f"\n아티팩트 Lv.{level} | 총 AP {result.budget} | 크리스탈 {result.count}개")
    if result.status == "infeasible":
        print("조건 충족 불가능: 이 레벨에서는 고정 옵션을 유지하며 치확 Lv.10을 확보할 수 없습니다.")
        print(f"계산 시간: {result.elapsed:.3f}초")
        return
    print("최적해 확정 — 치확 10 → 핵심 6종 합계 → 핵심 효과 우선순위")
    print("→ 전체 효과 합계 → 나머지 효과 우선순위 → AP 최소")
    rows = []
    for i, crystal in enumerate(result.crystals):
        name = CRYSTAL_NAMES[i] if i < len(CRYSTAL_NAMES) else f"크리스탈 {i + 1}"
        rows.append((name, crystal.level, " / ".join(EFFECTS[j] for j in crystal.options), COSTS[crystal.level - 1]))
    table(("크리스탈", "레벨", "옵션", "AP"), rows)
    metrics = result.metrics
    print(f"\n사용 AP: {metrics.used_ap} / {result.budget} | 남은 AP: {result.budget - metrics.used_ap}")
    print(f"크리스탈 레벨 합: {metrics.level_sum}")
    print(f"핵심 6종 효과 합계: {metrics.core_total} / 60")
    print(f"올스탯 적용 레벨: {metrics.effective[6]} / 10")
    print(f"실제 효과 레벨 총합: {metrics.total} / 120 | 초과분 합: {sum(metrics.overflow)}")
    print()
    table(("효과", "원시 합계", "적용 레벨", "초과분"), [
        (name, metrics.raw[j], metrics.effective[j], metrics.overflow[j]) for j, name in enumerate(EFFECTS)
    ])
    print(f"계산 시간: {result.elapsed:.3f}초\n")
