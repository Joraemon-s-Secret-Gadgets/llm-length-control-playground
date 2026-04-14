"""
자기소개서 분량 재조정의 핵심 비즈니스 로직.
LLM 호출 → 후처리 파이프라인 → 검증 → 재시도.

UI(Chainlit)와 독립적으로 동작하도록 설계.
"""

from openai import AsyncOpenAI

# 패키지 내부 import (상대 경로)
from .text_counter import count_with_spaces
from .text_utils import (
    fix_korean_sentence_endings,
    ensure_paragraphs,
    smart_trim,
    count_paragraphs,
    extract_numbers,
    detect_fabricated_numbers,
)
from .prompts import (
    SYSTEM_PROMPT,
    build_initial_prompt,
    build_retry_prompt,
    build_revision_prompt,
)
from .types import AdjustmentResult, RevisionResult
from .exceptions import (                              # ⭐ 추가
    EmptyTextError,
    InvalidTargetLengthError,
    TextTooShortError,
)

# LLM이 목표치보다 얼마나 길게 쓸지의 비율
OVERSHOOT_RATIO = 1.15
MAX_RETRIES = 2
MODEL_NAME = "gpt-4o-mini"


class LengthController:
    """자기소개서 분량 재조정 컨트롤러."""

    def __init__(self, client: AsyncOpenAI = None):
        self.client = client or AsyncOpenAI()

    async def adjust_length(
        self,
        original_text: str,
        min_len: int,
        max_len: int,
        on_token=None,
        on_status=None,
    ) -> AdjustmentResult:
        """
        원문을 목표 글자수 범위로 재조정한다.

        Args:
            original_text: 재조정할 원본 자소서
            min_len: 최소 글자 수 (공백 포함)
            max_len: 최대 글자 수 (공백 포함)
            on_token: 토큰 수신 시 호출될 비동기 콜백 (optional, UI 스트리밍용)
            on_status: 상태 변경 시 호출될 비동기 콜백 (optional, 진행률 표시용)

        Returns:
            AdjustmentResult: 조정 결과 객체
                - text: 최종 자소서 본문
                - length: 최종 글자 수
                - success: 검증 통과 여부
                - attempts: 총 시도 횟수
                - errors: 검증 실패 사유 (실패 시)
        """
        # === 입력 검증 ===
        if not original_text or not original_text.strip():
            raise EmptyTextError()

        if min_len <= 0 or max_len <= 0:
            raise InvalidTargetLengthError(
                min_len, max_len, reason="글자수는 양수여야 합니다"
            )

        if min_len > max_len:
            raise InvalidTargetLengthError(
                min_len, max_len, reason="최소값이 최대값보다 큽니다"
            )

        text_length = count_with_spaces(original_text)
        if text_length < max_len * 0.3:
            raise TextTooShortError(text_length, max_len)

        # === 본 로직 시작 ===
        # LLM에게 지시할 목표치 (상한의 +15%)
        generous_target = int(max_len * OVERSHOOT_RATIO)
        llm_min = max_len
        llm_max = generous_target

        original_num_set = extract_numbers(original_text)
        user_prompt = build_initial_prompt(
            original_text, llm_min, llm_max, min_len, max_len
        )

        final_text = ""
        last_errors = []

        for attempt in range(MAX_RETRIES):
            temperature = 0.2 + (attempt * 0.2)

            if on_status:
                await on_status(
                    f"⚙️ {min_len}~{max_len}자로 조정 중... "
                    f"(시도 {attempt + 1}/{MAX_RETRIES}, temp={temperature:.1f})"
                )

            # LLM 호출 (스트리밍)
            stream = await self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                temperature=temperature,
            )

            raw_text = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    raw_text += token
                    if on_token:
                        await on_token(token)

            # 후처리 파이프라인
            processed = fix_korean_sentence_endings(raw_text)
            processed = ensure_paragraphs(processed, sentences_per_paragraph=3)
            processed = smart_trim(processed, min_len, max_len)
            processed = fix_korean_sentence_endings(processed)

            final_text = processed
            final_len = count_with_spaces(final_text)
            paragraph_count = count_paragraphs(final_text)

            # 검증
            errors = []
            if not (min_len <= final_len <= max_len):
                errors.append(f"글자 수 {final_len}자 (목표 {min_len}~{max_len})")
            if paragraph_count < 3:
                errors.append(f"문단 {paragraph_count}개 (최소 3개)")

            fabricated = detect_fabricated_numbers(original_num_set, final_text)
            if fabricated:
                errors.append(f"원문에 없는 수치 감지: {', '.join(fabricated[:3])}")

            # 통과 시 즉시 반환
            if not errors:
                return AdjustmentResult(
                    success=True,
                    text=final_text,
                    length=final_len,
                    attempts=attempt + 1,
                    errors=[],
                )

            last_errors = errors

            # 재시도 프롬프트 구성
            if attempt < MAX_RETRIES - 1:
                user_prompt = build_retry_prompt(
                    original_text, final_text, errors, llm_min, llm_max
                )

        # 재시도 소진
        return AdjustmentResult(
            success=False,
            text=final_text,
            length=count_with_spaces(final_text),
            attempts=MAX_RETRIES,
            errors=last_errors,
        )

    async def revise_text(
        self,
        original_text: str,
        current_text: str,
        user_feedback: str,
        min_len: int,
        max_len: int,
        on_token=None,
        on_status=None,
    ) -> RevisionResult:
        """
        사용자 피드백을 반영해 기존 결과물을 수정한다.

        Args:
            original_text: 원본 자소서 (사실 검증 기준)
            current_text: 현재 결과물 (수정 대상)
            user_feedback: 사용자의 수정 요청 (자연어)
            min_len, max_len: 유지할 글자 수 범위
            on_token, on_status: UI 콜백

        Returns:
            RevisionResult: 수정 결과 객체
        """
        original_num_set = extract_numbers(original_text)
        user_prompt = build_revision_prompt(
            original_text, current_text, user_feedback, min_len, max_len
        )

        if on_status:
            await on_status(f'✏️ 피드백 반영 중: "{user_feedback[:30]}..."')

        stream = await self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            temperature=0.3,  # 수정은 안정적으로
        )

        raw_text = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                token = chunk.choices[0].delta.content
                raw_text += token
                if on_token:
                    await on_token(token)

        # 후처리 파이프라인 (adjust_length와 동일)
        processed = fix_korean_sentence_endings(raw_text)
        processed = ensure_paragraphs(processed, sentences_per_paragraph=3)
        processed = smart_trim(processed, min_len, max_len)
        processed = fix_korean_sentence_endings(processed)

        final_len = count_with_spaces(processed)
        paragraph_count = count_paragraphs(processed)

        # 검증
        errors = []
        if not (min_len <= final_len <= max_len):
            errors.append(f"글자 수 {final_len}자 (목표 {min_len}~{max_len})")
        if paragraph_count < 3:
            errors.append(f"문단 {paragraph_count}개 (최소 3개)")

        fabricated = detect_fabricated_numbers(original_num_set, processed)
        if fabricated:
            errors.append(f"원문에 없는 수치: {', '.join(fabricated[:3])}")

        return RevisionResult(
            success=len(errors) == 0,
            text=processed,
            length=final_len,
            errors=errors,
        )