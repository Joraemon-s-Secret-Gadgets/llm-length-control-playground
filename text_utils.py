"""
한국어 자기소개서 텍스트 후처리 유틸리티.
- 마침표 자동 복구
- 문단 구조 정비
- 문장 단위 정밀 트리밍
- 사실 날조(숫자) 검증
"""

import re
from text_counter import count_with_spaces


def fix_korean_sentence_endings(text: str) -> str:
    """
    LLM이 글자 수 아끼려고 한국어 문장 종결부 뒤 마침표를 생략한 경우 복구.
    '~니다' / '~요' 종결 뒤 공백+다음 문장이 이어지면 마침표 삽입.
    """
    text = re.sub(
        r'(?<=[가-힣])(니다)(?=\s+[^\s.,!?)\]}])',
        r'\1.',
        text,
    )
    text = re.sub(
        r'(?<=[가-힣])(해요|이에요|예요|드려요|아요|어요)(?=\s+[^\s.,!?)\]}])',
        r'\1.',
        text,
    )
    text = re.sub(r'(?<=[가-힣])(니다|해요|이에요|예요)\s*$', r'\1.', text)
    return text


def count_paragraphs(text: str) -> int:
    """빈 줄(\\n\\n)로 구분되는 문단 개수."""
    paras = [p for p in re.split(r'\n\s*\n', text.strip()) if p.strip()]
    return len(paras)


def ensure_paragraphs(text: str, sentences_per_paragraph: int = 3) -> str:
    """
    문단 구분이 부족하면 자동으로 빈 줄 삽입.
    이미 3개 이상의 문단이 있으면 그대로 반환.
    """
    if count_paragraphs(text) >= 3:
        return text

    flat = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?])\s+', flat)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= sentences_per_paragraph:
        return text

    paragraphs = []
    for i in range(0, len(sentences), sentences_per_paragraph):
        group = sentences[i:i + sentences_per_paragraph]
        paragraphs.append(" ".join(group))

    return "\n\n".join(paragraphs)


def smart_trim(text: str, min_len: int, max_len: int) -> str:
    """
    문단·문장 구조를 보존하며 max_len 이하로 정밀 트리밍.
    이미 범위 안이면 그대로 반환.
    """
    current = count_with_spaces(text)

    if min_len <= current <= max_len:
        return text

    if current < min_len:
        return text  # 확장은 LLM 재시도 몫

    paragraphs = re.split(r'\n\s*\n', text.strip())
    kept_paras = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        sentences = re.split(r'(?<=[.!?])\s+', para)
        kept_sentences = []

        for s in sentences:
            s = s.strip()
            if not s:
                continue
            tentative = "\n\n".join(
                kept_paras + [" ".join(kept_sentences + [s])]
            )
            if count_with_spaces(tentative) <= max_len:
                kept_sentences.append(s)
            else:
                break

        if kept_sentences:
            kept_paras.append(" ".join(kept_sentences))

    result = "\n\n".join(kept_paras) if kept_paras else text
    return result


def extract_numbers(text: str) -> set:
    """
    원문에서 숫자 토큰 추출. 사실 날조 검증용.
    '3개월', '5명', '20%', '1000만원' 같은 패턴 감지.
    """
    pattern = r'\d+\s*(?:개월|년|일|주|시간|분|명|인|개|%|만원|원|억|천|배|등|위|회|차)?'
    matches = re.findall(pattern, text)
    return set(m.replace(" ", "") for m in matches if m.strip())


def detect_fabricated_numbers(original_nums: set, generated_text: str) -> list:
    """
    생성 결과에 원문에 없던 숫자가 나타났는지 검증.
    연도(4자리)와 한 자리 숫자는 false positive 위험이 있어 제외.
    """
    generated_nums = extract_numbers(generated_text)
    fabricated = generated_nums - original_nums
    filtered = [
        n for n in fabricated
        if not (n.isdigit() and (len(n) == 4 or int(n) < 10))
    ]
    return filtered


def parse_target_length(input_str: str) -> tuple:
    """
    사용자 입력을 (min_len, max_len)으로 변환.
    - "500~550" → (500, 550)
    - "1000" → (990, 1000)
    """
    match = re.search(r'(\d+)\s*[-~]\s*(\d+)', input_str)
    if match:
        num1, num2 = int(match.group(1)), int(match.group(2))
        return min(num1, num2), max(num1, num2)

    nums = re.findall(r'\d+', input_str)
    if nums:
        max_len = int(nums[0])
        buffer = max(10, int(max_len * 0.01))
        min_len = max(1, max_len - buffer)
        return min_len, max_len

    return None, None