"""Notion API 연동 서비스"""
from datetime import datetime
from notion_client import Client

from config import NOTION_TOKEN, NOTION_DATABASE_ID


def _get_client() -> Client:
    """Notion 클라이언트 생성"""
    return Client(auth=NOTION_TOKEN)


def _get_next_seq(client: Client) -> int:
    """오늘 날짜의 다음 순번을 반환합니다."""
    today = datetime.now().strftime("%Y-%m-%d")

    results = client.databases.query(
        database_id=NOTION_DATABASE_ID,
        filter={
            "property": "날짜+순번",
            "title": {"starts_with": today},
        },
        sorts=[
            {"property": "날짜+순번", "direction": "descending"}
        ],
    )

    if not results["results"]:
        return 1

    last_title = (
        results["results"][0]["properties"]["날짜+순번"]["title"][0]["plain_text"]
    )
    try:
        last_seq = int(last_title.split("-")[3])
        return last_seq + 1
    except (IndexError, ValueError):
        return 1


def save_words(words: list[dict], summary: str) -> str:
    """Notion DB에 새 페이지를 생성하고, 페이지 내부에 3열 단어 테이블을 추가합니다."""
    client = _get_client()
    today = datetime.now().strftime("%Y-%m-%d")
    seq = _get_next_seq(client)
    page_title = f"{today}-{seq:02d}-{summary}"

    new_page = client.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "날짜+순번": {
                "title": [{"text": {"content": page_title}}]
            },
            "요약": {
                "rich_text": [{"text": {"content": summary}}]
            },
        },
    )

    page_id = new_page["id"]

    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📚 단어 목록"}}]
            },
        },
        {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": 3,
                "has_column_header": True,
                "has_row_header": False,
                "children": [
                    {
                        "type": "table_row",
                        "table_row": {
                            "cells": [
                                [{"type": "text", "text": {"content": "Word"}}],
                                [{"type": "text", "text": {"content": "Meaning"}}],
                                [{"type": "text", "text": {"content": "결과"}}],
                            ]
                        },
                    },
                ]
                + [
                    {
                        "type": "table_row",
                        "table_row": {
                            "cells": [
                                [{"type": "text", "text": {"content": w["word"]}}],
                                [{"type": "text", "text": {"content": w["meaning"]}}],
                                [{"type": "text", "text": {"content": "-"}}],
                            ]
                        },
                    }
                    for w in words
                ],
            },
        },
    ]

    client.blocks.children.append(block_id=page_id, children=children)
    return page_title


def fetch_pages() -> list[dict]:
    """목차 DB에서 페이지 목록을 조회합니다."""
    client = _get_client()

    results = client.databases.query(
        database_id=NOTION_DATABASE_ID,
        sorts=[{"property": "날짜+순번", "direction": "descending"}],
    )

    pages = []
    for page in results["results"]:
        title_prop = page["properties"]["날짜+순번"]["title"]
        summary_prop = page["properties"]["요약"]["rich_text"]

        title = title_prop[0]["plain_text"] if title_prop else "(제목 없음)"
        summary = summary_prop[0]["plain_text"] if summary_prop else ""

        pages.append({"id": page["id"], "title": title, "summary": summary})

    return pages


def fetch_words(page_id: str) -> list[dict]:
    """특정 페이지의 테이블 블록에서 단어 목록을 추출합니다 (결과 컬럼 포함)."""
    client = _get_client()

    blocks = client.blocks.children.list(block_id=page_id)
    words = []

    for block in blocks["results"]:
        if block["type"] == "table":
            table_width = block.get("table", {}).get("table_width", 2)
            table_rows = client.blocks.children.list(block_id=block["id"])

            for i, row in enumerate(table_rows["results"]):
                if i == 0:
                    continue

                if row["type"] == "table_row":
                    cells = row["table_row"]["cells"]
                    if len(cells) >= 2:
                        word_text = cells[0][0]["plain_text"] if cells[0] else ""
                        meaning_text = cells[1][0]["plain_text"] if cells[1] else ""
                        result_text = ""
                        if table_width >= 3 and len(cells) >= 3 and cells[2]:
                            result_text = cells[2][0]["plain_text"] if cells[2] else ""

                        if word_text and meaning_text:
                            words.append({
                                "word": word_text,
                                "meaning": meaning_text,
                                "result": result_text,
                            })

    return words


def update_word_results(page_id: str, results: list[dict]) -> None:
    """
    퀴즈 결과를 Notion 페이지의 단어 테이블에 업데이트합니다.

    Args:
        page_id: Notion 페이지 ID
        results: [{"word": "apple", "result": "✅"}, ...]
    """
    client = _get_client()
    result_map = {r["word"]: r["result"] for r in results}

    blocks = client.blocks.children.list(block_id=page_id)

    for block in blocks["results"]:
        if block["type"] == "table":
            table_width = block.get("table", {}).get("table_width", 2)
            table_rows = client.blocks.children.list(block_id=block["id"])

            for i, row in enumerate(table_rows["results"]):
                if i == 0:
                    continue

                if row["type"] == "table_row":
                    cells = row["table_row"]["cells"]
                    word = cells[0][0]["plain_text"] if cells[0] else ""

                    if word in result_map:
                        emoji = result_map[word]
                        if table_width >= 3:
                            new_cells = [
                                cells[0],
                                cells[1],
                                [{"type": "text", "text": {"content": emoji}}],
                            ]
                        else:
                            meaning = cells[1][0]["plain_text"] if cells[1] else ""
                            new_cells = [
                                cells[0],
                                [{"type": "text", "text": {"content": f"{meaning} {emoji}"}}],
                            ]

                        client.blocks.update(
                            block_id=row["id"],
                            table_row={"cells": new_cells},
                        )
            break
