"""Korean terminal interface: double-click or --level N."""

import argparse
import sys
from artifact_output import display


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
        import artifact_engine
    except ImportError as exc:
        print(f"실행 환경이 준비되지 않았습니다: {exc}\nREADME의 설치 절차를 확인하세요.", file=sys.stderr)
        return 1
    if args.level is not None:
        return calculate(args.level)

    return interactive()


def interactive():
    """Repeat level input without mixing command-line argument handling."""
    from artifact_engine import resources

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
