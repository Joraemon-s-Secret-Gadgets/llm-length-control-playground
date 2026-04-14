"""
패키지에서 사용하는 사용자 정의 예외 클래스.
호출자가 상황별로 적절히 대응할 수 있도록 명확한 예외 계층을 제공한다.

사용 예:
    >>> try:
    ...     result = await controller.adjust_length(...)
    ... except TextTooShortError as e:
    ...     print(f"원문이 너무 짧습니다: {e}")
    ... except InvalidTargetLengthError as e:
    ...     print(f"잘못된 목표 글자수: {e}")
    ... except LengthControlError as e:
    ...     print(f"기타 오류: {e}")
"""


class LengthControlError(Exception):
    """패키지의 모든 예외의 기본 클래스.

    이 예외만 catch하면 패키지에서 발생하는 모든 에러를 처리할 수 있다.
    """
    pass


class TextTooShortError(LengthControlError):
    """원문이 목표 분량 대비 너무 짧을 때 발생.

    원문이 목표 글자수의 30% 미만이면 LLM이 사실 날조 없이는
    분량을 채우기 어렵다.
    """

    def __init__(self, text_length: int, target_length: int):
        self.text_length = text_length
        self.target_length = target_length
        message = (
            f"원문 {text_length}자가 목표 {target_length}자의 30%(권장 최소치)에 "
            f"미달합니다. 원문을 더 보강해주세요."
        )
        super().__init__(message)


class InvalidTargetLengthError(LengthControlError):
    """목표 글자수가 유효하지 않을 때 발생.

    예: min > max, 음수, 0 이하 등.
    """

    def __init__(self, min_len: int, max_len: int, reason: str = ""):
        self.min_len = min_len
        self.max_len = max_len
        message = f"잘못된 목표 글자수 범위: min={min_len}, max={max_len}"
        if reason:
            message += f" ({reason})"
        super().__init__(message)


class EmptyTextError(LengthControlError):
    """원문이 비어있거나 공백뿐일 때 발생."""

    def __init__(self):
        super().__init__("원문이 비어있습니다. 자소서 텍스트를 입력해주세요.")


class LLMResponseError(LengthControlError):
    """LLM 응답에 문제가 있을 때 발생.

    예: API 오류, 빈 응답, 형식 오류 등.
    """

    def __init__(self, message: str = "LLM 응답에 문제가 발생했습니다."):
        super().__init__(message)