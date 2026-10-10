"""Korean terminal interface: double-click or --level N."""

import argparse
import sys
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
    print("최적해 확정 — 치확 10 → 효과 총합 → 효과 우선순위 → AP 최소")
    rows = []
    for i, crystal in enumerate(result.crystals):
        name = CRYSTAL_NAMES[i] if i < len(CRYSTAL_NAMES) else f"크리스탈 {i + 1}"
        rows.append((name, crystal.level, " / ".join(EFFECTS[j] for j in crystal.options), COSTS[crystal.level - 1]))
    table(("크리스탈", "레벨", "옵션", "AP"), rows)
    metrics = result.metrics
    print(f"\n사용 AP: {metrics.used_ap} / {result.budget} | 남은 AP: {result.budget - metrics.used_ap}")
    print(f"크리스탈 레벨 합: {metrics.level_sum}")
    print(f"실제 효과 레벨 총합: {metrics.total} / 120 | 초과분 합: {sum(metrics.overflow)}")
    print()
    table(("효과", "원시 합계", "적용 레벨", "초과분"), [
        (name, metrics.raw[j], metrics.effective[j], metrics.overflow[j]) for j, name in enumerate(EFFECTS)
    ])
    print(f"계산 시간: {result.elapsed:.3f}초\n")


def calculate(level):
    from artifact_engine import SolveIncomplete, solve_level

    try:
        result = solve_level(level, progress=lambda text: print(text, flush=True))
        display(level, result)
        return 0 if result.status == "optimal" else 2
    except (KeyboardInterrupt, SolveIncomplete):
        print("\n계산이 중단되었거나 완료되지 않았습니다. 최적해·불가능 판정은 하지 않았습니다.")
        return 130
    except Exception as exc:
        print(f"\n계산 오류: {exc}", file=sys.stderr)
        return 1


def main(argv=None):
    # Direct and redirected Windows output use the same UTF-8 encoding.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="유니온 아티팩트 배치 계산기 (레벨 1~60)")
    parser.add_argument("--level", type=int, choices=range(1, 61), metavar="1~60", help="한 번 계산 후 종료")
    args = parser.parse_args(argv)
    try:
        from artifact_engine import resources
    except ImportError as exc:
        print(f"실행 환경이 준비되지 않았습니다: {exc}\nREADME의 설치 절차를 확인하세요.", file=sys.stderr)
        return 1
    if args.level is not None:
        return calculate(args.level)

    print("유니온 아티팩트 배치 계산기")
    print("현재 아티팩트 레벨만 입력하세요. 총 AP로 전체 배치를 다시 계산합니다.")
    print("모든 크리스탈이 활성 상태라고 가정합니다. q: 종료, Ctrl+C: 중단/종료\n")
    previous = None
    while True:
        default = f" [Enter: {previous}]" if previous is not None else ""
        try:
            text = input(f"아티팩트 레벨 (1~60){default}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            return 0
        if text.lower() in ("q", "quit", "exit"):
            return 0
        if not text and previous is not None:
            level = previous
        else:
            try:
                level = int(text)
                resources(level)
            except ValueError:
                print("1~60의 정수를 입력하세요. 종료하려면 q를 입력하세요.\n")
                continue
        previous = level
        calculate(level)


if __name__ == "__main__":
    sys.exit(main())
