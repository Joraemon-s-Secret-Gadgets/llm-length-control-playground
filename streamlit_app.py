"""
Streamlit 기반 자기소개서 글자수 편집 UI.
Chainlit 버전(app.py)과 동일한 기능을 Streamlit으로 구현.
"""

import asyncio
import streamlit as st
from dotenv import load_dotenv

from llm_length_control import (
    LengthController,
    count_paragraphs,
    count_with_spaces,
    count_without_spaces,
    TextTooShortError,
    InvalidTargetLengthError,
    EmptyTextError,
)

# === 환경 설정 ===
load_dotenv()

st.set_page_config(
    page_title="자기소개서 글자수 편집기",
    page_icon="📝",
    layout="wide",
)

# === 세션 상태 초기화 ===
if "original_text" not in st.session_state:
    st.session_state.original_text = ""
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "target_min" not in st.session_state:
    st.session_state.target_min = 950
if "target_max" not in st.session_state:
    st.session_state.target_max = 1000
if "revision_count" not in st.session_state:
    st.session_state.revision_count = 0
if "controller" not in st.session_state:
    st.session_state.controller = LengthController()


# === 비동기 실행 헬퍼 ===
def run_async(coro):
    """Streamlit에서 async 함수 실행을 위한 래퍼."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# === UI 시작 ===
st.title("📝 자기소개서 글자수 편집기")
st.caption("작성된 자기소개서를 원하는 글자 수에 정밀하게 맞춰드립니다.")

# === 1단계: 원본 + 목표 입력 ===
with st.expander("📄 1단계: 자기소개서 입력", expanded=True):
    col1, col2 = st.columns([3, 1])

    with col1:
        original_text = st.text_area(
            "자기소개서 원본",
            height=300,
            placeholder="여기에 자기소개서 원본을 붙여넣어 주세요...",
            value=st.session_state.original_text,
        )
        st.session_state.original_text = original_text

    with col2:
        if original_text:
            current_len = count_with_spaces(original_text)
            st.metric("현재 글자 수", f"{current_len}자", help="공백 포함")

        # 목표 글자수 입력
        target = st.number_input(
            "목표 글자수",
            min_value=100,
            max_value=5000,
            value=1000,
            step=50,
            help="최대 허용 글자수 (이 값을 초과하지 않음)",
        )

        # 허용 오차 입력 (기본값: 목표의 10%, 최소 10자)
        default_buffer = max(10, int(target * 0.10))
        buffer = st.number_input(
            "허용 오차 (자)",
            min_value=1,
            max_value=500,
            value=default_buffer,
            step=10,
            help="목표의 10%가 기본값. 엄격하게 맞추려면 낮추세요 (초과는 불가)",
        )

        # 범위 자동 계산 표시
        min_len = max(1, target - buffer)
        max_len = target
        st.info(f"💡 결과 범위: **{min_len} ~ {max_len}자**")

        # 분량 조정 버튼
        if st.button("🚀 분량 조정 시작", type="primary", use_container_width=True):
            if not original_text.strip():
                st.error("⚠️ 자기소개서 원본을 입력해주세요.")
            elif min_len < 1:
                st.error("⚠️ 허용 오차가 너무 큽니다. 결과 범위가 0자 이하입니다.")
            else:
                st.session_state.target_min = min_len
                st.session_state.target_max = max_len
                st.session_state.revision_count = 0

                # 분량 조정 실행
                with st.spinner(f"⚙️ {min_len}~{max_len}자로 조정 중..."):
                    try:
                        result = run_async(
                            st.session_state.controller.adjust_length(
                                original_text=original_text,
                                min_len=min_len,
                                max_len=max_len,
                            )
                        )
                        st.session_state.current_result = result
                        st.rerun()
                    except TextTooShortError as e:
                        st.error(f"⚠️ {str(e)}")
                    except InvalidTargetLengthError as e:
                        st.error(f"⚠️ {str(e)}")
                    except EmptyTextError as e:
                        st.error(f"⚠️ {str(e)}")
                    except Exception as e:
                        st.error(f"❌ 오류: {str(e)}")

# === 2단계: 결과 표시 ===
if st.session_state.current_result is not None:
    result = st.session_state.current_result

    st.divider()

    # 결과 헤더
    if result.success:
        st.success(
            f"✅ **조정 완료!** {result.length}자 "
            f"(목표: {st.session_state.target_min}~{st.session_state.target_max}자)"
        )
    else:
        st.warning(
            f"⚠️ **근사치 결과** — {result.length}자 "
            f"(사유: {', '.join(result.errors)})"
        )

    # 2열 레이아웃: 결과 본문 + 통계
    col_text, col_stats = st.columns([3, 1])

    with col_text:
        st.subheader("📄 조정된 자기소개서")
        st.text_area(
            "본문",
            value=result.text,
            height=400,
            label_visibility="collapsed",
        )

    with col_stats:
        st.subheader("📊 통계")
        with_spaces = count_with_spaces(result.text)
        without_spaces = count_without_spaces(result.text)
        para_count = count_paragraphs(result.text)

        # 목표 대비 차이 계산
        target_max = st.session_state.target_max
        diff = with_spaces - target_max
        diff_pct = (with_spaces / target_max) * 100

        st.metric(
            "공백 포함",
            f"{with_spaces}자",
            delta=f"{diff:+d}자 ({diff_pct:.1f}%)",
            delta_color="off" if abs(diff) <= 5 else "inverse",
        )
        st.metric("공백 제외", f"{without_spaces}자")
        st.metric("문단 수", f"{para_count}개")

        # attempts는 AdjustmentResult만 있음 (RevisionResult엔 없음)
        if hasattr(result, 'attempts'):
            st.metric(
                "LLM 시도",
                f"{result.attempts}회",
                help="LLM 호출 횟수 (1=한 번에 성공)"
            )

        st.metric("수정 요청", f"{st.session_state.revision_count}회")

    # === 3단계: 피드백 수정 ===
    st.divider()
    st.subheader("✏️ 피드백으로 수정하기")
    st.caption("자연어로 수정 요청을 입력하면 AI가 반영해서 다시 작성합니다.")

    feedback = st.text_input(
        "수정 요청",
        placeholder="예: 첫 문단을 더 강렬하게 시작해줘 / 협업 경험을 더 강조해줘",
        key="feedback_input",
    )

    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        revise_clicked = st.button("✏️ 수정하기", type="primary", use_container_width=True)
    with col_btn2:
        reset_clicked = st.button("🔄 처음부터 다시", use_container_width=True)

    if revise_clicked:
        if not feedback.strip():
            st.error("⚠️ 수정 요청을 입력해주세요.")
        else:
            with st.spinner(f'✏️ 피드백 반영 중: "{feedback[:30]}..."'):
                try:
                    revision = run_async(
                        st.session_state.controller.revise_text(
                            original_text=st.session_state.original_text,
                            current_text=result.text,
                            user_feedback=feedback,
                            min_len=st.session_state.target_min,
                            max_len=st.session_state.target_max,
                        )
                    )
                    # RevisionResult를 AdjustmentResult 속성에 덮어쓰기
                    st.session_state.current_result.text = revision.text
                    st.session_state.current_result.length = revision.length
                    st.session_state.current_result.success = revision.success
                    st.session_state.current_result.errors = revision.errors
                    st.session_state.revision_count += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 오류: {str(e)}")

    if reset_clicked:
        st.session_state.current_result = None
        st.session_state.revision_count = 0
        st.rerun()