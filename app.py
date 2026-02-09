# app.py
import os
import re
import json
import random
from datetime import datetime, timedelta, date

import requests
import pandas as pd
import streamlit as st


# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="AI 습관 트래커", page_icon="📊", layout="wide")
st.title("📊 AI 습관 트래커")

# -------------------------
# Sidebar: API Keys
# -------------------------
with st.sidebar:
    st.header("🔑 API 설정")
    openai_api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    owm_api_key = st.text_input("OpenWeatherMap API Key", type="password", value=os.getenv("OPENWEATHER_API_KEY", ""))
    st.caption("키는 브라우저 세션에만 사용됩니다. (session_state 저장)")

# =========================
# Session State 초기화
# =========================
if "records" not in st.session_state:
    # records: { "YYYY-MM-DD": {habits: {...}, mood: int, city: str, coach_style: str, created_at: str } }
    st.session_state.records = {}

if "demo_initialized" not in st.session_state:
    st.session_state.demo_initialized = False


def _iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _today_iso() -> str:
    return datetime.now().date().strftime("%Y-%m-%d")


def init_demo_records():
    """데모용 6일 샘플 데이터 생성 (오늘 제외), session_state에 저장."""
    if st.session_state.demo_initialized:
        return

    today = datetime.now().date()
    cities = ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Suwon", "Ulsan", "Jeju", "Sejong"]
    styles = ["스파르타 코치", "따뜻한 멘토", "게임 마스터"]

    for i in range(6, 0, -1):
        d = today - timedelta(days=i)
        # 랜덤 습관 체크
        habits = {
            "기상 미션": random.choice([True, False]),
            "물 마시기": random.choice([True, False]),
            "공부/독서": random.choice([True, False]),
            "운동하기": random.choice([True, False]),
            "수면": random.choice([True, False]),
        }
        mood = random.randint(4, 9)
        city = random.choice(cities)
        coach_style = random.choice(styles)
        st.session_state.records[_iso(d)] = {
            "habits": habits,
            "mood": mood,
            "city": city,
            "coach_style": coach_style,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    st.session_state.demo_initialized = True


init_demo_records()


# =========================
# API 연동 함수들
# =========================
def get_weather(city: str, api_key: str):
    """
    OpenWeatherMap에서 날씨 가져오기 (한국어, 섭씨).
    실패 시 None 반환. timeout=10
    """
    if not city or not api_key:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric", "lang": "kr"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        weather_desc = (data.get("weather") or [{}])[0].get("description")
        temp = (data.get("main") or {}).get("temp")
        feels_like = (data.get("main") or {}).get("feels_like")
        humidity = (data.get("main") or {}).get("humidity")
        wind = (data.get("wind") or {}).get("speed")
        return {
            "city": city,
            "desc": weather_desc,
            "temp_c": temp,
            "feels_like_c": feels_like,
            "humidity": humidity,
            "wind_mps": wind,
        }
    except Exception:
        return None


def _breed_from_dog_ceo_url(image_url: str):
    # 예: https://images.dog.ceo/breeds/hound-afghan/n02088094_1003.jpg
    try:
        m = re.search(r"/breeds/([^/]+)/", image_url)
        if not m:
            return None
        raw = m.group(1)  # "hound-afghan" 같은 형태
        # 보기 좋게 변환
        parts = raw.split("-")
        parts = [p.replace("_", " ").strip().title() for p in parts if p.strip()]
        return " ".join(parts) if parts else None
    except Exception:
        return None


def get_dog_image():
    """
    Dog CEO에서 랜덤 강아지 사진 URL과 품종 가져오기.
    실패 시 None 반환. timeout=10
    """
    try:
        url = "https://dog.ceo/api/breeds/image/random"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("status") != "success":
            return None
        image_url = data.get("message")
        breed = _breed_from_dog_ceo_url(image_url) or "Unknown"
        return {"image_url": image_url, "breed": breed}
    except Exception:
        return None


def _openai_responses(api_key: str, model: str, instructions: str, user_input: str, max_output_tokens: int = 700):
    """
    OpenAI Responses API 호출 (requests 사용).
    실패 시 None 반환. timeout=10
    """
    if not api_key:
        return None
    try:
        url = "https://api.openai.com/v1/responses"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model,
            "instructions": instructions,
            "input": user_input,
            "max_output_tokens": max_output_tokens,
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        # SDK의 output_text가 없어도 최대한 텍스트를 뽑아오기
        if isinstance(data, dict) and data.get("output_text"):
            return data["output_text"]
        # output 배열에서 message의 content 텍스트 합치기
        out = []
        for item in data.get("output", []) if isinstance(data, dict) else []:
            if item.get("type") == "message":
                content = item.get("content", [])
                for c in content:
                    if c.get("type") in ("output_text", "text"):
                        txt = c.get("text") or c.get("content") or ""
                        if txt:
                            out.append(txt)
        return "\n".join(out).strip() if out else None
    except Exception:
        return None


def generate_report(
    habits: dict,
    mood: int,
    weather: dict | None,
    dog: dict | None,
    coach_style: str,
    openai_key: str,
):
    """
    습관+기분+날씨+강아지 품종을 모아서 OpenAI에 전달해 리포트 생성.
    코치 스타일별 시스템 프롬프트 적용.
    출력 형식:
      - 컨디션 등급(S~D)
      - 습관 분석
      - 날씨 코멘트
      - 내일 미션
      - 오늘의 한마디
    모델: gpt-5-mini
    """
    style_prompts = {
        "스파르타 코치": (
            "너는 엄격하고 단호한 코치다. 변명은 차단하고, 실행 가능한 지시를 짧고 강하게 준다. "
            "하지만 인신공격은 절대 하지 않는다."
        ),
        "따뜻한 멘토": (
            "너는 따뜻하고 공감적인 멘토다. 사용자의 노력을 인정하고, 작은 개선을 부드럽게 제안한다. "
            "과장된 칭찬 대신 구체적이고 현실적인 격려를 한다."
        ),
        "게임 마스터": (
            "너는 RPG 게임 마스터다. 사용자의 하루를 퀘스트/경험치/레벨업 관점으로 재해석해준다. "
            "유쾌하지만 목표는 분명하게, 내일 미션은 '퀘스트'로 제시한다."
        ),
    }

    checked = [k for k, v in habits.items() if v]
    unchecked = [k for k, v in habits.items() if not v]

    weather_text = "날씨 정보 없음"
    if weather:
        weather_text = (
            f"{weather.get('city')} / {weather.get('desc')} / "
            f"{weather.get('temp_c')}°C(체감 {weather.get('feels_like_c')}°C), "
            f"습도 {weather.get('humidity')}%, 바람 {weather.get('wind_mps')}m/s"
        )

    dog_text = "강아지 정보 없음"
    if dog:
        dog_text = f"{dog.get('breed')} (이미지 URL: {dog.get('image_url')})"

    instructions = (
        style_prompts.get(coach_style, style_prompts["따뜻한 멘토"])
        + "\n\n"
        + "출력은 반드시 아래 섹션 헤더를 그대로 사용해 한국어로 작성해.\n"
        + "형식:\n"
        + "컨디션 등급: (S/A/B/C/D 중 하나)\n"
        + "습관 분석:\n"
        + "- ...\n"
        + "날씨 코멘트:\n"
        + "- ...\n"
        + "내일 미션:\n"
        + "- ... (최대 3개)\n"
        + "오늘의 한마디:\n"
        + "- ... (1줄)\n"
        + "추가 설명이나 다른 섹션은 만들지 마.\n"
    )

    user_input = (
        "아래 데이터를 바탕으로 오늘의 컨디션 리포트를 작성해줘.\n\n"
        f"[기분] {mood}/10\n"
        f"[완료한 습관] {', '.join(checked) if checked else '없음'}\n"
        f"[미완료 습관] {', '.join(unchecked) if unchecked else '없음'}\n"
        f"[날씨] {weather_text}\n"
        f"[강아지] {dog_text}\n"
    )

    return _openai_responses(
        api_key=openai_key,
        model="gpt-5-mini",
        instructions=instructions,
        user_input=user_input,
        max_output_tokens=750,
    )


# =========================
# 습관 체크인 UI
# =========================
HABITS = [
    ("🌅", "기상 미션"),
    ("💧", "물 마시기"),
    ("📚", "공부/독서"),
    ("🏃", "운동하기"),
    ("😴", "수면"),
]

CITIES = ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Gwangju", "Suwon", "Ulsan", "Jeju", "Sejong"]
COACH_STYLES = ["스파르타 코치", "따뜻한 멘토", "게임 마스터"]

today_key = _today_iso()
today_record = st.session_state.records.get(today_key, None)

# 기본값 복원 (있으면 오늘 기록, 없으면 초기값)
default_habits = {name: False for _, name in HABITS}
default_mood = 6
default_city = "Seoul"
default_style = "따뜻한 멘토"

if today_record:
    default_habits.update(today_record.get("habits", {}))
    default_mood = int(today_record.get("mood", default_mood))
    default_city = today_record.get("city", default_city)
    default_style = today_record.get("coach_style", default_style)

st.subheader("✅ 오늘의 체크인")

left, right = st.columns([1, 1])

# 체크박스 5개를 2열로 배치
cb_cols = st.columns(2)
habits_state = {}
for i, (emoji, name) in enumerate(HABITS):
    col = cb_cols[i % 2]
    with col:
        habits_state[name] = st.checkbox(f"{emoji} {name}", value=bool(default_habits.get(name, False)))

mood = st.slider("🙂 오늘 기분은 어때요?", min_value=1, max_value=10, value=int(default_mood))
city = st.selectbox("🏙️ 도시 선택", options=CITIES, index=CITIES.index(default_city) if default_city in CITIES else 0)
coach_style = st.radio("🧑‍🏫 코치 스타일", options=COACH_STYLES, index=COACH_STYLES.index(default_style), horizontal=True)

# session_state 기록 저장 (즉시)
st.session_state.records[today_key] = {
    "habits": habits_state,
    "mood": mood,
    "city": city,
    "coach_style": coach_style,
    "created_at": datetime.now().isoformat(timespec="seconds"),
}

# =========================
# 달성률 + metric 카드
# =========================
completed_count = sum(1 for v in habits_state.values() if v)
total_count = len(habits_state)
achievement = int(round((completed_count / total_count) * 100)) if total_count else 0

m1, m2, m3 = st.columns(3)
m1.metric("달성률", f"{achievement}%")
m2.metric("달성 습관", f"{completed_count}/{total_count}")
m3.metric("기분", f"{mood}/10")

# =========================
# 7일 바 차트 (데모 6일 + 오늘)
# =========================
st.subheader("📈 최근 7일 달성률")

today = datetime.now().date()
last7 = [today - timedelta(days=i) for i in range(6, -1)]

rows = []
for d in last7:
    key = _iso(d)
    rec = st.session_state.records.get(key)

    if isinstance(rec, dict):
        h = rec.get("habits") or {}
        # habits가 dict가 아닐 수도 있으니 방어
        if not isinstance(h, dict):
            h = {}

        c = sum(1 for v in h.values() if bool(v))
        t = len(h) if len(h) > 0 else 5
        rate = int(round((c / t) * 100)) if t else 0
        mood_v = rec.get("mood", 0)
    else:
        rate = 0
        mood_v = 0

    rows.append({"date": key, "achievement(%)": rate, "mood": int(mood_v) if mood_v is not None else 0})

# rows 방어: 혹시라도 비면 기본값 7개 생성
if not rows:
    rows = [{"date": _iso(today - timedelta(days=i)), "achievement(%)": 0, "mood": 0} for i in range(6, -1)]

df = pd.DataFrame(rows)

# 컬럼 방어: date가 없으면 강제로 생성
if "date" not in df.columns:
    df["date"] = [r.get("date", "") for r in rows]

df = df.set_index("date")

# 차트 표시 (컬럼이 없을 때도 대비)
if "achievement(%)" in df.columns:
    st.bar_chart(df[["achievement(%)"]], height=260)
else:
    st.warning("차트 데이터를 만들지 못했어요. 기록을 다시 저장해보세요.")

# =========================
# 결과 표시: 날씨 + 강아지 + AI 리포트
# =========================
st.subheader("🧠 AI 코치 리포트")

btn_disabled = not bool(openai_api_key)
btn_help = "OpenAI API Key를 사이드바에 입력하면 활성화됩니다." if btn_disabled else None

if st.button("컨디션 리포트 생성", type="primary", disabled=btn_disabled, help=btn_help):
    with st.spinner("날씨/강아지/AI 리포트를 준비하는 중..."):
        weather = get_weather(city, owm_api_key)
        dog = get_dog_image()

        report = generate_report(
            habits=habits_state,
            mood=mood,
            weather=weather,
            dog=dog,
            coach_style=coach_style,
            openai_key=openai_api_key,
        )

    # 2열 카드: 날씨 + 강아지
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 🌦️ 오늘의 날씨")
        if weather:
            st.info(
                f"**{weather.get('city')}**\n\n"
                f"- 상태: {weather.get('desc')}\n"
                f"- 기온: {weather.get('temp_c')}°C (체감 {weather.get('feels_like_c')}°C)\n"
                f"- 습도: {weather.get('humidity')}%\n"
                f"- 바람: {weather.get('wind_mps')}m/s"
            )
        else:
            st.warning("날씨 정보를 가져오지 못했어요. (API Key/도시/네트워크 확인)")

    with c2:
        st.markdown("#### 🐶 오늘의 강아지")
        if dog and dog.get("image_url"):
            st.caption(f"품종: **{dog.get('breed', 'Unknown')}**")
            st.image(dog["image_url"], use_container_width=True)
        else:
            st.warning("강아지 이미지를 가져오지 못했어요. (네트워크 확인)")

    # AI 리포트
    st.markdown("#### 📝 리포트")
    if report:
        st.markdown(report)
    else:
        st.error("AI 리포트를 생성하지 못했어요. (OpenAI Key/요금/모델/네트워크 확인)")

    # 공유용 텍스트
    share_lines = []
    share_lines.append(f"📊 AI 습관 트래커 - {today_key}")
    share_lines.append(f"도시: {city} | 코치: {coach_style}")
    share_lines.append(f"달성률: {achievement}% ({completed_count}/{total_count}) | 기분: {mood}/10")
    share_lines.append("완료 습관: " + (", ".join([k for k, v in habits_state.items() if v]) or "없음"))
    if weather:
        share_lines.append(f"날씨: {weather.get('desc')} / {weather.get('temp_c')}°C")
    if dog:
        share_lines.append(f"강아지: {dog.get('breed')}")
    share_lines.append("\n[AI 리포트]\n" + (report or "(생성 실패)"))

    st.markdown("#### 📣 공유용 텍스트")
    st.code("\n".join(share_lines), language="markdown")

# =========================
# 하단: API 안내
# =========================
with st.expander("ℹ️ API 안내 / 설정 팁"):
    st.markdown(
        """
- **OpenAI API Key**: OpenAI 플랫폼에서 발급한 키를 입력하세요.
  - 이 앱은 **Responses API**를 사용해 `https://api.openai.com/v1/responses` 로 요청합니다.
  - 모델은 요청대로 **gpt-5-mini**를 사용합니다.
- **OpenWeatherMap API Key**: OpenWeatherMap에서 발급받아 입력하세요.
  - 현재 날씨 API(`data/2.5/weather`)를 사용하며 **섭씨(units=metric)**, **한국어(lang=kr)** 로 요청합니다.
- **Dog CEO API**: 키 없이 무료로 호출됩니다.
  - 랜덤 이미지 URL에서 품종(가능한 경우)을 추정해 표시합니다.

문제 해결:
- 리포트 생성 실패: OpenAI Key, 결제/쿼터, 모델 접근 권한을 확인하세요.
- 날씨 실패: OpenWeatherMap Key, 도시명(영문), 무료 플랜 제한 여부를 확인하세요.
"""
    )
