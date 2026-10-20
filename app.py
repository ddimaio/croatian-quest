import asyncio
import base64
import html
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
try:
    import edge_tts
except ImportError:  # Keep the course usable until optional audio dependencies are installed.
    edge_tts = None

st.set_page_config(page_title="Bok! — Croatian Quest", page_icon="🇭🇷", layout="centered")
word_order_component = st.components.v1.declare_component(
    "croatian_word_order", path=str(Path(__file__).parent / "components" / "word_order")
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@600;700;800&display=swap');
:root { --ink:#193b35; --muted:#75847e; --green:#58cc7a; --deep:#2eaa58; --cream:#f8fbf7; --line:#e5ece6; }
.stApp { background:var(--cream); color:var(--ink); font-family:'DM Sans',sans-serif; }
.block-container { max-width:780px; padding-top:2.4rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:'Manrope',sans-serif !important; color:var(--ink); }
.brand { display:flex; align-items:center; gap:12px; font-family:'Manrope',sans-serif; font-weight:800; font-size:1.15rem; letter-spacing:-.03em; }
.brand-mark { width:40px; height:40px; display:grid; place-items:center; border-radius:14px; background:#e4f8e9; font-size:1.35rem; }
.eyebrow { color:var(--deep); font-size:.76rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
.hero { padding:1.3rem 0 1rem; }
.hero h1 { font-size:2.65rem; line-height:1.08; letter-spacing:-.055em; margin:.55rem 0; }
.hero p { color:var(--muted); font-size:1.05rem; margin:0; }
.stat { background:white; border:1px solid var(--line); border-radius:18px; padding:14px 16px; text-align:center; }
.stat-num { font-family:'Manrope'; font-size:1.25rem; font-weight:800; }
.stat-label { color:var(--muted); font-size:.75rem; font-weight:700; }
.lesson-card { background:white; border:1px solid var(--line); border-radius:22px; padding:22px; margin:12px 0; }
.prompt { font-family:'Manrope'; font-size:1.45rem; font-weight:800; letter-spacing:-.03em; line-height:1.3; }
.pill { display:inline-block; background:#eef8f0; color:#268447; font-size:.75rem; font-weight:800; padding:5px 10px; border-radius:99px; }
hr { border-color:var(--line); }
[data-testid="stMetric"] { background:white; padding:12px 16px; border-radius:16px; border:1px solid var(--line); }
.stButton>button { border-radius:13px; font-weight:800; min-height:48px; border:1px solid var(--line); }
.stButton>button[kind="primary"] { background:var(--green); border-color:var(--green); color:#123624; }
.stButton>button[kind="primary"]:hover { background:var(--deep); border-color:var(--deep); color:white; }
.stProgress>div>div>div { background:var(--green); }
[data-testid="stRadio"] [role="radiogroup"] label {
  box-sizing:border-box; width:100%; min-height:56px; display:flex; align-items:center;
  padding:10px 14px; gap:12px; white-space:normal;
  border:1px solid var(--line); border-radius:14px; background:#fff;
}
[data-testid="stRadio"] [role="radiogroup"] label p {
  font-size:1rem !important; line-height:1.45 !important; margin:0;
  white-space:normal; overflow-wrap:anywhere;
}
@media (max-width:640px) {
  .block-container { padding-left:1rem; padding-right:1rem; }
  [data-testid="stRadio"] [role="radiogroup"] label { min-height:60px; padding:12px; }
  [data-testid="stRadio"] [role="radiogroup"] label p { font-size:1.1rem !important; }
  .lesson-card { padding:16px; }
}
"""
st.markdown(CSS, unsafe_allow_html=True)

# Starter course: content lessons introduce vocabulary/grammar; review lessons draw from one course-wide deck.
STARTER_COURSE = [{'id': 'lesson-01-greetings',
  'number': 1,
  'title': 'Say hello',
  'topic': 'Greetings',
  'lesson_type': 'vocabulary',
  'difficulty': 1,
  'level': 'Beginner',
  'description': 'Greet people and use a few polite words.',
  'vocabulary': [{'hr': 'Bok', 'en': 'Hi / bye'},
                 {'hr': 'Dobar dan', 'en': 'Good day'},
                 {'hr': 'Dobro jutro', 'en': 'Good morning'},
                 {'hr': 'Hvala', 'en': 'Thank you'},
                 {'hr': 'Molim', 'en': 'Please / you’re welcome'},
                 {'hr': 'Doviđenja', 'en': 'Goodbye'}],
  'exercises': [{'type': 'multiple_choice',
                 'prompt': 'How do you say ‘Hi’ in Croatian?',
                 'options': ['Bok', 'Hvala', 'Molim', 'Doviđenja'],
                 'answer': 'Bok',
                 'hint': 'It can mean both hi and bye.'},
                {'type': 'translate_en_to_hr', 'prompt': 'Good morning', 'answer': 'Dobro jutro'},
                {'type': 'translate_hr_to_en', 'prompt': 'Hvala', 'answer': 'Thank you'},
                {'type': 'translate_en_to_hr', 'prompt': 'Good day', 'answer': 'Dobar dan'},
                {'type': 'fill_blank', 'prompt': 'Complete: Do___đenja (goodbye)', 'answer': 'vi'},
                {'type': 'fill_blank', 'prompt': 'Complete: Dobar ___ (good day)', 'answer': 'dan'},
                {'type': 'reorder_words',
                 'prompt': 'Build the greeting: ‘Dobar dan, Ana.’',
                 'words': ['dan,', 'Ana.', 'Dobar'],
                 'answer': ['Dobar', 'dan,', 'Ana.']},
                {'type': 'comprehension',
                 'passage': 'Ana: Dobar dan! Marko: Bok, Ana! Ana: Hvala!',
                 'prompt': 'Who says ‘Bok’?',
                 'options': ['Ana', 'Marko', 'They both do'],
                 'answer': 'Marko'}]},
 {'id': 'lesson-02-introductions',
  'number': 2,
  'title': 'Introduce yourself',
  'topic': 'Names and pronouns',
  'lesson_type': 'grammar',
  'difficulty': 1,
  'level': 'Beginner',
  'description': 'Learn a first sentence pattern and when Croatian drops pronouns.',
  'grammar_note': 'Zovem se means ‘I am called’. Croatian often leaves out subject pronouns because the verb '
                  'ending tells you who is speaking. Use Ja sam for emphasis: ‘I am…’.',
  'vocabulary': [{'hr': 'Zovem se', 'en': 'My name is / I am called'},
                 {'hr': 'Ja sam', 'en': 'I am'},
                 {'hr': 'Kako se zoveš?', 'en': 'What is your name?'},
                 {'hr': 'Drago mi je', 'en': 'Nice to meet you'}],
  'exercises': [{'type': 'translate_en_to_hr', 'prompt': 'My name is Ana', 'answer': 'Zovem se Ana'},
                {'type': 'translate_hr_to_en', 'prompt': 'Kako se zoveš?', 'answer': 'What is your name?'},
                {'type': 'multiple_choice',
                 'prompt': 'What does ‘Drago mi je’ mean?',
                 'options': ['Nice to meet you', 'Good morning', 'Where are you?'],
                 'answer': 'Nice to meet you'},
                {'type': 'translate_en_to_hr',
                 'prompt': 'I am Marko',
                 'answer': 'Ja sam Marko',
                 'hint': 'Use Ja sam to emphasize ‘I am’.'},
                {'type': 'reorder_words',
                 'prompt': 'Put the words in order: ‘My name is Ana.’',
                 'words': ['Ana.', 'se', 'Zovem'],
                 'answer': ['Zovem', 'se', 'Ana.']},
                {'type': 'comprehension',
                 'passage': 'Zovem se Luka. Drago mi je.',
                 'prompt': 'What is his name?',
                 'options': ['Luka', 'Ana', 'Marko'],
                 'answer': 'Luka'},
                {'type': 'translate_hr_to_en', 'prompt': 'Drago mi je', 'answer': 'Nice to meet you'},
                {'type': 'fill_blank',
                 'prompt': 'Complete the question: Kako se ___? (What is your name?)',
                 'answer': 'zoveš'}]},
 {'id': 'lesson-03-cafe',
  'number': 3,
  'title': 'At the café',
  'topic': 'Drinks and ordering',
  'lesson_type': 'vocabulary',
  'difficulty': 2,
  'level': 'Beginner',
  'description': 'A themed vocabulary lesson for ordering a drink.',
  'vocabulary': [{'hr': 'Kava', 'en': 'Coffee'},
                 {'hr': 'Voda', 'en': 'Water'},
                 {'hr': 'Čaj', 'en': 'Tea'},
                 {'hr': 'Sok', 'en': 'Juice'},
                 {'hr': 'Molim', 'en': 'Please'},
                 {'hr': 'Račun, molim', 'en': 'The bill, please'}],
  'exercises': [{'type': 'translate_hr_to_en', 'prompt': 'Kava', 'answer': 'Coffee'},
                {'type': 'translate_en_to_hr', 'prompt': 'Water', 'answer': 'Voda'},
                {'type': 'multiple_choice',
                 'prompt': 'What does ‘Račun, molim’ mean?',
                 'options': ['The bill, please', 'A cup of tea', 'Good evening'],
                 'answer': 'The bill, please'},
                {'type': 'translate_en_to_hr', 'prompt': 'Tea', 'answer': 'Čaj'},
                {'type': 'translate_hr_to_en', 'prompt': 'Sok', 'answer': 'Juice'},
                {'type': 'reorder_words',
                 'prompt': 'Put the order together: ‘One coffee, please.’',
                 'words': ['molim.', 'kavu,', 'Jednu'],
                 'answer': ['Jednu', 'kavu,', 'molim.']},
                {'type': 'comprehension',
                 'passage': 'Ana: Jednu kavu, molim. Konobar: Izvolite.',
                 'prompt': 'What does Ana order?',
                 'options': ['Coffee', 'Tea', 'Water'],
                 'answer': 'Coffee'},
                {'type': 'fill_blank',
                 'prompt': 'Complete the order: Čaj, ___. (Tea, please.)',
                 'answer': 'molim'}]},
 {'id': 'lesson-04-review',
  'number': 4,
  'title': 'Review: first conversations',
  'topic': 'Greetings, names, and café words',
  'lesson_type': 'review',
  'difficulty': 2,
  'level': 'Beginner',
  'description': 'Revisit due words from every lesson you have studied so far.',
  'vocabulary': [],
  'exercises': []},
 {'id': 'lesson-05-people',
  'number': 5,
  'title': 'People around you',
  'topic': 'Family and people',
  'lesson_type': 'vocabulary',
  'difficulty': 2,
  'level': 'Beginner',
  'description': 'Learn words for family and the people you meet.',
  'vocabulary': [{'hr': 'Obitelj', 'en': 'Family'},
                 {'hr': 'Majka', 'en': 'Mother'},
                 {'hr': 'Otac', 'en': 'Father'},
                 {'hr': 'Prijatelj', 'en': 'Friend (male)'},
                 {'hr': 'Prijateljica', 'en': 'Friend (female)'}],
  'exercises': [{'type': 'translate_en_to_hr', 'prompt': 'Mother', 'answer': 'Majka'},
                {'type': 'translate_hr_to_en', 'prompt': 'Otac', 'answer': 'Father'},
                {'type': 'multiple_choice',
                 'prompt': 'What does ‘obitelj’ mean?',
                 'options': ['Family', 'Coffee', 'Name'],
                 'answer': 'Family'},
                {'type': 'translate_en_to_hr', 'prompt': 'Friend (female)', 'answer': 'Prijateljica'},
                {'type': 'comprehension',
                 'passage': 'Ovo je moja obitelj. Majka se zove Ana, a otac Marko.',
                 'prompt': 'What is the mother’s name?',
                 'options': ['Ana', 'Marko', 'Luka'],
                 'answer': 'Ana'},
                {'type': 'reorder_words',
                 'prompt': 'Build the sentence: ‘This is my family.’',
                 'words': ['moja', 'Ovo', 'obitelj.', 'je'],
                 'answer': ['Ovo', 'je', 'moja', 'obitelj.']},
                {'type': 'fill_blank', 'prompt': 'Majka i ___. (Mother and father.)', 'answer': 'otac'},
                {'type': 'translate_en_to_hr', 'prompt': 'Family', 'answer': 'Obitelj'}]},
 {'id': 'lesson-06-present-tense',
  'number': 6,
  'title': 'I have, you have',
  'topic': 'Present tense: imati',
  'lesson_type': 'grammar',
  'difficulty': 3,
  'level': 'Beginner → early A1',
  'description': 'Use the present-tense verb imati (to have) in simple sentences.',
  'grammar_note': 'Imati (to have): ja imam, ti imaš, on/ona ima. The ending changes with the subject. '
                  'Croatian subject pronouns can usually be omitted: Imam kavu = I have coffee.',
  'vocabulary': [{'hr': 'Imam', 'en': 'I have'},
                 {'hr': 'Imaš', 'en': 'You have'},
                 {'hr': 'Ima', 'en': 'He / she has'},
                 {'hr': 'Knjiga', 'en': 'Book'}],
  'exercises': [{'type': 'translate_en_to_hr', 'prompt': 'I have coffee', 'answer': 'Imam kavu'},
                {'type': 'multiple_choice',
                 'prompt': 'Choose ‘you have’ (informal).',
                 'options': ['Imam', 'Imaš', 'Ima'],
                 'answer': 'Imaš'},
                {'type': 'translate_hr_to_en', 'prompt': 'Ima knjigu', 'answer': 'He / she has a book'},
                {'type': 'fill_blank', 'prompt': 'Ti ___ kavu. (You have coffee.)', 'answer': 'imaš'},
                {'type': 'reorder_words',
                 'prompt': 'Build the sentence: ‘I have a book.’',
                 'words': ['knjigu.', 'imam', 'Ja'],
                 'answer': ['Ja', 'imam', 'knjigu.']},
                {'type': 'comprehension',
                 'passage': 'Luka ima knjigu. Ana ima kavu.',
                 'prompt': 'What does Luka have?',
                 'options': ['A book', 'Coffee', 'Water'],
                 'answer': 'A book'},
                {'type': 'fill_blank', 'prompt': 'Ana ___ kavu. (Ana has coffee.)', 'answer': 'ima'},
                {'type': 'translate_en_to_hr', 'prompt': 'You have water', 'answer': 'Imaš vodu'}]},
 {'id': 'lesson-07-review',
  'number': 7,
  'title': 'Review: people and verbs',
  'topic': 'Cumulative course review',
  'lesson_type': 'review',
  'difficulty': 3,
  'level': 'Beginner → early A1',
  'description': 'Practice due vocabulary from the entire course deck.',
  'vocabulary': [],
  'exercises': []}]
EXERCISE_TYPES = {"multiple_choice", "translate_en_to_hr", "translate_hr_to_en", "fill_blank", "reorder_words", "comprehension"}
LESSON_TYPES = {"vocabulary", "grammar", "review"}


def normalize(text):
    return " ".join(str(text).strip().lower().replace("!", "").replace("?", "").replace(".", "").replace(",", "").split())


@st.cache_data(show_spinner=False)
def pronunciation_audio(text):
    """Create Croatian MP3 audio on the server and cache it across reruns."""
    if edge_tts is None:
        raise RuntimeError("Install project requirements to enable Croatian audio.")
    async def generate():
        speech = edge_tts.Communicate(text, voice="hr-HR-GabrijelaNeural", rate="-15%")
        audio = bytearray()
        async for chunk in speech.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        return bytes(audio)

    return asyncio.run(generate())


def pronunciation_button(text, key):
    try:
        with st.spinner("Preparing Croatian audio…"):
            audio = pronunciation_audio(str(text))
        if not audio:
            raise RuntimeError("The speech service returned empty audio.")
    except Exception:
        if edge_tts is None:
            st.caption("Croatian audio needs the project dependencies. Run `python -m pip install -r requirements.txt` and restart the app.")
        else:
            st.caption("Croatian audio is temporarily unavailable. Check the app server’s internet connection and try again.")
        return

    audio_data = base64.b64encode(audio).decode("ascii")
    button_id = f"speak-{key}"
    html = f"""<button id="{button_id}" style="background:#e4f8e9;border:1px solid #c9ebd2;border-radius:12px;padding:11px 16px;color:#193b35;font:700 15px Arial;cursor:pointer;">🔊 Hear pronunciation</button>
<div id="voice-status-{key}" role="status" style="margin-top:5px;color:#75847e;font:12px Arial;"></div>
<script>
const audioData = "{audio_data}";
document.getElementById("{button_id}").addEventListener("click", () => {{
  const player = new Audio("data:audio/mpeg;base64," + audioData);
  player.play().catch(() => {{ document.getElementById("voice-status-{key}").textContent = "Could not play audio in this browser."; }});
}});
</script>"""
    st.components.v1.html(html, height=76)


def validate_lesson(data):
    errors = []
    if not isinstance(data, dict): return ["The JSON root must be an object."]
    for field in ("number", "title", "topic", "lesson_type", "difficulty"):
        if field not in data: errors.append(f"Add the required ‘{field}’ field.")
    if errors: return errors
    if not isinstance(data["number"], int) or isinstance(data["number"], bool) or data["number"] < 1: errors.append("‘number’ must be a positive whole number.")
    if not isinstance(data["title"], str) or not data["title"].strip(): errors.append("‘title’ must be a non-empty string.")
    if not isinstance(data["topic"], str) or not data["topic"].strip(): errors.append("‘topic’ must be a non-empty string.")
    if not isinstance(data["lesson_type"], str) or data["lesson_type"] not in LESSON_TYPES: errors.append("‘lesson_type’ must be vocabulary, grammar, or review.")
    if not isinstance(data["difficulty"], int) or isinstance(data["difficulty"], bool) or not 1 <= data["difficulty"] <= 5: errors.append("‘difficulty’ must be a whole number from 1 to 5.")
    vocab = data.get("vocabulary", [])
    if not isinstance(vocab, list): errors.append("‘vocabulary’ must be an array."); vocab = []
    for i, word in enumerate(vocab, 1):
        if not isinstance(word, dict) or not all(isinstance(word.get(k), str) and word[k].strip() for k in ("hr", "en")):
            errors.append(f"Vocabulary item {i} needs Croatian ‘hr’ and English ‘en’ strings.")
    exercises = data.get("exercises", [])
    if not isinstance(exercises, list): errors.append("‘exercises’ must be an array."); exercises = []
    if data.get("lesson_type") in ("vocabulary", "grammar") and not exercises: errors.append("Vocabulary and grammar lessons need at least one exercise.")
    if data.get("lesson_type") == "vocabulary" and not vocab: errors.append("Vocabulary lessons need a ‘vocabulary’ list for spaced repetition.")
    if data.get("lesson_type") == "grammar" and (not isinstance(data.get("grammar_note"), str) or not data["grammar_note"].strip()): errors.append("Grammar lessons need a ‘grammar_note’ explanation.")
    for i, item in enumerate(exercises, 1):
        if not isinstance(item, dict): errors.append(f"Exercise {i} must be an object."); continue
        typ = item.get("type")
        if not isinstance(typ, str) or typ not in EXERCISE_TYPES: errors.append(f"Exercise {i}: unsupported type ‘{typ}’. "); continue
        if not isinstance(item.get("prompt"), str) or not item["prompt"].strip(): errors.append(f"Exercise {i}: ‘prompt’ is required.")
        if typ != "reorder_words" and (not isinstance(item.get("answer"), str) or not item["answer"].strip()): errors.append(f"Exercise {i}: ‘answer’ is required.")
        if typ in ("multiple_choice", "comprehension") and (not isinstance(item.get("options"), list) or len(item["options"]) < 2): errors.append(f"Exercise {i}: {typ} needs at least two ‘options’.")
        if typ in ("multiple_choice", "comprehension") and isinstance(item.get("options"), list) and item.get("answer") not in item["options"]: errors.append(f"Exercise {i}: ‘answer’ must match one of its options.")
        if typ == "comprehension" and (not isinstance(item.get("passage"), str) or not item["passage"].strip()): errors.append(f"Exercise {i}: comprehension needs a ‘passage’.")
        if typ == "reorder_words":
            words, answer = item.get("words"), item.get("answer")
            if not isinstance(words, list) or len(words) < 3 or not all(isinstance(w, str) and w.strip() for w in words): errors.append(f"Exercise {i}: reorder_words needs at least three ‘words’ strings.")
            if not isinstance(answer, list) or not all(isinstance(w, str) for w in answer): errors.append(f"Exercise {i}: reorder_words ‘answer’ must be an ordered array of words.")
            elif isinstance(words, list) and sorted(normalize(w) for w in words) != sorted(normalize(w) for w in answer): errors.append(f"Exercise {i}: ‘answer’ must use the same words as ‘words’.")
    return errors


def check_difficulty_order(lesson):
    peers = [l for l in st.session_state.lessons.values() if l["lesson_type"] != "review" and l["number"] != lesson["number"]]
    before = [l for l in peers if l["number"] < lesson["number"]]
    after = [l for l in peers if l["number"] > lesson["number"]]
    if before and lesson["lesson_type"] != "review" and lesson["difficulty"] < max(before, key=lambda x: x["number"])["difficulty"]:
        return "Difficulty should stay level or increase as numbered content lessons advance."
    if after and lesson["lesson_type"] != "review" and lesson["difficulty"] > min(after, key=lambda x: x["number"])["difficulty"]:
        return "This lesson would make a later numbered content lesson easier; adjust the difficulty order."
    return None


def now_utc():
    return datetime.now(timezone.utc)


def due_cards():
    now = now_utc()
    return sorted([(key, card) for key, card in st.session_state.cards.items() if datetime.fromisoformat(card["due_at"]) <= now], key=lambda pair: pair[1]["due_at"])


def review_uses_typing(card):
    """Graduate established or explicitly easy words to typed recall."""
    reps = int(card.get("reps", 0))
    interval = float(card.get("interval", 0))
    return reps >= 2 or (reps >= 1 and interval >= 4.0)


def review_choices(key, card, cards, index):
    """Build stable multiple-choice options with up to three course-wide distractors."""
    answer = card["hr"]
    distractors = list({normalize(item["hr"]): item["hr"] for other_key, item in cards.items() if other_key != key and normalize(item["hr"]) != normalize(answer)}.values())
    chooser = random.Random(f"{key}:{index}")
    selected = chooser.sample(distractors, min(3, len(distractors)))
    options = [answer, *selected]
    chooser.shuffle(options)
    return options


def add_lesson_words(lesson):
    now = now_utc().isoformat()
    for word in lesson.get("vocabulary", []):
        key = normalize(word["hr"])
        if key not in st.session_state.cards:
            st.session_state.cards[key] = {"hr": word["hr"], "en": word["en"], "interval": 0.0, "ease": 2.3, "reps": 0, "lapses": 0, "due_at": now}
        else:
            st.session_state.cards[key]["en"] = word["en"]


def begin_review(lesson_id=None):
    # A new review session should start with blank typing and choice widgets.
    for widget_key in list(st.session_state.keys()):
        if widget_key.startswith(("answer_review_", "choice_review_")):
            del st.session_state[widget_key]
    st.session_state.page = "review"
    st.session_state.active_review_lesson = lesson_id
    st.session_state.review_queue = [key for key, _ in due_cards()]
    st.session_state.review_index = 0
    st.session_state.review_revealed = False
    st.session_state.review_correct = None


PROGRESS_PATH = Path(__file__).with_name("progress.json")


def read_progress_file():
    try:
        saved = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        if not isinstance(saved, dict) or saved.get("schema_version") != 1:
            return {}
        return saved
    except (OSError, json.JSONDecodeError):
        return {}


def save_progress():
    """Atomically save this local learner's course and session progress."""
    data = {
        "schema_version": 1,
        "lessons": st.session_state.lessons,
        "xp": st.session_state.xp,
        "completed_lessons": sorted(st.session_state.completed_lessons),
        "cards": st.session_state.cards,
        "page": st.session_state.page,
        "lesson_id": st.session_state.lesson_id,
        "lesson_attempts": st.session_state.lesson_attempts,
        "index": st.session_state.index,
        "checked": st.session_state.checked,
        "widget_values": {key: value for key, value in st.session_state.items() if key.startswith(("answer_", "choice_")) and isinstance(value, str)},
        "ordering_words": st.session_state.ordering_words,
        "review_queue": st.session_state.review_queue,
        "review_index": st.session_state.review_index,
        "review_revealed": st.session_state.review_revealed,
        "review_correct": st.session_state.review_correct,
        "active_review_lesson": st.session_state.active_review_lesson,
    }
    try:
        temp_path = PROGRESS_PATH.with_name(PROGRESS_PATH.name + ".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(PROGRESS_PATH)
        st.session_state.progress_save_error = None
    except OSError as exc:
        st.session_state.progress_save_error = str(exc)


def restore_progress(saved):
    """Restore valid saved course data over the built-in starter course."""
    lessons = {lesson["id"]: lesson for lesson in STARTER_COURSE}
    saved_lessons = saved.get("lessons", {})
    if isinstance(saved_lessons, dict):
        for lesson_id, lesson in saved_lessons.items():
            if not isinstance(lesson_id, str) or not isinstance(lesson, dict) or lesson.get("id") != lesson_id:
                continue
            if validate_lesson(lesson):
                continue
            conflict = next((key for key, existing in lessons.items() if existing["number"] == lesson["number"] and key != lesson_id), None)
            if conflict is None:
                lessons[lesson_id] = lesson
    return lessons


def lesson_is_unlocked(lesson, course_lessons, completed_ids):
    """New topics depend on prior content lessons; review units never gate the course."""
    prior_content = [
        item for item in course_lessons
        if item["number"] < lesson["number"] and item["lesson_type"] != "review"
    ]
    return lesson["id"] in completed_ids or all(item["id"] in completed_ids for item in prior_content)


saved_progress = read_progress_file()
if "lessons" not in st.session_state:
    st.session_state.lessons = restore_progress(saved_progress)
try:
    saved_xp = max(0, int(saved_progress.get("xp", 0)))
except (TypeError, ValueError):
    saved_xp = 0
if "xp" not in st.session_state: st.session_state.xp = saved_xp
saved_completed = saved_progress.get("completed_lessons", [])
if not isinstance(saved_completed, list): saved_completed = []
saved_completed = [item for item in saved_completed if isinstance(item, str)]
if "completed_lessons" not in st.session_state: st.session_state.completed_lessons = set(saved_completed)
saved_cards = saved_progress.get("cards", {})
if not isinstance(saved_cards, dict): saved_cards = {}
if "cards" not in st.session_state: st.session_state.cards = saved_cards
if "page" not in st.session_state: st.session_state.page = saved_progress.get("page", "home")
if "lesson_id" not in st.session_state: st.session_state.lesson_id = saved_progress.get("lesson_id")
if "lesson_attempts" not in st.session_state: st.session_state.lesson_attempts = saved_progress.get("lesson_attempts", 0)
if "ordering_words" not in st.session_state: st.session_state.ordering_words = saved_progress.get("ordering_words", {})
if "index" not in st.session_state: st.session_state.index = saved_progress.get("index", 0)
if "checked" not in st.session_state: st.session_state.checked = saved_progress.get("checked")
saved_widgets = saved_progress.get("widget_values", {})
if not isinstance(saved_widgets, dict): saved_widgets = {}
for widget_key, widget_value in saved_widgets.items():
    if isinstance(widget_key, str) and widget_key.startswith(("answer_", "choice_")) and isinstance(widget_value, str) and widget_key not in st.session_state:
        st.session_state[widget_key] = widget_value
if "review_queue" not in st.session_state: st.session_state.review_queue = saved_progress.get("review_queue", [])
if "review_index" not in st.session_state: st.session_state.review_index = saved_progress.get("review_index", 0)
if "review_revealed" not in st.session_state: st.session_state.review_revealed = saved_progress.get("review_revealed", False)
if "review_correct" not in st.session_state: st.session_state.review_correct = saved_progress.get("review_correct")
if "active_review_lesson" not in st.session_state: st.session_state.active_review_lesson = saved_progress.get("active_review_lesson")
if "progress_save_error" not in st.session_state: st.session_state.progress_save_error = None

clean_cards = {}
for card_key, card in st.session_state.cards.items():
    if not isinstance(card_key, str) or not isinstance(card, dict): continue
    if not all(isinstance(card.get(field), str) for field in ("hr", "en", "due_at")): continue
    try:
        datetime.fromisoformat(card["due_at"])
        card["interval"] = max(0.0, float(card.get("interval", 0)))
        card["ease"] = max(1.3, float(card.get("ease", 2.3)))
        card["reps"] = max(0, int(card.get("reps", 0)))
        card["lapses"] = max(0, int(card.get("lapses", 0)))
    except (TypeError, ValueError):
        continue
    clean_cards[card_key] = card
st.session_state.cards = clean_cards
if not isinstance(st.session_state.completed_lessons, set):
    st.session_state.completed_lessons = set()
st.session_state.completed_lessons.intersection_update(st.session_state.lessons.keys())
if not isinstance(st.session_state.lesson_attempts, int): st.session_state.lesson_attempts = 0
if not isinstance(st.session_state.index, int) or st.session_state.index < 0: st.session_state.index = 0
if not isinstance(st.session_state.review_queue, list): st.session_state.review_queue = []
st.session_state.review_queue = [key for key in st.session_state.review_queue if key in st.session_state.cards]
if not isinstance(st.session_state.review_index, int) or st.session_state.review_index < 0: st.session_state.review_index = 0
if not isinstance(st.session_state.ordering_words, dict): st.session_state.ordering_words = {}
if not isinstance(st.session_state.active_review_lesson, str) or st.session_state.active_review_lesson not in st.session_state.lessons:
    st.session_state.active_review_lesson = None
if st.session_state.page == "lesson" and (not isinstance(st.session_state.lesson_id, str) or st.session_state.lesson_id not in st.session_state.lessons):
    st.session_state.page = "home"
    st.session_state.lesson_id = None
if not isinstance(st.session_state.page, str) or st.session_state.page not in {"home", "lesson", "review"}:
    st.session_state.page = "home"

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">🇭🇷</span><span>Bok! Croatian Quest</span></div>', unsafe_allow_html=True)
    st.markdown("### Your journey")
    st.metric("⭐ Total XP", st.session_state.xp)
    st.metric("✅ Lessons finished", len(st.session_state.completed_lessons))
    st.metric("🧠 Words in course deck", len(st.session_state.cards))
    if st.session_state.progress_save_error:
        st.warning("Progress could not be saved here. Check that the project folder is writable.")
    else:
        st.caption("Progress auto-saves on this computer.")
    st.markdown("---")
    st.markdown("### Add a numbered lesson")
    uploaded = st.file_uploader("Upload one lesson JSON", type=["json"], help="Lessons are added to this course for your current session.")
    if uploaded:
        try:
            lesson = json.load(uploaded)
            errs = validate_lesson(lesson)
            if not errs:
                lid = str(lesson.get("id") or f"lesson-{lesson['number']:02d}")
                lesson["id"] = lid
                for existing in st.session_state.lessons.values():
                    if existing["number"] == lesson["number"] and existing["id"] != lid:
                        errs.append(f"Lesson number {lesson['number']} is already used by ‘{existing['title']}’.")
                        break
                order_error = check_difficulty_order(lesson)
                if order_error: errs.append(order_error)
            if errs:
                for error in errs: st.error(error)
            else:
                st.session_state.lessons[lesson["id"]] = lesson
                st.success(f"Added lesson {lesson['number']:02d}: {lesson['title']}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            st.error("That file isn’t valid JSON. Check its syntax and try again.")
    with st.expander("Lesson JSON format"):
        st.code('''{
  "id": "lesson-08-shopping",
  "number": 8,
  "title": "At the market",
  "topic": "Food and shopping",
  "lesson_type": "vocabulary",
  "difficulty": 3,
  "description": "Learn words for fruit and prices.",
  "vocabulary": [
    {"hr": "Jabuka", "en": "Apple"},
    {"hr": "Koliko košta?", "en": "How much does it cost?"}
  ],
  "exercises": [
    {"type": "translate_en_to_hr", "prompt": "Apple", "answer": "Jabuka"}
  ]
}''', language="json")
        st.caption("lesson_type: vocabulary, grammar, or review. Vocabulary/grammar lessons have exercises; vocabulary lessons need vocabulary entries; grammar lessons need grammar_note. Difficulty 1–5 should rise as numbered content lessons advance. Review lessons use the shared due-word deck and need no exercises.")

st.markdown('<div class="brand"><span class="brand-mark">🇭🇷</span><span>Bok! Croatian Quest</span></div>', unsafe_allow_html=True)

if st.session_state.page == "home":
    st.markdown('<div class="hero"><div class="eyebrow">A little Croatian, every day</div><h1>Dobro došli!<br>Let’s learn Croatian.</h1><p>Follow the course in order. New words return for review across every lesson.</p></div>', unsafe_allow_html=True)
    due = due_cards()
    col1, col2, col3 = st.columns(3)
    for col, value, label in [(col1, str(st.session_state.xp), "TOTAL XP"), (col2, str(len(st.session_state.lessons)), "NUMBERED LESSONS"), (col3, str(len(due)), "WORDS DUE")]:
        with col: st.markdown(f'<div class="stat"><div class="stat-num">{value}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)
    if due and st.button(f"🧠 Review {len(due)} due words", type="primary", use_container_width=True):
        begin_review(); save_progress(); st.rerun()
    st.markdown("\n### Course path")
    lessons = sorted(st.session_state.lessons.values(), key=lambda x: x["number"])
    for lesson in lessons:
        complete = lesson["id"] in st.session_state.completed_lessons
        lesson_unlocked = lesson_is_unlocked(lesson, lessons, st.session_state.completed_lessons)
        types = {"vocabulary":"📚 Vocabulary", "grammar":"🧩 Grammar", "review":"🔁 Spaced repetition"}
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                mark = "✅" if complete else ("🔒" if not lesson_unlocked else "🇭🇷")
                st.markdown(f"#### {mark} {lesson['number']:02d} · {lesson['title']}")
                st.caption(f"{lesson['topic']} · {types[lesson['lesson_type']]} · Difficulty {lesson['difficulty']}/5")
                if lesson.get("description"): st.write(lesson["description"])
            with right:
                st.write("")
                if lesson_unlocked:
                    if st.button("Review →" if lesson["lesson_type"] == "review" else ("Repeat →" if complete else "Start →"), key=f"start_{lesson['id']}", type="primary", use_container_width=True):
                        if lesson["lesson_type"] == "review":
                            begin_review(lesson["id"])
                        else:
                            st.session_state.page = "lesson"
                            st.session_state.lesson_id = lesson["id"]
                            st.session_state.index = 0
                            st.session_state.checked = None
                            st.session_state.lesson_attempts += 1
                        save_progress(); st.rerun()
                else:
                    st.button("Locked", key=f"locked_{lesson['id']}", disabled=True, use_container_width=True)
    st.info("🔒 Finish the numbered content lessons in order. Review lessons draw due words from the shared deck and never block a new topic.")
elif st.session_state.page == "review":
    due = due_cards()
    # Keep the review batch from the moment the session began; words added after that wait for the next batch.
    queue = st.session_state.review_queue
    title = "Course-wide spaced repetition"
    if st.session_state.active_review_lesson:
        active_lesson = st.session_state.lessons[st.session_state.active_review_lesson]
        title = f"{active_lesson['number']:02d} · {active_lesson['title']}"
    st.markdown(f'<div class="hero"><div class="eyebrow">{title}</div><h1>Bring words back<br>at the right time.</h1><p>Type well-known words; choose from options while they’re still new.</p></div>', unsafe_allow_html=True)
    idx = st.session_state.review_index
    if idx >= len(queue):
        st.success("Review complete — you’re all caught up for this session! 🎉")
        st.markdown(f"### {len(queue)} cards reviewed")
        if st.session_state.active_review_lesson and st.session_state.active_review_lesson not in st.session_state.completed_lessons:
            st.session_state.completed_lessons.add(st.session_state.active_review_lesson)
            save_progress()
        if st.button("Back to course", type="primary"):
            st.session_state.page = "home"; st.session_state.active_review_lesson = None; save_progress(); st.rerun()
    else:
        key = queue[idx]
        card = st.session_state.cards.get(key)
        if not card:
            st.session_state.review_index += 1; save_progress(); st.rerun()
        else:
            st.progress(idx / max(1, len(queue)))
            st.caption(f"Card {idx + 1} of {len(queue)} · Previously learned across the course")
            st.markdown(f'<div class="lesson-card"><div class="eyebrow">What does this mean?</div><div class="prompt">{html.escape(card["en"])}</div></div>', unsafe_allow_html=True)
            typing_mode = review_uses_typing(card)
            st.caption("Type the Croatian word" if typing_mode else "Choose the Croatian word")
            if not st.session_state.review_revealed:
                if typing_mode:
                    response = st.text_input("Your answer", key=f"answer_review_{idx}", label_visibility="collapsed", placeholder="Type in Croatian…")
                else:
                    options = review_choices(key, card, st.session_state.cards, idx)
                    response = st.radio("Choose the Croatian translation", options, key=f"choice_review_{idx}", label_visibility="collapsed")
                if st.button("Check answer", key=f"check_review_{idx}", type="primary", use_container_width=True):
                    st.session_state.review_correct = normalize(response) == normalize(card["hr"])
                    st.session_state.review_revealed = True
                    save_progress(); st.rerun()
            else:
                if st.session_state.review_correct is True:
                    st.success("Correct! Lijepo! 🎉")
                elif st.session_state.review_correct is False:
                    st.error(f"Not quite — the answer is **{card['hr']}**.")
                else:
                    st.info(f"Answer: **{card['hr']}**")
                st.markdown(f"### {html.escape(card['hr'])}")
                pronunciation_button(card["hr"], f"review-{idx}")
                st.caption("How well did you remember it?")
                ratings = st.columns(4)
                for col, rating, label in zip(ratings, ["again", "hard", "good", "easy"], ["Again", "Hard", "Good", "Easy"]):
                    with col:
                        if st.button(label, key=f"rate_{idx}_{rating}", use_container_width=True):
                            now = now_utc()
                            if rating == "again":
                                card["interval"] = 0.01; card["ease"] = max(1.3, card["ease"] - 0.2); card["reps"] = 0; card["lapses"] += 1
                            elif rating == "hard":
                                card["interval"] = max(0.5, card["interval"] * 1.2 if card["interval"] else 0.5); card["ease"] = max(1.3, card["ease"] - 0.15); card["reps"] += 1
                            elif rating == "good":
                                card["interval"] = 1.0 if card["reps"] == 0 else (3.0 if card["reps"] == 1 else card["interval"] * card["ease"]); card["reps"] += 1
                            else:
                                card["interval"] = 4.0 if card["reps"] == 0 else (7.0 if card["reps"] == 1 else card["interval"] * card["ease"] * 1.3); card["ease"] = min(3.0, card["ease"] + 0.15); card["reps"] += 1
                            card["due_at"] = (now + timedelta(days=card["interval"])).isoformat()
                            if rating != "again": st.session_state.xp += 2
                            st.session_state.review_index += 1; st.session_state.review_revealed = False; st.session_state.review_correct = None; save_progress(); st.rerun()
    if st.button("← Exit review"):
        st.session_state.page = "home"; st.session_state.active_review_lesson = None; save_progress(); st.rerun()
else:
    lesson = st.session_state.lessons[st.session_state.lesson_id]
    exercises = lesson["exercises"]
    total = len(exercises)
    idx = st.session_state.index
    st.markdown(f"**{lesson['number']:02d} · {lesson['title']}**  ·  {lesson['topic']}")
    st.markdown(f"Difficulty {lesson['difficulty']}/5 · {lesson['lesson_type'].title()}")
    if lesson.get("grammar_note"):
        with st.expander("Grammar note", expanded=True): st.write(lesson["grammar_note"])
    if idx >= total:
        st.markdown('<div class="hero"><div class="eyebrow">Lesson complete</div><h1>Odlično! 🎉</h1><p>New words are now in your course-wide review deck.</p></div>', unsafe_allow_html=True)
        st.balloons()
        st.markdown(f"### +{total * 10} XP earned")
        st.progress(1.0)
        if st.button("Back to course", type="primary"):
            st.session_state.completed_lessons.add(lesson["id"])
            add_lesson_words(lesson)
            st.session_state.page = "home"; st.session_state.lesson_id = None; save_progress(); st.rerun()
    else:
        ex = exercises[idx]
        st.markdown(f"Question {idx + 1} of {total}")
        st.progress(idx / total)
        prompt_map = {
            "translate_en_to_hr": ("Translate to Croatian", f"How do you say ‘{ex['prompt']}’ in Croatian?"),
            "translate_hr_to_en": ("Translate to English", f"What does ‘{ex['prompt']}’ mean?"),
            "multiple_choice": ("Choose the right answer", ex["prompt"]),
            "fill_blank": ("Fill in the blank", ex["prompt"]),
            "comprehension": ("Read and understand", ex["prompt"]),
            "reorder_words": ("Arrange the words", ex["prompt"])
        }
        label, prompt = prompt_map[ex["type"]]
        st.markdown(f'<span class="pill">{label}</span>', unsafe_allow_html=True)
        if ex["type"] == "comprehension":
            st.markdown(f'<div class="lesson-card"><div class="eyebrow">Read this</div><div>{html.escape(ex["passage"]).replace(chr(10), "<br>")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="lesson-card"><div class="prompt">{html.escape(prompt)}</div></div>', unsafe_allow_html=True)
        if ex["type"] == "translate_hr_to_en": pronunciation_button(ex["prompt"], f"prompt-{idx}")
        if ex["type"] in ("multiple_choice", "comprehension"):
            answer = st.radio("Choose one", ex["options"], key=f"choice_{idx}", label_visibility="collapsed", disabled=st.session_state.checked is not None)
        elif ex["type"] == "reorder_words":
            order_id = f"{st.session_state.lesson_id}-{st.session_state.lesson_attempts}-{idx}"
            if order_id not in st.session_state.ordering_words:
                shuffled = list(ex["words"])
                random.shuffle(shuffled)
                st.session_state.ordering_words[order_id] = shuffled
            initial_order = st.session_state.ordering_words[order_id]
            answer = word_order_component(words=initial_order, key=f"word-order-{order_id}", default=initial_order)
            if answer is None: answer = initial_order
            if isinstance(answer, list) and all(isinstance(word, str) for word in answer):
                st.session_state.ordering_words[order_id] = answer
        else:
            answer = st.text_input("Your answer", key=f"answer_{st.session_state.lesson_id}_{st.session_state.lesson_attempts}_{idx}", placeholder="Type your answer…", disabled=st.session_state.checked is not None)
        if st.session_state.checked is None:
            has_answer = bool(answer) if isinstance(answer, list) else bool(answer.strip())
            if st.button("Check answer", type="primary", use_container_width=True, disabled=not has_answer):
                if ex["type"] == "reorder_words":
                    correct = [normalize(word) for word in answer] == [normalize(word) for word in ex["answer"]]
                else:
                    correct = normalize(answer) == normalize(ex["answer"])
                st.session_state.checked = {"correct": correct, "given": answer}
                if correct: st.session_state.xp += 10
                save_progress(); st.rerun()
        else:
            result = st.session_state.checked
            if result["correct"]: st.success("Correct! +10 XP 🎉")
            else:
                expected = " ".join(ex["answer"]) if ex["type"] == "reorder_words" else ex["answer"]
                st.error(f"Not quite. The answer is: **{expected}**")
            if ex.get("hint"): st.caption(f"💡 {ex['hint']}")
            spoken = None
            if ex["type"] in ("translate_en_to_hr", "fill_blank"): spoken = ex["answer"]
            elif ex["type"] == "translate_hr_to_en": spoken = ex["prompt"]
            elif ex["type"] == "reorder_words": spoken = " ".join(ex["answer"])
            if spoken: pronunciation_button(spoken, f"answer-{idx}")
            if st.button("Continue →", type="primary", use_container_width=True):
                st.session_state.index += 1; st.session_state.checked = None; save_progress(); st.rerun()
        if st.button("← Exit lesson"):
            st.session_state.page = "home"; st.session_state.lesson_id = None; st.session_state.checked = None; save_progress(); st.rerun()


# Persist widget-driven changes (including word-order interactions) after every render.
save_progress()
