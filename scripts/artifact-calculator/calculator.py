"""Korean terminal interface: double-click or --level N."""

import argparse
import sys
from artifact_output import display
from artifact_policy import MODE_NAMES, Mode


def calculate(level, *, mode=Mode.CORE6):
    from artifact_engine import SolveIncomplete, solve_level

    try:
        result = solve_level(level, progress=lambda text: print(text, flush=True), mode=mode)
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
    parser.add_argument("--mode", type=Mode, choices=list(Mode), default=Mode.CORE6,
                        help="계산 방식 (기본: core6, 반복 입력에서는 최초 기본값)")
    args = parser.parse_args(argv)
    try:
        import artifact_engine
    except ImportError as exc:
        print(f"실행 환경이 준비되지 않았습니다: {exc}\nREADME의 설치 절차를 확인하세요.", file=sys.stderr)
        return 1
    if args.level is not None:
        return calculate(args.level, mode=args.mode)

    return interactive(mode=args.mode)


def select_mode(current):
    """Return the chosen mode or None when the user exits at this prompt."""
    choices = {str(i): mode for i, mode in enumerate(Mode, 1)}
    default = next(key for key, mode in choices.items() if mode == current)
    print("\n계산 방식")
    for key, mode in choices.items():
        print(f"{key}. {MODE_NAMES[mode]}")
    while True:
        try:
            text = input(f"선택 [Enter: {default}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            return None
        if text.lower() in ("q", "quit", "exit"):
            return None
        if not text:
            return current
        if text in choices:
            return choices[text]
        print("1~3 중 선택하세요. 종료하려면 q를 입력하세요.")


def interactive(*, mode=Mode.CORE6):
    """Repeat level input without mixing command-line argument handling."""
    from artifact_engine import resources

    print("유니온 아티팩트 배치 계산기")
    print("현재 아티팩트 레벨과 계산 방식을 선택하세요. 총 AP로 전체 배치를 다시 계산합니다.")
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
        selected = select_mode(mode)
        if selected is None:
            return 0
        previous, mode = level, selected
        calculate(level, mode=mode)


if __name__ == "__main__":
    sys.exit(main())
