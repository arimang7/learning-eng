"""English Vocab Master — Streamlit + Notion + Gemini 영어 단어 학습 앱"""
import time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from streamlit_autorefresh import st_autorefresh

from config import validate_config
from services import gemini_service, notion_service, quiz_service

# ──────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="English Vocab Master",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# 커스텀 CSS
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .sub-header {
        text-align: center;
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }

    .score-card h1 {
        font-size: 3rem;
        margin: 0;
    }

    .correct-answer {
        padding: 0.8rem 1.2rem;
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border-left: 4px solid #28a745;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #155724;
        font-size: 1.1rem;
    }

    .wrong-answer {
        padding: 0.8rem 1.2rem;
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        border-left: 4px solid #dc3545;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #721c24;
        font-size: 1.1rem;
    }

    .timeout-answer {
        padding: 0.8rem 1.2rem;
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border-left: 4px solid #ffc107;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #856404;
        font-size: 1.1rem;
    }

    .word-card {
        background: linear-gradient(135deg, #f8f9ff 0%, #e8ecff 100%);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #e0e3ff;
        margin-bottom: 1rem;
    }

    .word-card h2 {
        color: #4c51bf;
        margin: 0;
    }

    .timer-normal {
        text-align: center; padding: 0.8rem; border-radius: 12px;
        background: linear-gradient(135deg, #e8ecff, #f0f4ff);
        font-size: 1.5rem; font-weight: 700; color: #667eea;
    }

    .timer-warning {
        text-align: center; padding: 0.8rem; border-radius: 12px;
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        font-size: 1.5rem; font-weight: 700; color: #dc3545;
        animation: pulse 1s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 2rem;
        border-radius: 10px 10px 0 0;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 환경 변수 검증
# ──────────────────────────────────────────────
try:
    validate_config()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

# ──────────────────────────────────────────────
# Auto-refresh (퀴즈 진행 중에만 1초마다)
# ──────────────────────────────────────────────
if "quiz_state" in st.session_state:
    qs_ref = st.session_state["quiz_state"]
    if not qs_ref.get("completed", True):
        st_autorefresh(interval=1000, key="quiz_refresh")

# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown('<div class="main-header">📖 English Vocab Master</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">이미지에서 영어 단어를 추출하고, 퀴즈로 학습하세요!</div>',
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 탭 구성
# ──────────────────────────────────────────────
tab_register, tab_quiz = st.tabs(["📸 단어 등록", "📝 퀴즈"])

# 퀴즈 진행 중이면 JS로 퀴즈 탭 자동 포커스
if "quiz_state" in st.session_state:
    components.html("""
    <script>
        const tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
        if (tabs.length >= 2) { tabs[1].click(); }
    </script>
    """, height=0)


# ========================================
# 📸 단어 등록 탭
# ========================================
with tab_register:
    st.markdown("### 📸 이미지에서 단어 추출하기")
    st.caption("영어 단어가 포함된 이미지를 업로드하면 AI가 자동으로 단어와 뜻을 추출합니다.")

    col_upload, col_camera = st.columns(2)

    with col_upload:
        uploaded_file = st.file_uploader(
            "📁 파일 업로드",
            type=["png", "jpg", "jpeg", "webp"],
            help="영어 단어가 포함된 이미지를 선택하세요.",
        )

    with col_camera:
        if "camera_active" not in st.session_state:
            st.session_state["camera_active"] = False

        if not st.session_state["camera_active"]:
            if st.button("📷 카메라 촬영", use_container_width=True):
                st.session_state["camera_active"] = True
                st.rerun()
        else:
            camera_input = st.camera_input("📷 카메라", key="camera")
            if st.button("❌ 카메라 닫기", use_container_width=True):
                st.session_state["camera_active"] = False
                st.rerun()

    image_source = None
    if st.session_state.get("camera_active") and "camera" in st.session_state:
        camera_input = st.session_state.get("camera")
        if camera_input:
            image_source = camera_input
    if not image_source and uploaded_file:
        image_source = uploaded_file

    if image_source:
        st.image(image_source, caption="업로드된 이미지", use_container_width=True)

        if st.button("🔍 AI로 단어 추출하기", type="primary", use_container_width=True):
            with st.spinner("🤖 Gemini가 이미지를 분석하고 있습니다..."):
                try:
                    image_bytes = image_source.getvalue()
                    words = gemini_service.analyze_image(image_bytes)

                    if not words:
                        st.warning("⚠️ 이미지에서 영어 단어를 찾을 수 없습니다.")
                    else:
                        st.session_state["extracted_words"] = words
                        st.success(f"✅ {len(words)}개의 단어를 추출했습니다!")
                except Exception as e:
                    st.error(f"❌ 단어 추출 실패: {str(e)}")

    if "extracted_words" in st.session_state and st.session_state["extracted_words"]:
        words = st.session_state["extracted_words"]

        st.markdown("---")
        st.markdown("### 📋 추출된 단어 목록")

        df = pd.DataFrame(words)
        df.columns = ["Word", "Meaning"]
        df.index = range(1, len(df) + 1)
        st.dataframe(df, use_container_width=True)

        st.markdown("---")

        if st.button("💾 Notion에 저장하기", type="primary", use_container_width=True):
            with st.spinner("📤 Notion에 저장하는 중..."):
                try:
                    summary = gemini_service.generate_summary(words)
                    page_title = notion_service.save_words(words, summary)
                    st.success(f'✅ Notion에 저장 완료! 📄 페이지: **{page_title}**')
                    del st.session_state["extracted_words"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Notion 저장 실패: {str(e)}")


# ========================================
# 📝 퀴즈 탭
# ========================================
TIMER_SECONDS = 30

with tab_quiz:
    st.markdown("### 📝 단어 퀴즈")
    st.caption("Notion에 저장된 단어로 퀴즈를 풀어보세요!")

    # ── 페이지 로드 ──
    if st.button("🔄 페이지 목록 새로고침", use_container_width=True):
        st.session_state.pop("quiz_pages", None)
        st.session_state.pop("quiz_state", None)
        st.rerun()

    if "quiz_pages" not in st.session_state:
        with st.spinner("📥 Notion에서 페이지 목록을 불러오는 중..."):
            try:
                pages = notion_service.fetch_pages()
                st.session_state["quiz_pages"] = pages
            except Exception as e:
                st.error(f"❌ 페이지 목록 로드 실패: {str(e)}")
                st.stop()

    pages = st.session_state.get("quiz_pages", [])

    if not pages:
        st.info("📭 아직 저장된 단어가 없습니다. '단어 등록' 탭에서 먼저 단어를 등록해주세요!")
    else:
        # ── 퀴즈 설정 ──
        col_page, col_type, col_filter = st.columns([3, 1, 1])

        with col_page:
            page_options = {p["title"]: p["id"] for p in pages}
            selected_title = st.selectbox(
                "📄 학습할 페이지 선택",
                options=list(page_options.keys()),
            )

        with col_type:
            quiz_type = st.radio("퀴즈 유형", ["A: 영→한", "B: 한→영"], horizontal=True)
            quiz_type_key = "A" if "A" in quiz_type else "B"

        with col_filter:
            quiz_filter = st.radio("출제 범위", ["전체", "오답만"], horizontal=True)

        # ── 퀴즈 시작 ──
        if st.button("🚀 퀴즈 시작!", type="primary", use_container_width=True):
            selected_page_id = page_options[selected_title]

            with st.spinner("📥 단어를 불러오는 중..."):
                try:
                    all_words = notion_service.fetch_words(selected_page_id)

                    if quiz_filter == "오답만":
                        quiz_words = [w for w in all_words if w.get("result") in ["❌", "⏰", ""]]
                        if not quiz_words:
                            quiz_words = [w for w in all_words if w.get("result") != "✅"]
                    else:
                        quiz_words = all_words

                    if len(quiz_words) < 1 or len(all_words) < 2:
                        st.warning("⚠️ 퀴즈를 시작하려면 최소 2개 이상의 단어가 필요합니다.")
                    else:
                        quiz = quiz_service.generate_quiz(quiz_words, quiz_type_key, all_words)
                        st.session_state["quiz_state"] = {
                            "quiz": quiz,
                            "current": 0,
                            "score": 0,
                            "total": len(quiz),
                            "answers": [],
                            "completed": False,
                            "quiz_type": quiz_type_key,
                            "question_start_time": time.time(),
                            "submitted": False,
                            "feedback_time": 0,
                            "last_correct": False,
                            "last_answer": "",
                            "last_timeout": False,
                            "page_id": selected_page_id,
                            "notion_updated": False,
                        }
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 퀴즈 생성 실패: {str(e)}")

        # ── 퀴즈 진행 ──
        if "quiz_state" in st.session_state:
            qs = st.session_state["quiz_state"]

            if not qs["completed"]:
                current = qs["current"]
                total = qs["total"]
                q = qs["quiz"][current]

                # 진행 상황
                st.progress(current / total, text=f"문제 {current + 1} / {total}  |  점수: {qs['score']}/{current}")

                if not qs["submitted"]:
                    # ── 활성 문제 상태 ──
                    elapsed = time.time() - qs["question_start_time"]
                    remaining = max(0, int(TIMER_SECONDS - elapsed))

                    # 타임아웃 체크
                    if remaining <= 0:
                        qs["answers"].append({
                            "question": q["question"],
                            "your_answer": "⏰ 시간 초과",
                            "correct_answer": q["answer"],
                            "is_correct": False,
                        })
                        qs["submitted"] = True
                        qs["last_correct"] = False
                        qs["last_answer"] = q["answer"]
                        qs["last_timeout"] = True
                        qs["feedback_time"] = time.time()
                        st.rerun()

                    # 타이머 + 문제 표시
                    timer_col, question_col = st.columns([1, 5])

                    with timer_col:
                        css_class = "timer-warning" if remaining <= 10 else "timer-normal"
                        st.markdown(
                            f'<div class="{css_class}">⏰ {remaining}초</div>',
                            unsafe_allow_html=True,
                        )
                        st.progress(remaining / TIMER_SECONDS)

                    with question_col:
                        label = "Word" if qs["quiz_type"] == "A" else "뜻"
                        st.markdown(
                            f'<div class="word-card"><h2>{q["question"]}</h2>'
                            f'<p style="color:#6b7280;margin-top:0.5rem">위 {label}의 정답을 선택하세요</p></div>',
                            unsafe_allow_html=True,
                        )

                    # 선택지 (선택 시 자동 제출)
                    selected = st.radio(
                        "정답을 선택하세요:",
                        q["choices"],
                        index=None,
                        key=f"quiz_q_{current}",
                        label_visibility="collapsed",
                    )

                    # 선택하면 자동 제출
                    if selected is not None:
                        is_correct = selected == q["answer"]

                        if is_correct:
                            qs["score"] += 1

                        qs["answers"].append({
                            "question": q["question"],
                            "your_answer": selected,
                            "correct_answer": q["answer"],
                            "is_correct": is_correct,
                        })
                        qs["submitted"] = True
                        qs["last_correct"] = is_correct
                        qs["last_answer"] = q["answer"]
                        qs["last_timeout"] = False
                        qs["feedback_time"] = time.time()
                        st.rerun()

                else:
                    # ── 피드백 상태 ──
                    if qs["last_timeout"]:
                        st.markdown(
                            f'<div class="timeout-answer">⏰ 시간 초과! 정답은 <strong>{qs["last_answer"]}</strong>입니다.</div>',
                            unsafe_allow_html=True,
                        )
                    elif qs["last_correct"]:
                        st.markdown(
                            '<div class="correct-answer">🎉 정답입니다!</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div class="wrong-answer">❌ 오답! 정답은 <strong>{qs["last_answer"]}</strong>입니다.</div>',
                            unsafe_allow_html=True,
                        )

                    # 1초 후 자동 다음 문제 (autorefresh가 1초마다 rerun)
                    if time.time() - qs["feedback_time"] >= 1.5:
                        qs["submitted"] = False
                        qs["last_timeout"] = False
                        if current + 1 >= total:
                            qs["completed"] = True
                        else:
                            qs["current"] += 1
                            qs["question_start_time"] = time.time()
                        st.rerun()

            else:
                # ── 결과 화면 ──
                score = qs["score"]
                total = qs["total"]
                pct = (score / total) * 100

                # Notion 결과 업데이트 (최초 1회)
                if not qs.get("notion_updated"):
                    with st.spinner("📤 Notion에 퀴즈 결과를 저장하는 중..."):
                        try:
                            results = []
                            for a in qs["answers"]:
                                if a["your_answer"] == "⏰ 시간 초과":
                                    emoji = "⏰"
                                elif a["is_correct"]:
                                    emoji = "✅"
                                else:
                                    emoji = "❌"
                                results.append({"word": a["question"] if qs["quiz_type"] == "A" else a["correct_answer"], "result": emoji})

                            notion_service.update_word_results(qs["page_id"], results)
                            qs["notion_updated"] = True
                            st.rerun()
                        except Exception as e:
                            st.warning(f"⚠️ Notion 결과 업데이트 실패: {str(e)}")
                            qs["notion_updated"] = True

                st.markdown(
                    f"""
                    <div class="score-card">
                        <p style="font-size:1.2rem;margin-bottom:0.5rem">🏆 최종 점수</p>
                        <h1>{score} / {total}</h1>
                        <p style="font-size:1.5rem;margin-top:0.5rem">{pct:.0f}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if pct == 100:
                    st.balloons()
                    st.success("🎊 완벽합니다! 모든 문제를 맞혔어요!")
                elif pct >= 70:
                    st.success("👏 훌륭해요! 조금만 더 연습하면 완벽해질 거예요!")
                else:
                    st.info("💪 아직 갈 길이 멀지만 포기하지 마세요!")

                # 틀린 단어 목록
                wrong_answers = [a for a in qs["answers"] if not a["is_correct"]]
                if wrong_answers:
                    st.markdown("---")
                    st.markdown("### 📌 틀린 단어 복습")
                    wrong_df = pd.DataFrame(wrong_answers)
                    wrong_df.columns = ["문제", "내 답", "정답", "정오"]
                    wrong_df = wrong_df[["문제", "내 답", "정답"]]
                    wrong_df.index = range(1, len(wrong_df) + 1)
                    st.dataframe(wrong_df, use_container_width=True)

                # Notion 결과 반영 안내
                if qs.get("notion_updated"):
                    st.success("📝 Notion에 정답/오답 결과가 반영되었습니다!")

                # 다시 풀기
                if st.button("🔄 다시 풀기", type="primary", use_container_width=True):
                    del st.session_state["quiz_state"]
                    st.rerun()
