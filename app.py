import streamlit as st
import json
import os
import random
import hashlib
import datetime
from typing import Dict, Any, List, Optional, Tuple

APP_TITLE = "🐱 Cat Tarot + Card Dex"
DATA_PATH = "data.json"

MODEL_NAME = "gpt5mini"

TAROT_API_BASE = "https://tarotapi.dev/api/v1"
TAROT_ALL_CARDS_URL = f"{TAROT_API_BASE}/cards"
TAROT_RANDOM_URL = f"{TAROT_API_BASE}/cards/random?n=1"

CAT_FACTS_PRIMARY = "https://catfact.ninja/fact?max_length=180"
CAT_FACTS_FALLBACK = "https://cat-fact.herokuapp.com/facts/random?animal_type=cat&amount=1"

LOCAL_CAT_FACTS = [
    "고양이는 사람에게만 특별히 '야옹'을 쓴다는 얘기가 있다. (인간용 음성 패치)",
    "고양이는 낮잠을 실력처럼 잔다. 가끔은 직업처럼도 잔다.",
    "고양이의 꼬리는 감정의 안테나처럼 움직이지만, 진짜 뜻은 본인만 안다.",
    "고양이는 박스를 보면 들어가야 한다. 이유는 없다. 들어가야 한다.",
    "고양이는 가끔 아무것도 안 하는데도 바쁘다. 아주 바쁘다.",
    "고양이는 당신을 무시하는 게 아니라, 우선순위가 명확한 것이다.",
    "고양이는 발바닥 젤리를 소중히 보관한다. 귀여움도 같이 보관한다.",
    "고양이는 창밖을 보는 것으로 하루를 소비할 수 있다. 그게 계획이다.",
    "고양이는 눈을 천천히 깜빡이면 '괜찮다'고 말하는 셈이다. (대충 그런 느낌)",
    "고양이는 간식을 기억하고, 나머지는 선택적으로 기억한다.",
]

# ----------------------------
# Custom Cat Tarot (>=30)
# ----------------------------
CUSTOM_CARDS: List[Dict[str, Any]] = [
    {"id": "cat_major_00", "name_ko": "0. 바보 고양이", "arcana": "major", "suit": None, "keywords": ["즉흥", "우연", "허술함"], "image_url": None, "emoji": "🐾"},
    {"id": "cat_major_01", "name_ko": "1. 마술사 고양이", "arcana": "major", "suit": None, "keywords": ["기교", "손재주", "그럴싸"], "image_url": None, "emoji": "🪄"},
    {"id": "cat_major_02", "name_ko": "2. 여사제 고양이", "arcana": "major", "suit": None, "keywords": ["눈치", "비밀", "침묵"], "image_url": None, "emoji": "🌙"},
    {"id": "cat_major_03", "name_ko": "3. 여황제 고양이", "arcana": "major", "suit": None, "keywords": ["포근", "풍요", "간식"], "image_url": None, "emoji": "🧁"},
    {"id": "cat_major_04", "name_ko": "4. 황제 고양이", "arcana": "major", "suit": None, "keywords": ["영역", "통제", "규칙(있는 척)"], "image_url": None, "emoji": "👑"},
    {"id": "cat_major_05", "name_ko": "5. 교황 고양이", "arcana": "major", "suit": None, "keywords": ["의식", "전통", "엄숙"], "image_url": None, "emoji": "🕯️"},
    {"id": "cat_major_06", "name_ko": "6. 연인 고양이", "arcana": "major", "suit": None, "keywords": ["선택", "애착", "삐짐"], "image_url": None, "emoji": "💞"},
    {"id": "cat_major_07", "name_ko": "7. 전차 고양이", "arcana": "major", "suit": None, "keywords": ["돌진", "급발진", "질주"], "image_url": None, "emoji": "🏎️"},
    {"id": "cat_major_08", "name_ko": "8. 힘 고양이", "arcana": "major", "suit": None, "keywords": ["끈기", "발톱", "참는 척"], "image_url": None, "emoji": "💪"},
    {"id": "cat_major_09", "name_ko": "9. 은둔자 고양이", "arcana": "major", "suit": None, "keywords": ["혼자", "조용", "관찰"], "image_url": None, "emoji": "🕳️"},
    {"id": "cat_major_10", "name_ko": "10. 수레바퀴 고양이", "arcana": "major", "suit": None, "keywords": ["랜덤", "회전", "그냥됨"], "image_url": None, "emoji": "🎡"},
    {"id": "cat_major_11", "name_ko": "11. 정의 고양이", "arcana": "major", "suit": None, "keywords": ["공정", "판결", "심판(같은 척)"], "image_url": None, "emoji": "⚖️"},
    {"id": "cat_major_12", "name_ko": "12. 매달린 고양이", "arcana": "major", "suit": None, "keywords": ["역발상", "정지", "대롱"], "image_url": None, "emoji": "🪢"},
    {"id": "cat_major_13", "name_ko": "13. 큰 변화 고양이", "arcana": "major", "suit": None, "keywords": ["리셋", "변화", "갈아엎기"], "image_url": None, "emoji": "🌀"},
    {"id": "cat_major_14", "name_ko": "14. 절제 고양이", "arcana": "major", "suit": None, "keywords": ["적당", "균형", "눈치껏"], "image_url": None, "emoji": "🥛"},
    {"id": "cat_major_15", "name_ko": "15. 악마 고양이", "arcana": "major", "suit": None, "keywords": ["유혹", "집착", "레이저"], "image_url": None, "emoji": "😈"},
    {"id": "cat_major_16", "name_ko": "16. 타워 고양이", "arcana": "major", "suit": None, "keywords": ["붕괴", "깜짝", "넘어짐"], "image_url": None, "emoji": "🧱"},
    {"id": "cat_major_17", "name_ko": "17. 별 고양이", "arcana": "major", "suit": None, "keywords": ["반짝", "기분", "괜히희망"], "image_url": None, "emoji": "⭐"},
    {"id": "cat_major_18", "name_ko": "18. 달 고양이", "arcana": "major", "suit": None, "keywords": ["몽롱", "착각", "야행"], "image_url": None, "emoji": "🌙"},
    {"id": "cat_major_19", "name_ko": "19. 태양 고양이", "arcana": "major", "suit": None, "keywords": ["따뜻", "광합성", "누움"], "image_url": None, "emoji": "☀️"},
    {"id": "cat_major_20", "name_ko": "20. 심판 고양이", "arcana": "major", "suit": None, "keywords": ["재등장", "알림", "불시검문"], "image_url": None, "emoji": "📯"},
    {"id": "cat_major_21", "name_ko": "21. 세계 고양이", "arcana": "major", "suit": None, "keywords": ["완성", "한바퀴", "끝인척"], "image_url": None, "emoji": "🌏"},

    {"id": "cat_cups_01", "name_ko": "컵 1: 젖은 발", "arcana": "minor", "suit": "cups", "keywords": ["촉촉", "감정", "기분먼저"], "image_url": None, "emoji": "🥛"},
    {"id": "cat_cups_02", "name_ko": "컵 2: 두 그릇", "arcana": "minor", "suit": "cups", "keywords": ["관계", "나눔", "서로봄"], "image_url": None, "emoji": "🫶"},
    {"id": "cat_cups_03", "name_ko": "컵 3: 물그릇 파티", "arcana": "minor", "suit": "cups", "keywords": ["소동", "축하", "찰랑"], "image_url": None, "emoji": "🎉"},
    {"id": "cat_wands_01", "name_ko": "완드 1: 레이저 점", "arcana": "minor", "suit": "wands", "keywords": ["충동", "불꽃", "쫓아감"], "image_url": None, "emoji": "🔴"},
    {"id": "cat_wands_02", "name_ko": "완드 2: 창가 정찰", "arcana": "minor", "suit": "wands", "keywords": ["정찰", "계획", "밖궁금"], "image_url": None, "emoji": "🪟"},
    {"id": "cat_wands_03", "name_ko": "완드 3: 캣워크", "arcana": "minor", "suit": "wands", "keywords": ["진출", "확장", "영역넓힘"], "image_url": None, "emoji": "🧗"},
    {"id": "cat_swords_01", "name_ko": "소드 1: 날선 야옹", "arcana": "minor", "suit": "swords", "keywords": ["말", "생각", "정곡"], "image_url": None, "emoji": "🗡️"},
    {"id": "cat_swords_02", "name_ko": "소드 2: 눈감기", "arcana": "minor", "suit": "swords", "keywords": ["회피", "보류", "모른척"], "image_url": None, "emoji": "🙈"},
    {"id": "cat_swords_03", "name_ko": "소드 3: 심장 모양 털뭉치", "arcana": "minor", "suit": "swords", "keywords": ["서운", "찔림", "털빠짐"], "image_url": None, "emoji": "💔"},
    {"id": "cat_pents_01", "name_ko": "펜타 1: 동전 간식", "arcana": "minor", "suit": "pentacles", "keywords": ["현실", "보상", "득템"], "image_url": None, "emoji": "🪙"},
    {"id": "cat_pents_02", "name_ko": "펜타 2: 저글링 장난감", "arcana": "minor", "suit": "pentacles", "keywords": ["멀티", "균형", "양손냥"], "image_url": None, "emoji": "🤹"},
    {"id": "cat_pents_03", "name_ko": "펜타 3: 박스 공사", "arcana": "minor", "suit": "pentacles", "keywords": ["구조", "협업", "리모델링"], "image_url": None, "emoji": "📦"},

    {"id": "cat_odd_01", "name_ko": "이상한 카드: 박스", "arcana": "odd", "suit": None, "keywords": ["숨기", "넣기", "편함"], "image_url": None, "emoji": "📦"},
    {"id": "cat_odd_02", "name_ko": "이상한 카드: 새벽 우다다", "arcana": "odd", "suit": None, "keywords": ["폭주", "새벽", "질주"], "image_url": None, "emoji": "💨"},
    {"id": "cat_odd_03", "name_ko": "이상한 카드: 정체불명 부스러기", "arcana": "odd", "suit": None, "keywords": ["발견", "의문", "먹말"], "image_url": None, "emoji": "🧩"},
    {"id": "cat_odd_04", "name_ko": "이상한 카드: 비닐봉지", "arcana": "odd", "suit": None, "keywords": ["바스락", "유혹", "금지소리"], "image_url": None, "emoji": "🛍️"},
    {"id": "cat_odd_05", "name_ko": "이상한 카드: 벽의 그림자", "arcana": "odd", "suit": None, "keywords": ["사냥", "오해", "환상"], "image_url": None, "emoji": "👤"},
    {"id": "cat_odd_06", "name_ko": "이상한 카드: 엎어진 물", "arcana": "odd", "suit": None, "keywords": ["사고", "흔적", "모른척"], "image_url": None, "emoji": "💧"},
    {"id": "cat_odd_07", "name_ko": "이상한 카드: 청소기", "arcana": "odd", "suit": None, "keywords": ["위협", "도망", "소음"], "image_url": None, "emoji": "🧹"},
    {"id": "cat_odd_08", "name_ko": "이상한 카드: 느린 눈깜빡", "arcana": "odd", "suit": None, "keywords": ["평화", "괜찮음", "친화"], "image_url": None, "emoji": "😽"},
    {"id": "cat_odd_09", "name_ko": "이상한 카드: 발바닥 젤리", "arcana": "odd", "suit": None, "keywords": ["귀여움", "촉감", "비밀저장"], "image_url": None, "emoji": "🫘"},
    {"id": "cat_odd_10", "name_ko": "이상한 카드: 창문 감시", "arcana": "odd", "suit": None, "keywords": ["관찰", "정찰", "시간순삭"], "image_url": None, "emoji": "👀"},
]

CARD_INDEX_CUSTOM = {c["id"]: c for c in CUSTOM_CARDS}

# ----------------------------
# HTTP helpers (requests -> urllib fallback)
# ----------------------------
def http_get_json(url: str, timeout: int = 10) -> Tuple[bool, Any, str]:
    try:
        import requests  # type: ignore
        r = requests.get(url, timeout=timeout, headers={"Accept": "application/json"})
        if r.status_code >= 200 and r.status_code < 300:
            try:
                return True, r.json(), f"OK {r.status_code}"
            except Exception:
                return False, None, "JSON parse failed"
        return False, None, f"HTTP {r.status_code}"
    except Exception:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                text = resp.read().decode("utf-8", errors="replace")
                if status >= 200 and status < 300:
                    try:
                        return True, json.loads(text), f"OK {status}"
                    except Exception:
                        return False, None, "JSON parse failed"
                return False, None, f"HTTP {status}"
        except Exception as e:
            return False, None, str(e)

def http_post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int = 20) -> Tuple[int, str]:
    try:
        import requests  # type: ignore
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        return r.status_code, r.text
    except Exception:
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.getcode(), resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            return 0, str(e)

# ----------------------------
# Data storage
# ----------------------------
def today_str() -> str:
    return datetime.date.today().isoformat()

def load_data() -> Dict[str, Any]:
    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict):
                    return d
        except Exception:
            pass
    return {
        "settings": {"model": MODEL_NAME},
        "today": {"date": today_str(), "checked_in": False, "drawn": False, "reset_salt": 0},
        "draw_history": [],
        "dex": {},
    }

def save_data(data: Dict[str, Any]) -> None:
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_PATH)

def ensure_today(data: Dict[str, Any]) -> None:
    t = today_str()
    if "settings" not in data or not isinstance(data["settings"], dict):
        data["settings"] = {"model": MODEL_NAME}
    if "today" not in data or not isinstance(data["today"], dict):
        data["today"] = {"date": t, "checked_in": False, "drawn": False, "reset_salt": 0}
    if data["today"].get("date") != t:
        data["today"] = {"date": t, "checked_in": False, "drawn": False, "reset_salt": int(data["today"].get("reset_salt", 0))}
    if "draw_history" not in data or not isinstance(data["draw_history"], list):
        data["draw_history"] = []
    if "dex" not in data or not isinstance(data["dex"], dict):
        data["dex"] = {}

def get_today_record(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    t = today_str()
    for rec in reversed(data.get("draw_history", [])):
        if rec.get("date") == t:
            return rec
    return None

def has_drawn_today(data: Dict[str, Any]) -> bool:
    rec = get_today_record(data)
    return bool(rec and rec.get("cards"))

def reset_today_draw(data: Dict[str, Any]) -> None:
    t = today_str()
    data["draw_history"] = [r for r in data.get("draw_history", []) if r.get("date") != t]
    data["today"]["drawn"] = False

def dex_update(data: Dict[str, Any], card_id: str, date_s: str, one_liner: str, reading: str, vibe_tags: List[str]) -> None:
    dex = data.setdefault("dex", {})
    entry = dex.get(card_id)
    if not entry:
        entry = {"count": 0, "first_seen": date_s, "last_seen": date_s, "notes": []}
        dex[card_id] = entry
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last_seen"] = date_s
    if not entry.get("first_seen"):
        entry["first_seen"] = date_s
    notes = entry.get("notes", [])
    if not isinstance(notes, list):
        notes = []
    notes.append({"date": date_s, "one_liner": one_liner, "reading": reading, "vibe_tags": vibe_tags})
    entry["notes"] = notes[-30:]

# ----------------------------
# External APIs
# ----------------------------
@st.cache_data(ttl=60 * 60, show_spinner=False)
def fetch_tarot_cards_cached() -> Tuple[List[Dict[str, Any]], str]:
    ok, obj, msg = http_get_json(TAROT_ALL_CARDS_URL, timeout=12)
    if not ok or not isinstance(obj, dict) or "cards" not in obj:
        return [], f"FAIL: {msg}"
    cards = obj.get("cards", [])
    if not isinstance(cards, list) or not cards:
        return [], "FAIL: empty"
    return cards, f"OK: {len(cards)}"

def normalize_tarot_cards(raw_cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for c in raw_cards:
        if not isinstance(c, dict):
            continue
        ns = str(c.get("name_short", "")).strip()
        name = str(c.get("name", "")).strip()
        t = str(c.get("type", "")).strip().lower()
        suit = c.get("suit")
        suit_s = str(suit).strip().lower() if suit is not None else None
        if not ns or not name:
            continue
        emoji = "🔮"
        if suit_s == "cups":
            emoji = "🥛"
        elif suit_s == "wands":
            emoji = "🪄"
        elif suit_s == "swords":
            emoji = "🗡️"
        elif suit_s == "pentacles":
            emoji = "🪙"
        elif t == "major":
            emoji = "✨"
        out.append({
            "id": f"tarot_{ns}",
            "name_ko": f"타로: {name}",
            "arcana": "major" if t == "major" else "minor" if t == "minor" else "odd",
            "suit": suit_s,
            "keywords": [t] + ([suit_s] if suit_s else []) + ["RWS"],
            "image_url": None,
            "emoji": emoji,
            "source": "tarot_api",
            "raw": {
                "meaning_up": c.get("meaning_up", ""),
                "meaning_rev": c.get("meaning_rev", ""),
                "desc": c.get("desc", ""),
            }
        })
    return out

@st.cache_data(ttl=10 * 60, show_spinner=False)
def fetch_cat_fact_cached() -> Tuple[Optional[str], str]:
    ok, obj, msg = http_get_json(CAT_FACTS_PRIMARY, timeout=10)
    if ok and isinstance(obj, dict) and obj.get("fact"):
        return str(obj["fact"]).strip(), f"OK(primary)"
    ok2, obj2, msg2 = http_get_json(CAT_FACTS_FALLBACK, timeout=12)
    if ok2:
        if isinstance(obj2, dict) and obj2.get("text"):
            return str(obj2["text"]).strip(), f"OK(fallback)"
        if isinstance(obj2, list) and obj2 and isinstance(obj2[0], dict) and obj2[0].get("text"):
            return str(obj2[0]["text"]).strip(), f"OK(fallback)"
    return None, f"FAIL: {msg} / {msg2 if 'msg2' in locals() else ''}".strip()

# ----------------------------
# OpenAI: generate reading
# ----------------------------
def build_openai_payload(card: Dict[str, Any], cat_fact: Optional[str], mode_label: Optional[str]) -> Dict[str, Any]:
    label = f"[{mode_label}] " if mode_label else ""
    fact_line = f"고양이 사실(소재): {cat_fact}" if cat_fact else "고양이 사실(소재): (없음)"
    system = (
        "너는 '고양이 타로' 리더다. 진지한 척은 가능하지만, "
        "동기부여/자기계발/훈계/조언/목표설정/평가/지시를 절대 하지 않는다. "
        "특히 '해야 한다, 바꿔라, 목표, 노력, 동기' 같은 뉘앙스 금지. "
        "의료/법률/투자 조언 금지. "
        "결론은 가볍고 재미있고 약간 무책임해야 한다. "
        "사용자의 행동(성공/실패/체크인)을 언급하거나 평가하지 말고, 카드 자체의 분위기만 말하라. "
        "출력은 반드시 JSON 하나로만."
    )
    user = (
        f"{fact_line}\n\n"
        f"카드: {label}{card.get('name_ko')}\n"
        f"arcana: {card.get('arcana')}\n"
        f"suit: {card.get('suit')}\n"
        f"keywords: {', '.join(card.get('keywords', []) or [])}\n\n"
        "반드시 아래 JSON 스키마로만 출력:\n"
        "{\n"
        '  "one_liner": "string",\n'
        '  "reading": "string (2~4 sentences, Korean)",\n'
        '  "vibe_tags": ["string", "..."]\n'
        "}\n"
        "규칙:\n"
        "- 조언/훈계/동기부여/자기계발 금지\n"
        "- '해야 한다/바꿔라/목표/노력/동기' 류 표현 금지\n"
        "- 카드의 분위기 + 고양이 사실을 '은근히' 섞기(과하면 안 됨)\n"
        "- 책임지지 않는 톤 유지\n"
    )
    return {
        "model": MODEL_NAME,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }

def call_openai(api_key: str, card: Dict[str, Any], cat_fact: Optional[str], mode_label: Optional[str]) -> Optional[Dict[str, Any]]:
    if not api_key:
        return None
    url = "https://api.openai.com/v1/responses"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = build_openai_payload(card, cat_fact, mode_label)
    status, text = http_post_json(url, headers, payload, timeout=25)
    if status < 200 or status >= 300:
        return None
    try:
        obj = json.loads(text)
        out_text = obj.get("output_text") or ""
        if not out_text:
            out = obj.get("output", [])
            parts = []
            if isinstance(out, list):
                for item in out:
                    content = item.get("content", [])
                    if isinstance(content, list):
                        for c in content:
                            if c.get("type") in ("output_text", "text"):
                                t = c.get("text") or c.get("content")
                                if t:
                                    parts.append(str(t))
            out_text = "\n".join(parts).strip()
        if not out_text:
            return None
        data = json.loads(out_text)
        if not isinstance(data, dict):
            return None
        if "one_liner" not in data or "reading" not in data or "vibe_tags" not in data:
            return None
        one = str(data.get("one_liner", "")).strip()
        reading = str(data.get("reading", "")).strip()
        tags = data.get("vibe_tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = [str(x).strip() for x in tags if str(x).strip()][:3]
        if not one or not reading:
            return None
        return {"one_liner": one, "reading": reading, "vibe_tags": tags}
    except Exception:
        return None

LOCAL_VIBE_POOL = ["바스락", "몽롱", "반짝", "촉촉", "쿨", "찔끔", "우다다", "느긋", "수상함", "포근", "간식", "박스"]
LOCAL_ONE_LINERS = [
    "오늘은 이 카드가 출근했다.",
    "그럴싸하지만 책임은 없다.",
    "고양이는 알고, 카드는 모른다.",
    "이건 예언이 아니라 분위기다.",
    "아무튼 나왔다. 축하(?)",
]

def local_reading(card: Dict[str, Any], cat_fact: Optional[str], mode_label: Optional[str]) -> Dict[str, Any]:
    seed_src = f"{today_str()}::{card.get('id')}::{mode_label or ''}::{cat_fact or ''}"
    seed = int(hashlib.sha256(seed_src.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    one_liner = rng.choice(LOCAL_ONE_LINERS)
    tags = rng.sample(LOCAL_VIBE_POOL, k=rng.randint(1, 3))
    kw = card.get("keywords", []) or []
    label = f"{mode_label} " if mode_label else ""
    fact = cat_fact or rng.choice(LOCAL_CAT_FACTS)
    s1 = f"{label}{card.get('name_ko')}는(은) {', '.join(kw[:2]) if kw else '묘한 기운'} 쪽으로 기운다."
    s2 = f"그리고 참고로: {fact}"
    s3 = rng.choice(["딱히 결론은 없다.", "이 정도면 충분히 신비롭다.", "아무튼 고양이는 평온하다."])
    reading = " ".join([s1, s2, s3])
    return {"one_liner": one_liner, "reading": reading, "vibe_tags": tags}

# ----------------------------
# Draw logic
# ----------------------------
def seed_for_today(reset_salt: int, mode: int) -> int:
    raw = f"{today_str()}::{reset_salt}::{mode}".encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)

def pick_cards(pool: List[Dict[str, Any]], mode: int, reset_salt: int) -> List[Dict[str, Any]]:
    rng = random.Random(seed_for_today(reset_salt, mode))
    if len(pool) >= mode:
        return rng.sample(pool, k=mode)
    # edge
    picks = []
    for _ in range(mode):
        picks.append(rng.choice(pool))
    return picks

# ----------------------------
# UI helpers
# ----------------------------
def badge_for(card: Dict[str, Any]) -> str:
    arc = card.get("arcana")
    suit = card.get("suit")
    if arc == "major":
        return "✨ 메이저"
    if arc == "minor":
        if suit == "cups":
            return "🥛 컵"
        if suit == "wands":
            return "🪄 완드"
        if suit == "swords":
            return "🗡️ 소드"
        if suit == "pentacles":
            return "🪙 펜타"
        return "🧩 마이너"
    return "🌀 이상한"

def render_card(card: Dict[str, Any], reading: Dict[str, Any]) -> None:
    emoji = card.get("emoji") or "🐱"
    img = card.get("image_url")
    with st.container(border=True):
        cols = st.columns([1, 2])
        with cols[0]:
            if img:
                st.image(img, use_container_width=True)
            else:
                st.markdown(
                    f"""
                    <div style="height:170px;border-radius:16px;border:1px solid rgba(255,255,255,0.14);
                    display:flex;align-items:center;justify-content:center;font-size:48px;background:rgba(255,255,255,0.06);">
                        {emoji}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.caption(badge_for(card))
        with cols[1]:
            st.subheader(card.get("name_ko", ""))
            st.markdown(f"**{reading.get('one_liner','')}**")
            st.write(reading.get("reading", ""))
            tags = reading.get("vibe_tags", []) or []
            if tags:
                st.caption(" ".join([f"`#{t}`" for t in tags]))

def collection_stats(data: Dict[str, Any], all_cards: List[Dict[str, Any]]) -> Tuple[int, int, float]:
    total = len(all_cards)
    dex = data.get("dex", {})
    got = 0
    for c in all_cards:
        cid = c["id"]
        if cid in dex and int(dex[cid].get("count", 0)) > 0:
            got += 1
    return total, got, (got / total if total else 0.0)

# ----------------------------
# App init
# ----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🐱", layout="wide")
st.title(APP_TITLE)
st.caption("의미 있는 척은 가능. 책임은 없음. (카드도, 고양이도)")

data = load_data()
ensure_today(data)

if "data" not in st.session_state:
    st.session_state["data"] = data

if "api_status" not in st.session_state:
    st.session_state["api_status"] = {"tarot": "—", "catfacts": "—"}

# Fetch tarot cards once (cached)
raw_tarot, tarot_status = fetch_tarot_cards_cached()
st.session_state["api_status"]["tarot"] = tarot_status
tarot_cards_norm = normalize_tarot_cards(raw_tarot) if raw_tarot else []

# Build combined pool
COMBINED_POOL: List[Dict[str, Any]] = []
COMBINED_POOL.extend(tarot_cards_norm)
for c in CUSTOM_CARDS:
    cc = dict(c)
    cc["source"] = "custom"
    COMBINED_POOL.append(cc)

CARD_INDEX: Dict[str, Dict[str, Any]] = {c["id"]: c for c in COMBINED_POOL}

def persist():
    save_data(st.session_state["data"])

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", help="키가 없으면 로컬 템플릿으로만 굴러감")
    st.caption(f"모델: `{MODEL_NAME}` (고정)")

    st.divider()
    st.subheader("외부 API 상태")
    st.write(f"- Tarot API: {st.session_state['api_status'].get('tarot','—')}")
    st.write(f"- Cat Facts API: {st.session_state['api_status'].get('catfacts','—')}")

    if st.button("🐱 고양이 사실 테스트 호출", use_container_width=True):
        fact, status = fetch_cat_fact_cached()
        st.session_state["api_status"]["catfacts"] = status
        if fact:
            st.success(f"OK: {fact[:120] + ('…' if len(fact) > 120 else '')}")
        else:
            st.warning("못 가져옴. 로컬로 대체 가능.")

    st.divider()

    if st.button("🧽 오늘 리셋", use_container_width=True):
        st.session_state["confirm_today_reset"] = True
    if st.session_state.get("confirm_today_reset"):
        st.warning("오늘 뽑기 기록만 지울까? (도감은 남음)")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("응, 지워", use_container_width=True, key="do_today_reset"):
                reset_today_draw(st.session_state["data"])
                st.session_state["data"]["today"]["checked_in"] = False
                st.session_state["data"]["today"]["reset_salt"] = int(st.session_state["data"]["today"].get("reset_salt", 0)) + 1
                st.session_state["confirm_today_reset"] = False
                persist()
                st.success("오늘만 싹 지움. 아무 일도 없었다.")
                st.rerun()
        with c2:
            if st.button("아냐", use_container_width=True, key="cancel_today_reset"):
                st.session_state["confirm_today_reset"] = False
                st.rerun()

    st.divider()

    if st.button("💣 전체 초기화", use_container_width=True):
        st.session_state["confirm_full_reset"] = True
    if st.session_state.get("confirm_full_reset"):
        st.error("전체 데이터를 초기화할까? (도감/기록 전부 삭제)")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("응, 다 날려", use_container_width=True, key="do_full_reset"):
                st.session_state["data"] = {
                    "settings": {"model": MODEL_NAME},
                    "today": {"date": today_str(), "checked_in": False, "drawn": False, "reset_salt": 0},
                    "draw_history": [],
                    "dex": {},
                }
                st.session_state["confirm_full_reset"] = False
                persist()
                st.success("완전 초기화. 새 고양이 인생 시작.")
                st.rerun()
        with c2:
            if st.button("취소", use_container_width=True, key="cancel_full_reset"):
                st.session_state["confirm_full_reset"] = False
                st.rerun()

# ----------------------------
# Tabs
# ----------------------------
tab_draw, tab_dex = st.tabs(["🎴 오늘의 뽑기", "📚 카드 도감"])

# ----------------------------
# Tab: Draw
# ----------------------------
with tab_draw:
    left, right = st.columns([1.05, 1.0], gap="large")
    d = st.session_state["data"]
    ensure_today(d)

    with left:
        st.subheader("오늘의 상태")
        t = today_str()
        already = has_drawn_today(d)

        cols = st.columns([1, 1, 1])
        with cols[0]:
            if st.button("✅ 했음", use_container_width=True, disabled=already):
                d["today"]["checked_in"] = True
                persist()
                st.rerun()
        with cols[2]:
            st.metric("오늘", t)

        if already:
            st.info("오늘은 이미 뽑았다. 내일 또 와라. (또는 사이드바에서 오늘 리셋)")
        else:
            if d["today"].get("checked_in"):
                st.success("뽑기 가능 상태. (의식 시작 가능)")
            else:
                st.warning("아직 뽑기 잠김. '했음'을 눌러야 카드가 나온다.")

        st.divider()
        st.subheader("뽑기 설정")
        mode = st.radio("카드 모드", options=[1, 3], format_func=lambda x: "1장" if x == 1 else "3장", horizontal=True)
        note = st.text_input("메모(선택)", placeholder="오늘의 아무 말…", max_chars=140)

        can_draw = bool(d["today"].get("checked_in")) and not already
        draw_btn = st.button("🎲 뽑기", use_container_width=True, disabled=not can_draw)

        if draw_btn:
            fact, cstatus = fetch_cat_fact_cached()
            st.session_state["api_status"]["catfacts"] = cstatus
            if not fact:
                fact = random.choice(LOCAL_CAT_FACTS)

            reset_salt = int(d["today"].get("reset_salt", 0))
            cards = pick_cards(COMBINED_POOL, mode=mode, reset_salt=reset_salt)

            labels = None
            if mode == 3:
                labels = ["과거(같은 것)", "현재(같은 것)", "아무말(진짜 아무말)"]

            cards_out = []
            for i, card in enumerate(cards):
                mode_label = labels[i] if labels else None
                reading = call_openai(api_key, card, fact, mode_label)
                if not reading:
                    reading = local_reading(card, fact, mode_label)

                cards_out.append({
                    "id": card["id"],
                    "name": card.get("name_ko", ""),
                    "source": card.get("source", "custom"),
                    "mode_label": mode_label,
                    "one_liner": reading["one_liner"],
                    "reading": reading["reading"],
                    "vibe_tags": reading.get("vibe_tags", []),
                    "cat_fact": fact,
                })

                dex_update(d, card["id"], t, reading["one_liner"], reading["reading"], reading.get("vibe_tags", []))

            rec = {"date": t, "mode": mode, "cards": cards_out, "note": note or ""}
            d["draw_history"].append(rec)
            d["today"]["drawn"] = True
            persist()
            st.rerun()

    with right:
        st.subheader("결과")
        rec = get_today_record(st.session_state["data"])
        if not rec:
            st.caption("아직 오늘 결과가 없다. (뽑으면 생김)")
        else:
            st.caption(f"모드: {('1장' if rec.get('mode') == 1 else '3장')} · 기록됨")
            if rec.get("note"):
                st.caption(f"메모: {rec.get('note')}")
            st.write("")
            for cinfo in rec.get("cards", []):
                if cinfo.get("mode_label"):
                    st.caption(f"📍 {cinfo['mode_label']}")
                card = CARD_INDEX.get(cinfo["id"], {"id": cinfo["id"], "name_ko": cinfo.get("name", cinfo["id"]), "arcana": "odd", "suit": None, "keywords": [], "image_url": None, "emoji": "🐱"})
                reading = {"one_liner": cinfo.get("one_liner", ""), "reading": cinfo.get("reading", ""), "vibe_tags": cinfo.get("vibe_tags", [])}
                render_card(card, reading)

# ----------------------------
# Tab: Dex
# ----------------------------
with tab_dex:
    d = st.session_state["data"]
    total, got, rate = collection_stats(d, COMBINED_POOL)
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 카드", total)
    c2.metric("수집 카드", got)
    c3.metric("수집률", f"{rate*100:.1f}%")

    st.divider()

    dex = d.get("dex", {})
    got_only = st.checkbox("수집한 카드만 보기", value=False)
    sort_opt = st.selectbox("정렬", options=["등장횟수 ↓", "이름순"], index=0)

    rows = []
    for card in COMBINED_POOL:
        cid = card["id"]
        entry = dex.get(cid)
        count = int(entry.get("count", 0)) if entry else 0
        unlocked = count > 0
        if got_only and not unlocked:
            continue
        rows.append({
            "id": cid,
            "name": card.get("name_ko", ""),
            "badge": badge_for(card),
            "emoji": card.get("emoji") or "🐱",
            "locked": not unlocked,
            "count": count,
            "first_seen": (entry.get("first_seen", "") if entry else ""),
            "last_seen": (entry.get("last_seen", "") if entry else ""),
            "source": card.get("source", "custom"),
        })

    if sort_opt == "등장횟수 ↓":
        rows.sort(key=lambda r: (r["count"], r["name"]), reverse=True)
    else:
        rows.sort(key=lambda r: r["name"])

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.subheader("목록")
        if not rows:
            st.caption("표시할 카드가 없다. (필터를 풀거나 먼저 뽑자)")
        for r in rows:
            lock_icon = "🔓" if not r["locked"] else "🔒"
            title = f"{lock_icon} {r['emoji']} {r['name']} · {r['badge']}"
            meta = f"등장 {r['count']}회"
            if r["first_seen"]:
                meta += f" · 첫등장 {r['first_seen']}"
            if r["last_seen"]:
                meta += f" · 최근 {r['last_seen']}"
            meta += f" · 출처 {r['source']}"
            with st.expander(title, expanded=False):
                st.caption(meta)
                if st.button("이 카드 보기", key=f"pick_{r['id']}", use_container_width=True):
                    st.session_state["selected_card_id"] = r["id"]

    with right:
        st.subheader("카드 상세")
        sel = st.session_state.get("selected_card_id")
        if not sel:
            st.caption("왼쪽에서 카드를 선택하면 여기에 뜬다.")
        else:
            card = CARD_INDEX.get(sel)
            entry = dex.get(sel, {})
            if not card:
                st.error("카드를 못 찾았다. (이상한 일)")
            else:
                with st.container(border=True):
                    st.markdown(f"### {card.get('emoji','🐱')} {card.get('name_ko','')}")
                    st.caption(f"{badge_for(card)} · 출처 {card.get('source','custom')}")
                    st.metric("등장 횟수", int(entry.get("count", 0)))
                    st.caption(f"첫등장: {entry.get('first_seen','-')}  ·  최근: {entry.get('last_seen','-')}")

                    st.divider()
                    st.caption("최근 해석 히스토리 (최대 5개)")
                    notes = entry.get("notes", [])
                    if not isinstance(notes, list) or not notes:
                        st.caption("아직 기록이 없다. (뽑으면 생김)")
                    else:
                        for item in notes[-5:][::-1]:
                            dt = item.get("date", "")
                            one = item.get("one_liner", "")
                            read = item.get("reading", "")
                            tags = item.get("vibe_tags", []) or []
                            st.markdown(f"**{dt}** · {one}")
                            if tags:
                                st.caption(" ".join([f"`#{t}`" for t in tags]))
                            st.write(read)
                            st.write("")

                    st.divider()
                    st.caption("이 카드가 등장했던 기록 (최대 5개)")
                    hist = []
                    for rec in reversed(d.get("draw_history", [])):
                        for cinfo in rec.get("cards", []):
                            if cinfo.get("id") == sel:
                                hist.append({
                                    "date": rec.get("date"),
                                    "mode": rec.get("mode"),
                                    "mode_label": cinfo.get("mode_label") or "",
                                    "one_liner": cinfo.get("one_liner") or "",
                                })
                        if len(hist) >= 5:
                            break
                    if not hist:
                        st.caption("등장 기록이 없다. (근데 도감엔 왜 있지?)")
                    else:
                        for h in hist[:5]:
                            pos = f" · {h['mode_label']}" if h["mode_label"] else ""
                            st.write(f"- {h['date']} ({'1장' if h['mode']==1 else '3장'}{pos}): {h['one_liner']}")
