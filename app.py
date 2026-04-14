"""
Chainlit 기반 사용자 인터페이스.
- 초기 분량 조정
- 사용자 피드백 기반 수정 (revision loop)
"""

import re
import chainlit as cl
from dotenv import load_dotenv

from text_counter import count_with_spaces, count_without_spaces
from text_utils import parse_target_length, count_paragraphs
from length_controller import LengthController


load_dotenv()
controller = LengthController()


# 대화 종료 키워드
EXIT_KEYWORDS = {"완료", "끝", "종료", "done", "exit", "quit", "끝내기"}


@cl.on_chat_start
async def on_chat_start():
    res_text = await cl.AskUserMessage(
        content=(
            "👋 안녕하세요! 자기소개서 글자 수 편집 챗봇입니다.\n\n"
            "먼저 수정하고 싶은 **자기소개서 원본**을 붙여넣어 주세요."
        ),
        timeout=300,
    ).send()

    if not res_text:
        return

    original_text = res_text['output']
    current_len = count_with_spaces(original_text)

    res_length = await cl.AskUserMessage(
        content=(
            f"📝 현재 글자 수: **{current_len}자** (공백 포함)\n\n"
            f"**목표 글자 수**를 입력해 주세요.\n"
            f"- 단일 숫자 입력 시 자동으로 범위 설정: `1000` → `990~1000자`\n"
            f"- 직접 범위 지정도 가능: `950~1000`"
        ),
        timeout=120,
    ).send()

    if not res_length:
        return

    target_input = res_length['output']
    min_len, max_len = parse_target_length(target_input)

    if min_len is None:
        await cl.Message(
            content="⚠️ 숫자를 인식하지 못했습니다. 다시 시작해 주세요."
        ).send()
        return

    # 세션에 원본·목표 저장 (피드백 수정 시 재사용)
    cl.user_session.set("original_text", original_text)
    cl.user_session.set("target_min", min_len)
    cl.user_session.set("target_max", max_len)
    cl.user_session.set("revision_count", 0)

    # 초기 분량 조정 실행
    await run_initial_adjustment(original_text, min_len, max_len)

    # 피드백 루프 시작
    await revision_loop()


async def run_initial_adjustment(original_text: str, min_len: int, max_len: int):
    """초기 분량 조정 실행 및 결과 출력."""
    msg = cl.Message(content="")
    await msg.send()

    async def on_token(token: str):
        await msg.stream_token(token)

    async def on_status(status: str):
        msg.content = status + "\n\n"
        await msg.update()

    try:
        result = await controller.adjust_length(
            original_text=original_text,
            min_len=min_len,
            max_len=max_len,
            on_token=on_token,
            on_status=on_status,
        )
    except Exception as e:
        msg.content = f"오류 발생: {str(e)}"
        await msg.update()
        return

    # 세션에 현재 결과 저장
    cl.user_session.set("current_text", result["text"])

    # 결과 출력
    status_header = (
        "✅ **초기 조정 완료!**"
        if result["success"]
        else f"📊 **근사치 결과** (사유: {', '.join(result['errors'])})"
    )
    summary_lines = [
        f"- 목표: {min_len}~{max_len}자",
        f"- 결과: **{result['length']}자**",
        f"- 시도: {result['attempts']}회",
    ]

    await send_final_output(msg, status_header, summary_lines, result["text"])


async def revision_loop():
    """사용자 피드백을 받아 반복 수정하는 메인 루프."""
    while True:
        # 피드백 안내 메시지
        revision_count = cl.user_session.get("revision_count", 0)

        prompt_content = (
            f"✏️ **수정 요청을 자유롭게 입력해주세요**\n\n"
            f"예시:\n"
            f"- `첫 문단을 더 강렬하게 시작해줘`\n"
            f"- `두 번째 문단에 협업 경험을 더 강조해줘`\n"
            f"- `전체적으로 더 간결하게 다듬어줘`\n\n"
            f"완료하려면 **`완료`** 또는 **`끝`**을 입력하세요.\n"
            f"_(현재까지 수정 {revision_count}회)_"
        )

        res = await cl.AskUserMessage(
            content=prompt_content,
            timeout=300,
        ).send()

        if not res:
            await cl.Message(
                content="⏱️ 시간이 초과되어 작업을 마칩니다."
            ).send()
            return

        user_input = res['output'].strip()

        # 종료 조건 확인
        if user_input.lower() in EXIT_KEYWORDS:
            await cl.Message(
                content=(
                    f"✅ **작업을 마칩니다.**\n\n"
                    f"총 {revision_count}회 수정했습니다. 수고하셨어요! 🎉"
                )
            ).send()
            return

        # 피드백 수정 실행
        await run_revision(user_input)


async def run_revision(user_feedback: str):
    """사용자 피드백 기반 수정 실행."""
    original_text = cl.user_session.get("original_text")
    current_text = cl.user_session.get("current_text")
    min_len = cl.user_session.get("target_min")
    max_len = cl.user_session.get("target_max")
    revision_count = cl.user_session.get("revision_count", 0)

    if not current_text:
        await cl.Message(content="⚠️ 현재 결과가 없습니다. 처음부터 시작해주세요.").send()
        return

    msg = cl.Message(content="")
    await msg.send()

    async def on_token(token: str):
        await msg.stream_token(token)

    async def on_status(status: str):
        msg.content = status + "\n\n"
        await msg.update()

    try:
        result = await controller.revise_text(
            original_text=original_text,
            current_text=current_text,
            user_feedback=user_feedback,
            min_len=min_len,
            max_len=max_len,
            on_token=on_token,
            on_status=on_status,
        )
    except Exception as e:
        msg.content = f"오류 발생: {str(e)}"
        await msg.update()
        return

    # 세션 업데이트
    cl.user_session.set("current_text", result["text"])
    cl.user_session.set("revision_count", revision_count + 1)

    # 결과 출력
    status_header = (
        f"✏️ **수정 완료** (총 {revision_count + 1}회)"
        if result["success"]
        else f"⚠️ **수정 결과 (일부 검증 실패)**\n사유: {', '.join(result['errors'])}"
    )
    summary_lines = [
        f"- 수정 요청: _{user_feedback[:50]}{'...' if len(user_feedback) > 50 else ''}_",
        f"- 목표: {min_len}~{max_len}자",
        f"- 결과: **{result['length']}자**",
    ]

    await send_final_output(msg, status_header, summary_lines, result["text"])


async def send_final_output(msg, status_header: str, summary_lines: list,
                            body_text: str):
    """검증 결과·통계 + 본문을 두 메시지로 분리해 발송."""
    with_spaces = count_with_spaces(body_text)
    without_spaces = count_without_spaces(body_text)
    para_count = count_paragraphs(body_text)
    sentence_count = len(
        [s for s in re.split(r'[.!?]+', body_text) if s.strip()]
    )
    avg_sentence = with_spaces // max(sentence_count, 1)

    summary = "\n".join(summary_lines)

    stats_table = (
        f"| 항목 | 값 |\n"
        f"|---|---|\n"
        f"| 공백 포함 글자 수 | **{with_spaces}자** |\n"
        f"| 공백 제외 글자 수 | {without_spaces}자 |\n"
        f"| 문단 수 | {para_count}개 |\n"
        f"| 문장 수 | {sentence_count}개 |\n"
        f"| 평균 문장 길이 | {avg_sentence}자 |"
    )

    msg.content = (
        f"{status_header}\n"
        f"{summary}\n\n"
        f"### 📊 상세 통계\n"
        f"{stats_table}\n\n"
        f"⬇️ **자기소개서 본문은 아래 메시지에서 확인하세요.**"
    )
    await msg.update()

    body_message_content = f"## 📄 자기소개서\n\n{body_text}"
    await cl.Message(content=body_message_content).send()