def count_with_spaces(text: str) -> int:
    # 텍스트의 전체 길이(공백 및 줄바꿈 포함)를 반환합니다.
    return len(text)


def count_without_spaces(text: str) -> int:
    # 띄어쓰기, 줄바꿈, 탭 기호를 모두 제거하여 순수 글자만 남깁니다.
    text_without_spaces = text.replace(" ", "").replace("\n", "").replace("\t", "")

    # 공백이 제거된 순수 텍스트의 길이를 반환합니다.
    return len(text_without_spaces)


def get_text_stats(text: str) -> dict:
    # 위 두 함수를 조합하여, 공백 포함/제외 수치를 한 번에 딕셔너리로 반환합니다.
    return {
        "with_spaces": count_with_spaces(text),
        "without_spaces": count_without_spaces(text)
    }