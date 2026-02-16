"""퀴즈 생성 서비스"""
import random


def generate_quiz(words: list[dict], quiz_type: str = "A", all_words: list[dict] = None) -> list[dict]:
    """
    단어 리스트로부터 5지선다 퀴즈를 생성합니다.

    Args:
        words: 퀴즈 문제로 출제할 단어 목록
        quiz_type: "A" (영→한) 또는 "B" (한→영)
        all_words: 오답 후보 풀 (None이면 words와 동일)
    """
    if all_words is None:
        all_words = words

    if len(words) < 1:
        raise ValueError("퀴즈를 생성하려면 최소 1개 이상의 단어가 필요합니다.")
    if len(all_words) < 2:
        raise ValueError("오답 후보를 생성하려면 전체 단어가 2개 이상이어야 합니다.")

    shuffled_words = words.copy()
    random.shuffle(shuffled_words)

    quiz_list = []

    for target in shuffled_words:
        if quiz_type == "A":
            # 영어 단어 → 한국어 뜻 선택
            question = target["word"]
            answer = target["meaning"]
            pool_key = "meaning"
        else:
            # 한국어 뜻 → 영어 단어 선택
            question = target["meaning"]
            answer = target["word"]
            pool_key = "word"

        # 오답 후보 생성 (전체 단어 풀에서, 최대 4개)
        other_words = [w for w in all_words if w != target]
        num_distractors = min(4, len(other_words))
        distractors = random.sample(other_words, num_distractors)
        distractor_values = [d[pool_key] for d in distractors]

        # 선택지 구성 (정답 + 오답)
        choices = [answer] + distractor_values
        random.shuffle(choices)

        answer_index = choices.index(answer)

        quiz_list.append(
            {
                "question": question,
                "answer": answer,
                "choices": choices,
                "answer_index": answer_index,
            }
        )

    return quiz_list
