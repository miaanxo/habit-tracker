# app.py
# Streamlit: AI 습관 트래커 (포켓몬 에디션) + 포켓몬 도감(기록) 기능
# 실행: streamlit run app.py

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Tuple

import pandas as pd
import requests
import streamlit as st

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="AI 습관 트래커 (포켓몬)", page_icon="🎮", layout="wide")

st.title("🎮 AI 습관 트래커 (포켓몬)")
st.caption("오늘의 습관을 체크하고, 날씨 + 포켓몬 + AI 코치 리포트를 받아보세요!")

# -----------------------------
# Sidebar: API keys
# -----------------------------
with st.sidebar:
    st.header("🔑 API 설정")
    openai_api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    owm_api_key = st.text_input("OpenWeatherMap API Key", type="password", placeholder="OWM Key...")
    st.divider()
    st.caption("키는 로컬에만 사용되며 저장하지 않습니다.")

# -----------------------------
# Session state init (Pokedex)
# -----------------------------
if "pokedex" not in st.session_state:
    # list[dict] 형태로 누적 기록
    st.session_state.pokedex = []  # type: ignore[attr-defined]
if "pokedex_ids" not in st.session_state:
    # 중복 등록 방지용 (도감번호 기준)
    st.session_state.pokedex_ids = set()  # type: ignore[attr-defined]

# -----------------------------
# Constants / helpers
# -----------------------------
HABITS: List[Tuple[str, str]] = [
    ("기상 미션", "🌅"),
    ("물 마시기", "💧"),
    ("공부/독서", "📚"),
    ("운동하기", "🏃"),
    ("수면", "😴"),
]

CITIES = [
    "Seoul",
    "Busan",
    "Incheon",
    "Daegu",
    "Daejeon",
    "Gwangju",
    "Suwon",
    "Ulsan",
    "Jeju",
    "Sejong",
]

COACH_STYLES = {
    "스파르타 코치": "sparta",
    "따뜻한 멘토": "mentor",
    "게임 마스터": "gamemaster",
}

STAT_KR = {
    "hp": "HP",
    "attack": "공격",
    "defense": "방어",
    "special-attack": "특수공격",
    "special-defense": "특수방어",
    "speed": "스피드",
}


def safe_get(d: Dict[str, Any], *keys: str, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def _pokemon_record_from_api(pokemon: Dict[str, Any]) -> Dict[str, Any]:
    """도감 저장용 레코드(평탄화) 생성"""
    stats = pokemon.get("stats", {}) or {}
    return {
        "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dex_no": int(pokemon.get("dex_no") or 0),
        "name": pokemon.get("name") or "",
        "types": ", ".join(pokemon.get("types") or []),
        "artwork": pokemon.get("artwork") or "",
        "hp": int(stats.get("hp", 0)),
        "attack": int(stats.get("attack", 0)),
        "defense": int(stats.get("defense", 0)),
        "sp_atk": int(stats.get("special-attack", 0)),
        "sp_def": int(stats.get("special-defense", 0)),
        "speed": int(stats.get("speed", 0)),
        "bst": int(stats.get("hp", 0))
        + int(stats.get("attack", 0))
        + int(stats.get("defense", 0))
        + int(stats.get("special-attack", 0))
        + int(stats.get("special-defense", 0))
        + int(stats.get("speed", 0)),
    }


def add_to_pokedex(pokemon: Optional[Dict[str, Any]]) -> bool:
    """도감에 추가. 신규면 True, 중복/실패면 False"""
    if not pokemon:
        return False
    dex_no = pokemon.get("dex_no")
    if not dex_no:
        return False

    ids = st.session_state.pokedex_ids  # type: ignore[attr-defined]
    if dex_no in ids:
        return False

    rec = _pokemon_record_from_api(pokemon)
    st.session_state.pokedex.append(rec)  # type: ignore[attr-defined]
    ids.add(dex_no)
    return True


# -----------------------------
# API functions
# -----------------------------
def get_weather(city: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    OpenWeatherMap Current Weather API
    - language: Korean (lang=kr)
    - units: metric (섭씨)
    - timeout=10
    실패 시 None 반환
    """
    if not api_key:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric", "lang": "kr"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        j = r.json()

        weather_desc = safe_get(j, "weather", default=[{}])[0].get("description")
        icon = safe_get(j, "weather", default=[{}])[0].get("icon")
        temp = safe_get(j, "main", "temp")
        feels_like = safe_get(j, "main", "feels_like")
        humidity = safe_get(j, "main", "humidity")
        wind = safe_get(j, "wind", "speed")

        return {
            "city": city,
            "description": weather_desc,
            "icon": icon,
            "temp_c": temp,
            "feels_like_c": feels_like,
            "humidity": humidity,
            "wind_mps": wind,
        }
    except Exception:
        return None


def get_pokemon() -> Optional[Dict[str, Any]]:
    """
    PokeAPI: 1세대(1~151) 랜덤 포켓몬
    - 공식 아트워크 URL
    - 이름, 도감 번호, 타입, 스탯(HP/공격/방어/특수공격/특수방어/스피드)
    - timeout=10
    실패 시 None 반환
    """
    try:
        pid = random.randint(1, 151)
        url = f"https://pokeapi.co/api/v2/pokemon/{pid}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        j = r.json()

        name = j.get("name")
        dex_no = j.get("id")
        types = [t["type"]["name"] for t in j.get("types", []) if "type" in t]
        artwork = safe_get(j, "sprites", "other", "official-artwork", "front_default")

        stats_raw = {s["stat"]["name"]: s["base_stat"] for s in j.get("stats", [])}
        stats = {
            "hp": int(stats_raw.get("hp", 0)),
            "attack": int(stats_raw.get("attack", 0)),
            "defense": int(stats_raw.get("defense", 0)),
            "special-attack": int(stats_raw.get("special-attack", 0)),
            "special-defense": int(stats_raw.get("special-defense", 0)),
            "speed": int(stats_raw.get("speed", 0)),
        }

        return {"name": name, "dex_no": dex_no, "types": types, "artwork": artwork, "stats": stats}
    except Exception:
        return None


def generate_report(
    openai_api_key: str,
    coach_style_key: str,
    habits_checked: Dict[str, bool],
    mood: int,
    weather: Optional[Dict[str, Any]],
    pokemon: Optional[Dict[str, Any]],
    pokedex_count: int,
) -> str:
    """
    OpenAI 호출: gpt-5-mini
    출력 형식:
    - 컨디션 등급(S~D)
    - 습관 분석
    - 날씨 코멘트
    - 내일 미션
    - 오늘의 파트너 포켓몬(포켓몬 이름/타입/스탯을 활용한 응원)
    """
    if not openai_api_key:
        return "⚠️ OpenAI API Key가 없어 리포트를 생성할 수 없어요. (사이드바에 입력해 주세요)"

    style_system = {
        "sparta": (
            "너는 엄격한 스파르타 코치다. 말투는 단호하고 직설적이며, 핑계를 허용하지 않는다. "
            "하지만 모욕적이진 않다. 짧고 강하게, 실행 지시를 준다."
        ),
        "mentor": (
            "너는 따뜻한 멘토다. 말투는 다정하고 공감적이며, 작은 성취도 칭찬한다. "
            "현실적인 조언과 격려를 함께 준다."
        ),
        "gamemaster": (
            "너는 RPG 게임 마스터다. 오늘을 퀘스트와 스테이지로 묘사하며, 분위기는 모험적이고 재밌다. "
            "사용자가 성장하도록 다음 미션을 제시한다."
        ),
    }.get(coach_style_key, "너는 도움이 되는 코치다.")

    checked_list = [k for k, v in habits_checked.items() if v]
    unchecked_list = [k for k, v in habits_checked.items() if not v]

    weather_block = "날씨 정보: 없음(가져오기 실패 또는 API Key 없음)"
    if weather:
        weather_block = (
            f"날씨 정보: 도시={weather.get('city')}, 상태={weather.get('description')}, "
            f"기온={weather.get('temp_c')}°C, 체감={weather.get('feels_like_c')}°C, "
            f"습도={weather.get('humidity')}%, 바람={weather.get('wind_mps')}m/s"
        )

    pokemon_block = "포켓몬 정보: 없음(가져오기 실패)"
    if pokemon:
        stats = pokemon.get("stats", {})
        pokemon_block = (
            f"포켓몬 정보: 이름={pokemon.get('name')}, 도감번호={pokemon.get('dex_no')}, "
            f"타입={', '.join(pokemon.get('types', []))}, "
            f"스탯(HP={stats.get('hp')}, 공격={stats.get('attack')}, 방어={stats.get('defense')}, "
            f"특수공격={stats.get('special-attack')}, 특수방어={stats.get('special-defense')}, 스피드={stats.get('speed')})"
        )

    user_payload = f"""
[오늘 습관 체크]
- 완료: {", ".join(checked_list) if checked_list else "없음"}
- 미완료: {", ".join(unchecked_list) if unchecked_list else "없음"}
- 기분(1~10): {mood}
- 내 도감 진행도: {pokedex_count}/151

[{weather_block}]

[{pokemon_block}]

[출력 형식(반드시 지켜라)]
1) 컨디션 등급: S/A/B/C/D 중 하나 (한 줄)
2) 습관 분석: 3~6줄 (잘한 점 + 개선 1~2개)
3) 날씨 코멘트: 1~3줄 (날씨에 맞춘 행동 팁)
4) 내일 미션: 3개 체크리스트(짧게)
5) 오늘의 파트너 포켓몬: 포켓몬 이름/타입/스탯을 활용한 응원 3~5줄
""".strip()

    try:
        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=openai_api_key)
            resp = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": style_system},
                    {"role": "user", "content": user_payload},
                ],
            )
            return (resp.choices[0].message.content or "").strip() or "리포트 생성에 실패했어요."
        except Exception:
            import openai  # type: ignore

            openai.api_key = openai_api_key
            resp = openai.ChatCompletion.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": style_system},
                    {"role": "user", "content": user_payload},
                ],
            )
            return (resp["choices"][0]["message"]["content"] or "").strip() or "리포트 생성에 실패했어요."
    except Exception as e:
        return f"⚠️ 리포트 생성 중 오류가 발생했어요: {e}"


# -----------------------------
# Habit check-in UI
# -----------------------------
st.subheader("✅ 오늘의 체크인")

colA, colB = st.columns([1.2, 1])

with colA:
    st.markdown("#### 습관 체크")
    c1, c2 = st.columns(2)
    habits_checked: Dict[str, bool] = {}

    left_idx = [0, 2, 4]
    right_idx = [1, 3]

    with c1:
        for i in left_idx:
            label, emo = HABITS[i]
            habits_checked[label] = st.checkbox(f"{emo} {label}", key=f"habit_{i}")
    with c2:
        for i in right_idx:
            label, emo = HABITS[i]
            habits_checked[label] = st.checkbox(f"{emo} {label}", key=f"habit_{i}")

    st.markdown("#### 😊 기분")
    mood = st.slider("오늘 기분은 어때요?", min_value=1, max_value=10, value=6, step=1)

with colB:
    st.markdown("#### 🌍 환경 설정")
    city = st.selectbox("도시 선택", CITIES, index=0)
    coach_style_label = st.radio("코치 스타일", list(COACH_STYLES.keys()), horizontal=False)
    coach_style_key = COACH_STYLES[coach_style_label]

# -----------------------------
# Metrics + chart data
# -----------------------------
completed = sum(1 for v in habits_checked.values() if v)
total = len(HABITS)
achievement_rate = int(round((completed / total) * 100)) if total else 0

m1, m2, m3 = st.columns(3)
m1.metric("달성률", f"{achievement_rate} %")
m2.metric("달성 습관", f"{completed} / {total}")
m3.metric("기분", f"{mood} / 10")

st.divider()

st.subheader("📊 최근 7일 기록 (데모 + 오늘)")

today = datetime.now().date()
sample_days = [today - timedelta(days=d) for d in range(6, 0, -1)]
rng = random.Random(42)

sample_rows = []
for d in sample_days:
    sample_rows.append({"date": d.isoformat(), "completed": rng.randint(1, 5), "mood": rng.randint(3, 9)})

today_row = {"date": today.isoformat(), "completed": completed, "mood": mood}

df7 = pd.DataFrame(sample_rows + [today_row])
df7["day"] = pd.to_datetime(df7["date"]).dt.strftime("%m/%d")
df7["achievement_rate"] = (df7["completed"] / total * 100).round(0).astype(int)

chart_df = df7[["day", "achievement_rate"]].set_index("day")
st.bar_chart(chart_df, height=220)

# -----------------------------
# Pokedex (record so far) UI
# -----------------------------
st.divider()
st.subheader("📕 내 포켓몬 도감")

pokedex_count = len(st.session_state.pokedex)  # type: ignore[attr-defined]
progress = pokedex_count / 151
pcol1, pcol2, pcol3 = st.columns([1, 1, 2])

pcol1.metric("도감 등록", f"{pokedex_count} / 151")
pcol2.metric("진행도", f"{int(round(progress * 100))}%")

with pcol3:
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🧹 도감 초기화", use_container_width=True):
            st.session_state.pokedex = []  # type: ignore[attr-defined]
            st.session_state.pokedex_ids = set()  # type: ignore[attr-defined]
            st.success("도감을 초기화했어요.")
    with b2:
        # CSV 다운로드
        if pokedex_count > 0:
            df_poke = pd.DataFrame(st.session_state.pokedex)  # type: ignore[attr-defined]
            csv = df_poke.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "⬇️ CSV 다운로드",
                data=csv,
                file_name="pokedex.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("⬇️ CSV 다운로드", disabled=True, use_container_width=True)
    with b3:
        # 중복 제외하고 랜덤 1마리 미리보기용 필터(옵션)
        show_latest = st.toggle("최근 등록만 보기", value=True)

if pokedex_count == 0:
    st.info("아직 도감에 등록된 포켓몬이 없어요. 아래에서 리포트를 생성하면 자동으로 등록돼요!")
else:
    df_poke = pd.DataFrame(st.session_state.pokedex)  # type: ignore[attr-defined]
    df_poke = df_poke.sort_values(["dex_no"], ascending=True)

    if show_latest:
        # 최근 12마리만 카드처럼
        recent = df_poke.sort_values(["captured_at"], ascending=False).head(12)
        st.caption("최근 등록 포켓몬(최대 12마리)")
        grid = st.columns(6)
        for idx, row in enumerate(recent.to_dict("records")):
            with grid[idx % 6]:
                if row.get("artwork"):
                    st.image(row["artwork"], use_container_width=True)
                st.markdown(f"**#{int(row['dex_no']):03d} {row['name']}**")
                st.caption(f"타입: {row.get('types','-')}")
                st.caption(f"BST: {row.get('bst', 0)}")
    st.markdown("#### 도감 목록")
    st.dataframe(
        df_poke[
            [
                "dex_no",
                "name",
                "types",
                "bst",
                "hp",
                "attack",
                "defense",
                "sp_atk",
                "sp_def",
                "speed",
                "captured_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

# -----------------------------
# Generate report section
# -----------------------------
st.divider()
st.subheader("🧠 AI 코치 컨디션 리포트")

btn_col1, btn_col2 = st.columns([1, 2])
with btn_col1:
    generate = st.button("🚀 컨디션 리포트 생성", use_container_width=True)

weather_data = None
pokemon_data = None
ai_report = None

if generate:
    with st.spinner("날씨/포켓몬/리포트 생성 중..."):
        weather_data = get_weather(city, owm_api_key)
        pokemon_data = get_pokemon()

        # ✅ 도감 자동 기록 (중복은 무시)
        added = add_to_pokedex(pokemon_data)
        if pokemon_data and added:
            st.toast(f"도감에 등록!  #{int(pokemon_data.get('dex_no')):03d} {pokemon_data.get('name')}", icon="📕")
        elif pokemon_data and not added:
            st.toast("이미 도감에 있는 포켓몬이에요 (중복 등록 방지).", icon="✅")

        pokedex_count_now = len(st.session_state.pokedex)  # type: ignore[attr-defined]
        ai_report = generate_report(
            openai_api_key=openai_api_key,
            coach_style_key=coach_style_key,
            habits_checked=habits_checked,
            mood=mood,
            weather=weather_data,
            pokemon=pokemon_data,
            pokedex_count=pokedex_count_now,
        )

    # Results layout: Weather + Pokemon cards
    wcol, pcol = st.columns(2)

    with wcol:
        st.markdown("### 🌦️ 오늘의 날씨")
        if weather_data:
            desc = weather_data.get("description", "-")
            temp = weather_data.get("temp_c", "-")
            feels = weather_data.get("feels_like_c", "-")
            humidity = weather_data.get("humidity", "-")
            wind = weather_data.get("wind_mps", "-")
            st.info(
                f"**{weather_data.get('city')}**\n\n"
                f"- 상태: **{desc}**\n"
                f"- 기온: **{temp}°C** (체감 {feels}°C)\n"
                f"- 습도: **{humidity}%**\n"
                f"- 바람: **{wind} m/s**"
            )
        else:
            st.warning("날씨 정보를 가져오지 못했어요. (OpenWeatherMap API Key 확인)")

    with pcol:
        st.markdown("### 🧩 오늘의 파트너 포켓몬")
        if pokemon_data:
            name = pokemon_data.get("name", "?")
            dex_no = pokemon_data.get("dex_no", "?")
            types = pokemon_data.get("types", [])
            artwork = pokemon_data.get("artwork")

            head = f"**#{int(dex_no):03d} {name}**  ·  타입: **{', '.join(types) if types else '-'}**"
            st.success(head)

            img_col, stat_col = st.columns([1, 1.1])
            with img_col:
                if artwork:
                    st.image(artwork, caption=f"{name} (Official Artwork)", use_container_width=True)
                else:
                    st.caption("공식 아트워크를 찾지 못했어요.")

            with stat_col:
                stats = pokemon_data.get("stats", {})
                stat_series = pd.Series(
                    {
                        STAT_KR["hp"]: stats.get("hp", 0),
                        STAT_KR["attack"]: stats.get("attack", 0),
                        STAT_KR["defense"]: stats.get("defense", 0),
                        STAT_KR["special-attack"]: stats.get("special-attack", 0),
                        STAT_KR["special-defense"]: stats.get("special-defense", 0),
                        STAT_KR["speed"]: stats.get("speed", 0),
                    }
                )

                # st.bar_chart 빨간색 (가능하면 적용, 아니면 기본)
                try:
                    st.bar_chart(stat_series, height=240, color="#ff4b4b")
                except Exception:
                    st.bar_chart(stat_series, height=240)

        else:
            st.warning("포켓몬을 불러오지 못했어요. (PokeAPI 상태/네트워크 확인)")

    st.markdown("### 📝 AI 리포트")
    st.write(ai_report if ai_report else "리포트가 비어 있어요.")

    # Share text
    st.markdown("### 📣 공유용 텍스트")
    partner_line = "파트너 포켓몬: (불러오기 실패)"
    if pokemon_data:
        partner_line = f"파트너 포켓몬: #{int(pokemon_data.get('dex_no')):03d} {pokemon_data.get('name')} ({', '.join(pokemon_data.get('types', []))})"

    weather_line = "날씨: (불러오기 실패)"
    if weather_data:
        weather_line = f"날씨: {weather_data.get('city')} · {weather_data.get('description')} · {weather_data.get('temp_c')}°C"

    pokedex_count_now = len(st.session_state.pokedex)  # type: ignore[attr-defined]
    share_text = f"""[{today.isoformat()}] AI 습관 트래커(포켓몬)
- 달성률: {achievement_rate}%
- 완료: {completed}/{total}
- 기분: {mood}/10
- 도감: {pokedex_count_now}/151
- {weather_line}
- {partner_line}
"""
    st.code(share_text, language="text")

# -----------------------------
# Footer: API 안내
# -----------------------------
with st.expander("ℹ️ API 안내 / 문제 해결"):
    st.markdown(
        """
- **OpenAI API Key**: AI 코치 리포트 생성에 필요합니다.
- **OpenWeatherMap API Key**: 날씨 카드 표시(한국어/섭씨)에 필요합니다.
- **PokeAPI**: 포켓몬 정보는 별도 키 없이 호출됩니다.
- **도감 기록**: 브라우저 세션(세션 상태)에 저장됩니다. 새로고침/세션 종료 시 초기화될 수 있어요. (CSV 다운로드로 백업 추천)

**자주 생기는 이슈**
- 날씨가 안 나와요 → OpenWeatherMap 키가 맞는지, 도시명이 정확한지 확인하세요.
- 포켓몬이 안 나와요 → 네트워크/일시적 장애일 수 있어요. 다시 시도해 보세요.
- 리포트가 안 나와요 → OpenAI 키를 확인하고, 모델 접근 권한/요금 설정을 점검하세요.
"""
    )
