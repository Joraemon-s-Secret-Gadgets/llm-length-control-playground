"""
LLM 기반 자기소개서 글자수 정밀 제어 패키지.

주요 기능:
- 자소서 분량을 목표 글자수에 정밀하게 맞춤
- 사용자 피드백 기반 대화형 수정
- 사실 날조 방지 (원문 사실관계 100% 보존)
- STAR 구조 기반 문단 정비

기본 사용법:
    >>> from llm_length_control import LengthController
    >>> controller = LengthController()
    >>> result = await controller.adjust_length(
    ...     original_text="자소서 원본...",
    ...     min_len=790,
    ...     max_len=800,
    ... )
    >>> print(result["text"])
"""

# 핵심 진입점 노출
from .controller import LengthController

# 데이터 타입
from .types import AdjustmentResult, RevisionResult

# 예외 클래스
from .exceptions import (
    LengthControlError,
    TextTooShortError,
    InvalidTargetLengthError,
    EmptyTextError,
    LLMResponseError,
)

# 자주 쓰이는 헬퍼 함수
from .text_utils import (
    parse_target_length,
    count_paragraphs,
)
from .text_counter import (
    count_with_spaces,
    count_without_spaces,
)

# 외부에서 import 가능한 이름들 (선택적이지만 권장)
__all__ = [
    # 핵심 클래스
    "LengthController",

    # 데이터 타입
    "AdjustmentResult",
    "RevisionResult",

    # 예외 클래스
    "LengthControlError",
    "TextTooShortError",
    "InvalidTargetLengthError",
    "EmptyTextError",
    "LLMResponseError",

    # 헬퍼 함수
    "parse_target_length",
    "count_paragraphs",
    "count_with_spaces",
    "count_without_spaces",
]

# 패키지 버전
__version__ = "0.2.0"