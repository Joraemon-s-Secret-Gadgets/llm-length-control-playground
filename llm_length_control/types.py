"""
패키지에서 사용하는 데이터 타입 정의.
함수 반환값을 dict 대신 명시적인 객체로 표현해 타입 안전성을 높인다.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class AdjustmentResult:
    """
    분량 조정 결과를 담는 데이터 클래스.

    Attributes:
        text: 조정된 자기소개서 본문
        length: 최종 글자 수 (공백 포함)
        success: 검증 통과 여부 (True = 모든 검증 통과)
        attempts: 총 LLM 호출 시도 횟수
        errors: 검증 실패 사유 목록 (success=True면 빈 리스트)

    Example:
        >>> result = await controller.adjust_length(...)
        >>> if result.success:
        ...     print(f"성공! {result.length}자")
        ... else:
        ...     print(f"실패: {', '.join(result.errors)}")
    """
    text: str
    length: int
    success: bool
    attempts: int = 1
    errors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """간단한 텍스트 요약."""
        status = "✅ 성공" if self.success else "⚠️ 실패"
        return f"AdjustmentResult({status}, {self.length}자, {self.attempts}회 시도)"


@dataclass
class RevisionResult:
    """
    피드백 기반 수정 결과를 담는 데이터 클래스.
    AdjustmentResult와 유사하지만 attempts 정보가 없다 (수정은 1회 시도).

    Attributes:
        text: 수정된 자기소개서 본문
        length: 최종 글자 수 (공백 포함)
        success: 검증 통과 여부
        errors: 검증 실패 사유 목록
    """
    text: str
    length: int
    success: bool
    errors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "✅ 성공" if self.success else "⚠️ 실패"
        return f"RevisionResult({status}, {self.length}자)"