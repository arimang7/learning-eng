# 📖 English Vocab Master

이미지에서 영어 단어를 AI로 추출하고, Notion에 저장한 뒤, 퀴즈로 학습하는 Streamlit 웹 앱입니다.

---

## 🛠 Tech Stack

| 구분      | 기술                                                                                |
| --------- | ----------------------------------------------------------------------------------- |
| Language  | Python 3.10+                                                                        |
| Frontend  | Streamlit                                                                           |
| AI Engine | Google Gemini (gemini-flash)                                                        |
| Database  | Notion API                                                                          |
| Libraries | `google-generativeai`, `notion-client`, `pandas`, `Pillow`, `streamlit-autorefresh` |

---

## 📁 프로젝트 구조

```
learn_eng/
├── app.py                  # Streamlit 메인 앱 (UI, 탭, 퀴즈 로직)
├── config.py               # .env 환경변수 로더 및 검증
├── requirements.txt        # Python 의존성 목록
├── .env                    # API 키 설정 (git 제외)
├── .gitignore
└── services/
    ├── __init__.py
    ├── gemini_service.py   # Gemini API 이미지 분석 · 요약 생성
    ├── notion_service.py   # Notion DB CRUD (페이지 생성, 단어 저장/조회, 결과 업데이트)
    └── quiz_service.py     # 5지선다 퀴즈 생성 (Type A/B)
```

### 모듈별 역할

#### `app.py`

- **📸 단어 등록 탭**: 이미지 업로드 → Gemini 단어 추출 → Notion 저장
- **📝 퀴즈 탭**: 페이지 선택 → 30초 타이머 퀴즈 → 결과 Notion 반영

#### `services/gemini_service.py`

- `analyze_image(image_bytes)` — 이미지에서 `[{"word": "...", "meaning": "..."}]` JSON 추출
- `generate_summary(words)` — 단어 목록의 핵심 주제를 1줄 요약

#### `services/notion_service.py`

- `save_words(words, summary)` — 목차 DB에 새 행 + 페이지 내 단어 테이블(Word, Meaning, 결과) 생성
- `fetch_pages()` — 저장된 페이지 목록 조회
- `fetch_words(page_id)` — 특정 페이지의 단어 목록 조회 (결과 컬럼 포함)
- `update_word_results(page_id, results)` — 퀴즈 결과(✅/❌/⏰)를 Notion 테이블에 업데이트

#### `services/quiz_service.py`

- `generate_quiz(words, quiz_type, all_words)` — Type A(영→한) / Type B(한→영) 5지선다 퀴즈 생성

---

## ⚙️ 환경 설정

### 1. `.env` 파일 생성

프로젝트 루트에 `.env` 파일을 생성하고 아래 항목을 설정합니다:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here
```

| 변수                 | 설명                    | 발급 방법                                                                        |
| -------------------- | ----------------------- | -------------------------------------------------------------------------------- |
| `GEMINI_API_KEY`     | Google Gemini API 키    | [Google AI Studio](https://aistudio.google.com/)에서 발급                        |
| `GEMINI_MODEL`       | 사용할 Gemini 모델명    | 기본값: `gemini-flash-latest`                                                    |
| `NOTION_TOKEN`       | Notion Integration 토큰 | [Notion Developers](https://developers.notion.com/)에서 Integration 생성 후 발급 |
| `NOTION_DATABASE_ID` | Notion 데이터베이스 ID  | Notion DB 페이지 URL에서 추출 (32자리 hex)                                       |

### 2. Notion 데이터베이스 설정

1. Notion에서 **인라인 데이터베이스**를 생성합니다.
2. 컬럼 구성:
   - `날짜+순번` (제목, Title) — 자동 생성됨: `YYYY-MM-DD-순번-요약`
   - `요약` (텍스트, Rich Text) — AI가 생성한 주제 요약
3. 생성한 Integration을 해당 데이터베이스에 **연결(Connect)** 합니다.

---

## 🚀 실행 방법

### 1. 가상환경 생성 및 의존성 설치

```bash
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

### 2. 앱 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

---

## 📋 사용법

### 📸 단어 등록

1. **📸 단어 등록** 탭 선택
2. 영어 단어가 포함된 이미지를 **파일 업로드** 또는 **카메라 촬영**
3. **🔍 AI로 단어 추출하기** 클릭 → Gemini가 단어/뜻을 자동 추출
4. 추출 결과 확인 후 **💾 Notion에 저장하기** 클릭

### 📝 퀴즈

1. **📝 퀴즈** 탭 선택
2. 학습할 **페이지 선택** (Notion에서 불러옴)
3. **퀴즈 유형** 선택:
   - `A: 영→한` — 영어 단어를 보고 한국어 뜻 선택
   - `B: 한→영` — 한국어 뜻을 보고 영어 단어 선택
4. **출제 범위** 선택:
   - `전체` — 모든 단어 출제
   - `오답만` — 이전에 틀린 단어(❌/⏰)만 재출제
5. **🚀 퀴즈 시작!** 클릭

#### 퀴즈 규칙

- 문제당 **30초 제한시간** (10초 이하 빨간색 경고)
- 시간 초과 시 자동으로 다음 문제로 이동
- 정답/오답 표시 후 **1.5초 뒤 자동 다음 문제**
- 퀴즈 완료 시 **최종 점수** + **틀린 단어 복습** 표시
- 결과(✅/❌/⏰)가 **Notion 테이블에 자동 반영**

---

## 📊 Notion 데이터 구조

```
[영어 단어 퀴즈 DB]
├── 2026-02-16-01-동물 관련 단어  |  요약: 동물 관련 단어
│   └── 📚 단어 목록 (테이블 블록)
│       | Word    | Meaning | 결과 |
│       |---------|---------|------|
│       | cat     | 고양이   | ✅   |
│       | dog     | 개      | ❌   |
│       | bird    | 새      | ⏰   |
├── 2026-02-16-02-음식 관련 단어  |  요약: 음식 관련 단어
│   └── ...
```

| 결과 | 의미      |
| ---- | --------- |
| ✅   | 정답      |
| ❌   | 오답      |
| ⏰   | 시간 초과 |
| `-`  | 미응시    |
