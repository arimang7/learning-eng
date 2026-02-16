"""Gemini AI 이미지 분석 서비스"""
import json
import google.generativeai as genai
from PIL import Image
import io

from config import GEMINI_API_KEY, GEMINI_MODEL


def _configure():
    """Gemini API 초기화"""
    genai.configure(api_key=GEMINI_API_KEY)


def analyze_image(image_bytes: bytes) -> list[dict]:
    """
    이미지에서 영어 단어와 한국어 뜻을 추출합니다.

    Args:
        image_bytes: 업로드된 이미지의 바이트 데이터

    Returns:
        [{"word": "apple", "meaning": "사과"}, ...] 형태의 리스트
    """
    _configure()

    model = genai.GenerativeModel(GEMINI_MODEL)
    image = Image.open(io.BytesIO(image_bytes))

    prompt = """이 이미지에서 영어 단어와 한국어 뜻을 추출해주세요.

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.
[
  {"word": "영어단어", "meaning": "한국어뜻"},
  {"word": "영어단어", "meaning": "한국어뜻"}
]

만약 이미지에서 영어 단어를 찾을 수 없으면 빈 배열 []을 반환하세요."""

    try:
        response = model.generate_content([prompt, image])
        text = response.text.strip()

        # JSON 블록 마커 제거
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        words = json.loads(text)

        if not isinstance(words, list):
            raise ValueError("응답이 리스트 형식이 아닙니다.")

        return words

    except json.JSONDecodeError:
        raise ValueError(
            "Gemini 응답을 JSON으로 파싱할 수 없습니다. "
            "이미지에 영어 단어가 명확하게 포함되어 있는지 확인해주세요."
        )
    except Exception as e:
        raise RuntimeError(f"이미지 분석 중 오류가 발생했습니다: {str(e)}")


def generate_summary(words: list[dict]) -> str:
    """
    단어 목록의 핵심 주제를 1줄로 요약합니다.

    Args:
        words: [{"word": "...", "meaning": "..."}, ...] 형태의 리스트

    Returns:
        요약 문자열 (예: "동물 관련 단어")
    """
    _configure()

    model = genai.GenerativeModel(GEMINI_MODEL)
    word_list = ", ".join([w["word"] for w in words])

    prompt = f"""다음 영어 단어들의 공통 주제를 한국어로 짧게 요약해주세요 (10자 이내).
단어 목록: {word_list}

요약만 출력하세요. 예: "동물 관련 단어", "음식 관련 단어", "일상 회화 단어"
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip().strip('"').strip("'")
    except Exception:
        return "단어 모음"
