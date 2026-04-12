"""
Chainlit 기반 사용자 인터페이스.
실제 로직은 length_controller에 위임하고, 여기서는 UI 흐름만 담당.
"""

import re
import chainlit as cl
from dotenv import load_dotenv

from text_counter import count_with_spaces, count_without_spaces
from text_utils import parse_target_length, count_paragraphs
from length_controller import LengthController


load_dotenv()
controller = LengthController()


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

    await run_adjustment(original_text, min_len, max_len)


async def run_adjustment(original_text: str, min_len: int, max_len: int):
    """분량 조정 실행 및 결과 출력."""
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

    # 결과 출력
    if result["success"]:
        status_header = "✅ **검증 통과!**"
        summary_lines = [
            f"- 목표: {min_len}~{max_len}자",
            f"- 결과: **{result['length']}자** (여유 {max_len - result['length']}자)",
            f"- 시도: {result['attempts']}회",
        ]
    else:
        status_header = (
            f"📊 **근사치 결과** (사유: {', '.join(result['errors'])})"
        )
        summary_lines = [
            f"- 목표: {min_len}~{max_len}자",
            f"- 최종: **{result['length']}자**",
            f"- 시도: {result['attempts']}회",
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

    body_message_content = f"## 📄 완성된 자기소개서\n\n{body_text}"
    await cl.Message(content=body_message_content).send()