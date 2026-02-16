"""환경 변수 설정 모듈"""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


def validate_config():
    """필수 환경 변수가 설정되어 있는지 확인"""
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not NOTION_TOKEN:
        missing.append("NOTION_TOKEN")
    if not NOTION_DATABASE_ID:
        missing.append("NOTION_DATABASE_ID")

    if missing:
        raise EnvironmentError(
            f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing)}\n"
            f".env 파일을 확인해주세요."
        )
