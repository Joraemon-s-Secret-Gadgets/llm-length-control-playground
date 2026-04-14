# LLM Length Control Playground

> 작성된 자기소개서를 원하는 글자 수에 맞게 **정밀하게 재조정**하고, **사용자 피드백 기반으로 대화형 수정**까지 지원하는 LLM 기반 패키지

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Chainlit](https://img.shields.io/badge/Chainlit-F15A24?style=for-the-badge&logo=chainlit&logoColor=white)](https://chainlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

---

## 1. 프로젝트 개요

이 패키지는 **이미 작성된 자기소개서를 사용자가 지정한 글자 수(공백 포함) 범위에 정밀하게 맞추는 기능**과 **자연어 피드백 기반의 대화형 수정 기능**을 제공합니다.

LLM은 토큰 단위로 생성하기 때문에 한국어 글자 수를 직접 인지하지 못합니다. "1000자로 써줘"라고 지시해도 실제 결과는 700~1300자 사이에서 랜덤하게 나옵니다. 이 패키지는 다음 질문에 답합니다.

- 프롬프트 엔지니어링만으로 글자 수를 어느 정도 맞출 수 있는가?
- LLM 생성 결과를 후처리(트리밍)로 정밀 보정할 수 있는가?
- 분량 조절 과정에서 **사실 날조 없이** 문장을 재구성할 수 있는가?
- 한 번의 결과로 끝나지 않고 **사용자가 자연어로 수정 요청**을 할 수 있는가?

---

## 2. 빠른 시작 (Quick Start)

### 설치

```bash
pip install -r requirements.txt
```

### `.env` 파일 생성

```env
OPENAI_API_KEY=your_api_key_here
```

### 데모 앱 실행 (Chainlit UI)

```bash
chainlit run app.py -w
```

브라우저가 자동으로 열리며 `http://localhost:8000`에서 사용 가능합니다.

### 라이브러리로 사용 (다른 프로젝트에서)

```python
from llm_length_control import LengthController

controller = LengthController()

# 분량 조정
result = await controller.adjust_length(
    original_text="당신의 자기소개서 원본...",
    min_len=790,
    max_len=800,
)

if result.success:
    print(f"✅ {result.length}자로 조정 완료")
    print(result.text)
else:
    print(f"⚠️ {result.errors}")
```

---

## 3. 주요 기능

### 🎯 정밀 분량 제어
- 목표 글자수 ±1% 정확도
- 단일값(`800`) 또는 범위(`790~800`) 모두 지원

### 💬 대화형 피드백 수정
초기 결과에 만족하지 못하면 자연어로 수정 요청 가능:

```python
# 수정 요청
revision = await controller.revise_text(
    original_text=original,
    current_text=result.text,
    user_feedback="첫 문단을 더 강렬하게 시작해줘",
    min_len=790,
    max_len=800,
)
```

### 🛡️ 사실 날조 방지
- 원문에 없는 수치/도구/경험 자동 검출
- STAR 구조 강제로 논리적 흐름 유지

### 🔧 명확한 에러 처리

```python
from llm_length_control import (
    LengthController,
    TextTooShortError,
    InvalidTargetLengthError,
    EmptyTextError,
)

try:
    result = await controller.adjust_length(...)
except TextTooShortError as e:
    print(f"원문이 너무 짧음: {e}")
except InvalidTargetLengthError as e:
    print(f"잘못된 목표 글자수: {e}")
except EmptyTextError as e:
    print(f"빈 텍스트: {e}")
```

---

## 4. 핵심 접근 방식

### 1단계: LLM에 "넉넉히" 쓰게 지시
- 목표치의 **+15%** 길게 생성하도록 프롬프트 설계
- 글자 수 맞추는 책임은 LLM이 아닌 파이썬이 진다

### 2단계: 파이썬 후처리 파이프라인
1. 한국어 문장 종결부 마침표 자동 복구
2. 문단 구조 자동 정비 (STAR 구조 기반)
3. 문장 단위 정밀 트리밍
4. 사실 날조 검증 (원문 대비 신규 숫자 탐지)

### 3단계: 검증 실패 시 재시도
- temperature를 점진적으로 상승시켜 다양성 확보
- 최대 2회까지만 재시도

### 4단계: (옵션) 사용자 피드백 기반 수정
- 자연어 피드백을 받아 최소 침습적 수정
- 원본 사실 보존 + 목표 글자수 유지

---

## 5. 프로젝트 구조

```
llm-length-control-playground/
├── llm_length_control/         # 메인 패키지 (라이브러리)
│   ├── __init__.py             # 진입점 (외부 노출 API)
│   ├── controller.py           # 핵심 컨트롤러 (LengthController)
│   ├── prompts.py              # 시스템 프롬프트 + 빌더 함수
│   ├── text_utils.py           # 후처리 유틸리티
│   ├── text_counter.py         # 글자 수 계산
│   ├── types.py                # 데이터 클래스 (AdjustmentResult)
│   └── exceptions.py           # 예외 클래스
│
├── app.py                      # Chainlit 데모 앱
├── chainlit.md                 # 챗봇 환영 화면
├── requirements.txt            # 의존성
├── README.md                   # 이 파일
└── .env                        # API 키 (gitignore)
```

---

## 6. API 참조

### `LengthController`

분량 재조정 컨트롤러.

#### `adjust_length(original_text, min_len, max_len, on_token=None, on_status=None) -> AdjustmentResult`

원문을 목표 글자수 범위로 재조정합니다.

**Args:**
- `original_text`: 재조정할 원본 자소서
- `min_len`: 최소 글자 수 (공백 포함)
- `max_len`: 최대 글자 수 (공백 포함)
- `on_token`: 토큰 스트리밍 콜백 (UI 통합용, 선택)
- `on_status`: 상태 메시지 콜백 (UI 통합용, 선택)

**Returns:** `AdjustmentResult`

**Raises:**
- `EmptyTextError`: 원문이 비어있을 때
- `InvalidTargetLengthError`: 목표 글자수가 잘못됐을 때
- `TextTooShortError`: 원문이 목표치의 30% 미만일 때

#### `revise_text(original_text, current_text, user_feedback, min_len, max_len, on_token=None, on_status=None) -> RevisionResult`

사용자 피드백을 반영해 기존 결과를 수정합니다.

### `AdjustmentResult` / `RevisionResult`

분량 조정 결과 데이터 클래스.

**Attributes:**
- `text` (str): 조정된 자소서 본문
- `length` (int): 최종 글자 수
- `success` (bool): 검증 통과 여부
- `attempts` (int): 시도 횟수 (AdjustmentResult만)
- `errors` (List[str]): 검증 실패 사유

---

## 7. 기술 스택

- **Python** 3.10+
- **Chainlit** — 챗봇 UI
- **OpenAI** (`gpt-4o`) — LLM 호출
- **python-dotenv** — 환경 변수 관리

---

## 8. 팀 프로젝트 내 포지션

본 저장소는 팀 프로젝트 **JobPocket**의 독립 실험 모듈이며, **사후(post-generation) 글자 수 정밀 제어 기능**을 담당합니다.

최종 서비스에서 사용자가 이미 작성된 자소서를 다른 분량으로 재조정하고자 할 때, 본 모듈이 호출됩니다.

- **관련 Jira 이슈:** S3P-38
- **카테고리:** Prompt Engineering

---

## 9. 향후 과제

- [ ] 다양한 모델 비교 실험 (gpt-4o vs gpt-4o-mini)
- [ ] 프롬프트 A/B 테스트
- [ ] before/after 실험 결과 정리
- [ ] 팀 메인 서비스 통합 인터페이스 설계
- [ ] Streamlit 버전 추가 (선택)

---

## 10. License

MIT License