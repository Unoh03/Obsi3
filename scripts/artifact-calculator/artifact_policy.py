"""Shared policy definitions; independent of OR-Tools and user input."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


EFFECTS = (
    "치확", "크뎀", "공마", "보공", "데미지", "방무",
    "올스탯", "드롭", "메획", "경험치", "벞지", "재사용",
)


class Mode(StrEnum):
    CORE6 = "core6"
    CORE7 = "core7"
    TOTAL = "total"


MODE_NAMES = {
    Mode.CORE6: "핵심 6종 우선",
    Mode.CORE7: "핵심 6종 → 올스탯 우선",
    Mode.TOTAL: "전체 합계 우선",
}
MODE_SUMMARIES = {
    Mode.CORE6: "핵심 6종 합계 → 핵심 효과 우선순위 → 전체 효과 합계 → 나머지 효과 우선순위 → AP 최소",
    Mode.CORE7: "핵심 6종 합계 → 핵심 효과 우선순위 → 올스탯 → 전체 효과 합계 → 나머지 효과 우선순위 → AP 최소",
    Mode.TOTAL: "전체 효과 합계 → 효과 우선순위 → AP 최소",
}


@dataclass(frozen=True)
class Objective:
    target: Literal["core_total", "total", "effect", "spent"]
    label: str
    effect_index: int | None = None
    minimize: bool = False


_CORE = (Objective("core_total", "핵심 6종 합계 최대화"),) + tuple(
    Objective("effect", f"핵심 동점 비교: {EFFECTS[j]}", j) for j in range(1, 6)
)
_EFFECTS = tuple(Objective("effect", f"동점 비교: {name}", j) for j, name in enumerate(EFFECTS))
_TOTAL = (Objective("total", "전체 효과 합계 최대화"),)
_AP = (Objective("spent", "동점 비교: AP 최소화", minimize=True),)

POLICIES = {
    Mode.CORE6: _CORE + _TOTAL + _EFFECTS[6:] + _AP,
    Mode.CORE7: _CORE + _EFFECTS[6:7] + _TOTAL + _EFFECTS[7:] + _AP,
    Mode.TOTAL: _TOTAL + _EFFECTS[1:] + _AP,
}
