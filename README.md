# LLM Length Control Playground

> 작성된 자기소개서를 원하는 글자 수에 맞게 **정밀하게 재조정**하는 LLM 기반 실험 저장소

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Chainlit](https://img.shields.io/badge/Chainlit-F15A24?style=for-the-badge&logo=chainlit&logoColor=white)](https://chainlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

---

## 1. 프로젝트 개요

이 저장소는 **이미 작성된 자기소개서를 사용자가 지정한 글자 수(공백 포함) 범위에 정밀하게 맞추는 기능**을 실험하는 프로젝트입니다.

LLM은 토큰 단위로 생성하기 때문에 한국어 글자 수를 직접 인지하지 못합니다. "1000자로 써줘"라고 지시해도 실제 결과는 700~1300자 사이에서 랜덤하게 나옵니다. 이 저장소는 다음 질문에 답합니다.

- 프롬프트 엔지니어링만으로 글자 수를 어느 정도 맞출 수 있는가?
- LLM 생성 결과를 후처리(트리밍)로 정밀 보정할 수 있는가?
- 분량 조절 과정에서 **사실 날조 없이** 문장을 재구성할 수 있는가?

---

## 2. 프로젝트 배경

자기소개서는 기업마다 요구 분량이 다릅니다. 500자, 700자, 1000자, 1500자 등 문항별 상한이 엄격하게 정해져 있고, 한 글자만 넘겨도 지원 자격이 박탈되는 경우가 많습니다.

반면 LLM은:

1. 토큰 단위 생성 구조상 **정확한 글자 수를 인지하지 못함**
2. "N자로 써줘" 지시를 정확히 수행하지 못함
3. 분량을 맞추려고 재시도하면 **문장부호를 생략**하거나 **사실을 날조**하는 경향

본 프로젝트는 이 문제를 **프롬프트 설계 + 파이썬 후처리 하이브리드 구조**로 해결하는 방식을 실험합니다.

---

## 3. 핵심 접근 방식

### 1단계: LLM에 "넉넉히" 쓰게 지시
- 목표치의 +15% 길게 생성하도록 프롬프트 설계
- 글자 수 맞추는 책임은 LLM이 아닌 파이썬이 진다

### 2단계: 파이썬 후처리 파이프라인
1. 한국어 문장 종결부 마침표 자동 복구
2. 문단 구조 자동 정비 (STAR 구조 기반)
3. 문장 단위 정밀 트리밍
4. 사실 날조 검증 (원문 대비 신규 숫자 탐지)

### 3단계: 검증 실패 시 재시도
- temperature를 점진적으로 상승시켜 다양성 확보
- 최대 2회까지만 재시도 (과도한 재시도로 인한 품질 저하 방지)

---

## 4. 현재 단계

현재는 **프로토타입 구현 단계**입니다.

### 구현 완료
- [x] Chainlit 기반 사용자 인터페이스
- [x] 글자 수 목표 입력 파싱 (단일 숫자 / 범위 모두 지원)
- [x] LLM 생성 + 후처리 파이프라인
- [x] 한국어 마침표 자동 복구
- [x] 문단 구조 자동 정비
- [x] 문장 단위 정밀 트리밍
- [x] 상세 통계 출력 (글자 수, 문단 수, 평균 문장 길이)

### 향후 과제
- [ ] 코드 모듈 분리 (length_controller / text_utils / prompts)
- [ ] 사실 날조 검증 로직 추가
- [ ] 팀 메인 서비스와 통합 인터페이스 설계
- [ ] 다양한 모델 비교 실험 (gpt-4o / gpt-4o-mini)
- [ ] 프롬프트 A/B 테스트

---

## 5. 기술 스택

### Environment
- Python 3.10+
- Chainlit 기반 UI

### Library
- `chainlit` — 챗봇 인터페이스
- `openai` (AsyncOpenAI) — LLM 호출
- `python-dotenv` — 환경 변수 관리

### Model
- `gpt-4o` (현재)

---

## 6. 팀 프로젝트 내 포지션

본 저장소는 팀 프로젝트 **JobPocket**의 독립 실험 모듈이며,
**사후(post-generation) 글자 수 정밀 제어 기능**을 담당합니다.

최종 서비스에서 사용자가 이미 작성된 자소서를 다른 분량으로 재조정하고자 할 때,
본 모듈이 호출됩니다.

- 관련 Jira 이슈: **S3P-38**
- 카테고리: Prompt Engineering

---

## 7. 실행 방법

```bash
pip install -r requirements.txt
chainlit run app.py
```

> 상세 실행 가이드 및 환경 변수 설정은 코드 업로드 이후 업데이트 예정입니다.

---

## 8. License

MIT License
