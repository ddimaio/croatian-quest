import asyncio
import base64
import html
import json
import random

import requests
import time
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
speech_component = st.components.v1.declare_component(
    "croatian_speech", path=str(Path(__file__).parent / "components" / "speech")
)
auth_callback_component = st.components.v1.declare_component(
    "croatian_auth_callback", path=str(Path(__file__).parent / "components" / "auth_callback")
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
.dialogue-turn { padding:9px 12px; margin:7px 0; background:#f4fbf5; border-left:4px solid #58cc7a; border-radius:8px; line-height:1.55; }
.dialogue-speaker { color:#268447; font-weight:800; }
.pill { display:inline-block; background:#eef8f0; color:#268447; font-size:.75rem; font-weight:800; padding:5px 10px; border-radius:99px; }
hr { border-color:var(--line); }
[data-testid="stMetric"] { background:white; padding:12px 16px; border-radius:16px; border:1px solid var(--line); }
.stButton>button, [data-testid^="stBaseButton-"], [data-testid="stFormSubmitButton"] button {
  border-radius:13px; font-weight:800; min-height:48px;
  border:1px solid #c9d8cd !important; background-color:#ffffff !important;
  color:#193b35 !important; opacity:1;
}
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background-color:#58cc7a !important; border-color:#58cc7a !important; color:#123624 !important;
}
.stButton>button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
  background-color:#2eaa58 !important; border-color:#2eaa58 !important; color:#ffffff !important;
}
.stButton>button:not([kind="primary"]):not(:disabled):hover, [data-testid="stBaseButton-secondary"]:not(:disabled):hover {
  background-color:#e4f8e9 !important; border-color:#58cc7a !important; color:#193b35 !important;
}
.stButton>button:disabled, [data-testid^="stBaseButton-"]:disabled {
  background-color:#edf1ee !important; border-color:#dfe6e1 !important; color:#68756f !important; opacity:1 !important;
}
/* Keep button labels readable in the sidebar and when themes/browser styles override them. */
.stButton>button, [data-testid^="stBaseButton-"], [data-testid="stFormSubmitButton"] button,
[data-testid="stSidebar"] button {
  color:#193b35 !important;
  -webkit-text-fill-color:#193b35 !important;
  opacity:1 !important;
  font-weight:800 !important;
}
.stButton>button *, [data-testid^="stBaseButton-"] *, [data-testid="stFormSubmitButton"] button *,
[data-testid="stSidebar"] button * {
  color:inherit !important;
  -webkit-text-fill-color:currentColor !important;
  opacity:1 !important;
}
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"] {
  color:#123624 !important;
  -webkit-text-fill-color:#123624 !important;
}
.stProgress>div>div>div { background:var(--green); }
[data-testid="stRadio"] [role="radiogroup"] label {
  box-sizing:border-box; width:100%; min-height:56px; display:flex; align-items:center;
  padding:10px 14px; gap:12px; white-space:normal; color:#193b35 !important;
  border:1px solid var(--line); border-radius:14px; background:#fff;
}
[data-testid="stRadio"] [role="radiogroup"] label *,
[data-testid="stRadio"] [role="radiogroup"] label p,
[data-testid="stRadio"] [role="radiogroup"] label span {
  color:#193b35 !important;
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
  .stButton>button, [data-testid^="stBaseButton-"], [data-testid="stFormSubmitButton"] button,
  [data-testid="stSidebar"] button {
    box-sizing:border-box !important;
    width:100% !important;
    min-width:0 !important;
    min-height:52px !important;
    height:auto !important;
    padding:10px 12px !important;
    line-height:1.25 !important;
    font-size:1rem !important;
    white-space:normal !important;
    overflow-wrap:anywhere !important;
    text-overflow:clip !important;
  }
  /* Give lesson actions the full row so labels like “Review” and “Repeat” do not get clipped. */
  [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
    display:flex !important;
    flex-direction:column !important;
    gap:.5rem !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] {
    width:100% !important;
    min-width:0 !important;
    flex:1 1 auto !important;
  }
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
EXERCISE_TYPES = {"multiple_choice", "translate_en_to_hr", "translate_hr_to_en", "fill_blank", "reorder_words", "comprehension", "speak"}
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
    dialogue = data.get("dialogue")
    if dialogue is not None:
        if not isinstance(dialogue, dict):
            errors.append("‘dialogue’ must be an object.")
        else:
            if not isinstance(dialogue.get("context"), str) or not dialogue["context"].strip():
                errors.append("A dialogue needs a short ‘context’.")
            lines = dialogue.get("lines")
            if not isinstance(lines, list) or not lines:
                errors.append("A dialogue needs a non-empty ‘lines’ array.")
            elif any(
                not isinstance(line, dict)
                or not isinstance(line.get("speaker"), str) or not line["speaker"].strip()
                or not isinstance(line.get("text"), str) or not line["text"].strip()
                for line in lines
            ):
                errors.append("Each dialogue line needs a ‘speaker’ and Croatian ‘text’.")
            question = dialogue.get("question")
            if not isinstance(question, dict):
                errors.append("A dialogue needs one related ‘question’ object.")
            else:
                if not isinstance(question.get("prompt"), str) or not question["prompt"].strip():
                    errors.append("A dialogue question needs a ‘prompt’.")
                options = question.get("options")
                if not isinstance(options, list) or len(options) < 2:
                    errors.append("A dialogue question needs at least two ‘options’.")
                elif question.get("answer") not in options:
                    errors.append("A dialogue question’s ‘answer’ must match one of its options.")
    return errors


def load_course_lesson_files():
    """Add numbered lesson JSON files committed in the lessons folder to the starter course."""
    lessons_dir = Path(__file__).parent / "lessons"
    for lesson_path in sorted(lessons_dir.glob("lesson_*.json")):
        try:
            lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if validate_lesson(lesson):
            continue
        existing_index = next(
            (
                index for index, existing in enumerate(STARTER_COURSE)
                if existing["id"] == lesson.get("id")
                or existing["number"] == lesson["number"]
            ),
            None,
        )
        if existing_index is None:
            STARTER_COURSE.append(lesson)
        elif STARTER_COURSE[existing_index]["id"] == lesson.get("id"):
            # The JSON file is the source of truth for numbered lessons, including
            # newly added dialogue exercises.
            STARTER_COURSE[existing_index] = lesson
    STARTER_COURSE.sort(key=lambda item: item["number"])


load_course_lesson_files()


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


def record_study_day():
    """Update the persistent streak when the learner earns XP today."""
    today = now_utc().date().isoformat()
    last_day = st.session_state.last_activity_date
    if last_day == today:
        return
    yesterday = (now_utc().date() - timedelta(days=1)).isoformat()
    if last_day == yesterday:
        st.session_state.day_streak += 1
    else:
        st.session_state.day_streak = 1
    st.session_state.best_day_streak = max(
        st.session_state.best_day_streak,
        st.session_state.day_streak,
    )
    st.session_state.last_activity_date = today


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
    st.session_state.index = 0
    st.session_state.checked = None
    st.session_state.review_queue = [key for key, _ in due_cards()]
    st.session_state.review_index = 0
    st.session_state.review_revealed = False
    st.session_state.review_correct = None
    st.session_state.review_correct_answers = 0


def supabase_config():
    try:
        section = st.secrets["supabase"]
        config = {
            "url": str(section["url"]).rstrip("/"),
            "anon_key": str(section["anon_key"]),
            "site_url": str(section["site_url"]).rstrip("/"),
        }
        return config if all(config.values()) else None
    except Exception:
        return None


SUPABASE = supabase_config()


def supabase_request(path, method="POST", payload=None, token=None, params=None, prefer=None):
    headers = {"apikey": SUPABASE["anon_key"], "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if prefer:
        headers["Prefer"] = prefer
    try:
        return requests.request(
            method,
            f"{SUPABASE['url']}/{path.lstrip('/')}",
            headers=headers,
            json=payload,
            params=params,
            timeout=20,
        )
    except requests.RequestException:
        return None


def response_error(response, fallback):
    if response is None:
        return "Could not connect to the account service. Check your internet connection and try again."
    try:
        data = response.json()
        if isinstance(data, dict):
            return str(data.get("msg") or data.get("message") or data.get("error_description") or data.get("error") or fallback)
    except ValueError:
        pass
    return fallback


def auth_success(response):
    if response is None or not response.ok:
        return False
    try:
        data = response.json()
        if not data.get("access_token") or not data.get("user", {}).get("id"):
            return False
        st.session_state.auth_session = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": time.time() + int(data.get("expires_in", 3600)),
            "user": data["user"],
        }
        st.session_state["_auth_storage_synced_token"] = None
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def refresh_auth_session():
    session = st.session_state.get("auth_session")
    if not session:
        return False
    if float(session.get("expires_at", 0)) > time.time() + 60:
        return True
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        st.session_state.pop("auth_session", None)
        return False
    response = supabase_request(
        "auth/v1/token",
        payload={"refresh_token": refresh_token},
        params={"grant_type": "refresh_token"},
    )
    if not auth_success(response):
        st.session_state.pop("auth_session", None)
        st.session_state.auth_message = "Your session expired. Please sign in again."
        return False
    if st.session_state.auth_session.get("refresh_token") != refresh_token:
        # Persist a rotated refresh token to browser storage on the next render.
        st.rerun()
    return True


def show_auth_page():
    st.markdown('<div class="hero"><div class="eyebrow">Croatian Quest</div><h1>Your own learning journey.</h1><p>Create an account or sign in to keep your course progress private and synced.</p></div>', unsafe_allow_html=True)
    if st.session_state.get("auth_message"):
        st.info(st.session_state.pop("auth_message"))
    login_tab, signup_tab, reset_tab = st.tabs(["Log in", "Create account", "Forgot password"])
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email", autocomplete="username")
            password = st.text_input("Password", type="password", key="login_password", autocomplete="current-password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)
        if submitted:
            response = supabase_request(
                "auth/v1/token",
                payload={"email": email.strip(), "password": password},
                params={"grant_type": "password"},
            )
            if auth_success(response):
                st.session_state["_clear_auth_password_fields"] = True
                st.session_state.pop("_saved_progress", None)
                st.rerun()
            else:
                st.error(response_error(response, "We couldn't sign you in. Check your email and password."))
    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (at least 8 characters)", type="password", key="signup_password", autocomplete="new-password")
            confirm = st.text_input("Confirm password", type="password", key="signup_confirm", autocomplete="new-password")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            if len(password) < 8:
                st.error("Choose a password with at least 8 characters.")
            elif password != confirm:
                st.error("The passwords don't match.")
            else:
                response = supabase_request(
                    "auth/v1/signup",
                    payload={"email": email.strip(), "password": password},
                    params={"redirect_to": SUPABASE["site_url"]},
                )
                if response is not None and response.ok:
                    if auth_success(response):
                        st.session_state["_clear_auth_password_fields"] = True
                        st.session_state.pop("_saved_progress", None)
                        st.rerun()
                    else:
                        st.success("Account created. Check your email to confirm it, then log in.")
                else:
                    st.error(response_error(response, "We couldn't create the account. Check the email and try again."))
    with reset_tab:
        st.write("We'll email you a secure link to choose a new password.")
        with st.form("recovery_email_form"):
            email = st.text_input("Account email", key="recovery_email_input")
            submitted = st.form_submit_button("Send reset link", use_container_width=True)
        if submitted:
            response = supabase_request(
                "auth/v1/recover",
                payload={"email": email.strip()},
                params={"redirect_to": SUPABASE["site_url"]},
            )
            if response is not None and response.ok:
                st.success("If an account exists for that email, a password reset link has been sent.")
            else:
                st.error(response_error(response, "We couldn't request a reset link. Try again later."))


def handle_password_recovery():
    token_hash = st.query_params.get("token_hash")
    recovery_type = st.query_params.get("type")
    if token_hash and recovery_type == "recovery" and not st.session_state.get("recovery_session"):
        response = supabase_request(
            "auth/v1/verify",
            payload={"type": "recovery", "token_hash": token_hash},
        )
        if auth_success(response):
            st.session_state.recovery_session = st.session_state.pop("auth_session")
            st.query_params.clear()
        else:
            st.query_params.clear()
            st.session_state.auth_message = "That reset link is invalid or expired. Request a new one."
            return False

    recovery = st.session_state.get("recovery_session")
    if not recovery:
        return False
    st.title("Choose a new password")
    with st.form("set_new_password_form"):
        password = st.text_input("New password (at least 8 characters)", type="password", key="new_password", autocomplete="new-password")
        confirm = st.text_input("Confirm new password", type="password", key="new_password_confirm", autocomplete="new-password")
        submitted = st.form_submit_button("Save new password", type="primary", use_container_width=True)
    if submitted:
        if len(password) < 8:
            st.error("Choose a password with at least 8 characters.")
        elif password != confirm:
            st.error("The passwords don't match.")
        else:
            response = supabase_request(
                "auth/v1/user",
                method="PATCH",
                payload={"password": password},
                token=recovery["access_token"],
            )
            if response is not None and response.ok:
                st.session_state["_clear_auth_password_fields"] = True
                st.session_state.auth_session = recovery
                st.session_state.pop("recovery_session", None)
                st.session_state.pop("_saved_progress", None)
                st.success("Password updated. You're signed in.")
                st.rerun()
            else:
                st.error(response_error(response, "We couldn't update your password. Request another reset link."))
    return True


def handle_default_recovery_callback():
    """Restore a saved Supabase session and process Supabase recovery redirects."""
    storage_action = st.session_state.pop("_auth_storage_action", None)
    if storage_action == "clear":
        auth_callback_component(action="clear", key="auth-browser-bridge")
        st.session_state["_auth_storage_synced_token"] = None
        st.session_state["_auth_storage_ready"] = True
        return

    session = st.session_state.get("auth_session")
    if session:
        refresh_token = session.get("refresh_token", "")
        if refresh_token and st.session_state.get("_auth_storage_synced_token") != refresh_token:
            auth_callback_component(action="save", refresh_token=refresh_token, key="auth-browser-bridge")
            st.session_state["_auth_storage_synced_token"] = refresh_token
        else:
            auth_callback_component(action="idle", key="auth-browser-bridge")
        st.session_state["_auth_storage_ready"] = True
        return

    result = auth_callback_component(action="restore", key="auth-browser-bridge")
    if not isinstance(result, dict):
        st.session_state["_auth_storage_ready"] = False
        return

    if result.get("type") == "recovery":
        if st.session_state.get("_default_recovery_handled"):
            return
        st.session_state["_default_recovery_handled"] = True
    elif result.get("status") == "ready":
        st.session_state["_auth_storage_ready"] = True
        refresh_token = result.get("refresh_token", "")
        if not isinstance(refresh_token, str) or not refresh_token:
            return
        response = supabase_request(
            "auth/v1/token",
            payload={"refresh_token": refresh_token},
            params={"grant_type": "refresh_token"},
        )
        if auth_success(response):
            st.session_state["_auth_storage_ready"] = True
            st.rerun()
        else:
            st.session_state["_auth_storage_action"] = "clear"
            st.session_state.auth_message = "Your saved sign-in expired. Please log in again."
            st.rerun()
        return
    else:
        st.session_state["_auth_storage_ready"] = False
        return
    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    if not isinstance(access_token, str) or not access_token or not isinstance(refresh_token, str) or not refresh_token:
        st.session_state.auth_message = "That reset link is invalid or expired. Request a new one."
        return

    response = supabase_request("auth/v1/user", method="GET", token=access_token)
    try:
        user = response.json() if response is not None and response.ok else None
    except ValueError:
        user = None
    if not isinstance(user, dict) or not user.get("id"):
        st.session_state.auth_message = "That reset link is invalid or expired. Request a new one."
        return

    st.session_state.pop("auth_session", None)
    st.session_state.pop("_saved_progress", None)
    st.session_state.recovery_session = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": time.time() + 3500,
        "user": user,
    }


def authenticate_user():
    if st.session_state.pop("_clear_auth_password_fields", False):
        for key in ("login_password", "signup_password", "signup_confirm", "new_password", "new_password_confirm"):
            st.session_state.pop(key, None)
    if not SUPABASE:
        st.title("Account setup required")
        st.error("Add your Supabase project settings to Streamlit secrets to enable accounts.")
        st.code('[supabase]\\nurl = "https://YOUR_PROJECT.supabase.co"\\nanon_key = "YOUR_SUPABASE_ANON_KEY"\\nsite_url = "https://YOUR-APP.streamlit.app"')
        st.info("Follow the Supabase setup steps in README.md, then restart the app.")
        st.stop()

    if handle_password_recovery():
        st.stop()

    if not st.session_state.get("_auth_storage_ready"):
        st.caption("Restoring your sign-in…")
        st.stop()

    if st.session_state.get("auth_session") and refresh_auth_session():
        return
    show_auth_page()
    st.stop()


def load_user_progress():
    user_id = st.session_state.auth_session["user"]["id"]
    response = supabase_request(
        "rest/v1/learner_progress",
        method="GET",
        params={"select": "progress", "user_id": f"eq.{user_id}"},
        token=st.session_state.auth_session["access_token"],
    )
    if response is None or not response.ok:
        st.session_state.progress_save_error = "Could not load progress from the account database."
        return {}
    try:
        rows = response.json()
        return rows[0].get("progress", {}) if rows and isinstance(rows, list) else {}
    except (ValueError, AttributeError, TypeError):
        st.session_state.progress_save_error = "The account database returned invalid progress data."
        return {}


def save_progress():
    """Save course progress to the signed-in learner's private database row."""
    data = {
        "schema_version": 1,
        "lessons": st.session_state.lessons,
        "xp": st.session_state.xp,
        "day_streak": st.session_state.day_streak,
        "best_day_streak": st.session_state.best_day_streak,
        "last_activity_date": st.session_state.last_activity_date,
        "lesson_correct_answers": st.session_state.lesson_correct_answers,
        "completed_lessons": sorted(st.session_state.completed_lessons),
        "cards": st.session_state.cards,
        "page": st.session_state.page,
        "lesson_id": st.session_state.lesson_id,
        "lesson_attempts": st.session_state.lesson_attempts,
        "index": st.session_state.index,
        "checked": st.session_state.checked,
        "hint_counts": st.session_state.hint_counts,
        "widget_values": {key: value for key, value in st.session_state.items() if key.startswith(("answer_", "choice_")) and isinstance(value, str)},
        "ordering_words": st.session_state.ordering_words,
        "review_queue": st.session_state.review_queue,
        "review_index": st.session_state.review_index,
        "review_revealed": st.session_state.review_revealed,
        "review_correct": st.session_state.review_correct,
        "review_correct_answers": st.session_state.review_correct_answers,
        "active_review_lesson": st.session_state.active_review_lesson,
    }
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if st.session_state.get("_last_saved_progress") == serialized:
        return
    session = st.session_state.get("auth_session")
    if not session or not refresh_auth_session():
        st.session_state.progress_save_error = "Your session expired. Sign in again to save progress."
        return
    payload = {"user_id": session["user"]["id"], "progress": data}
    response = supabase_request(
        "rest/v1/learner_progress",
        method="POST",
        payload=payload,
        params={"on_conflict": "user_id"},
        token=st.session_state.auth_session["access_token"],
        prefer="resolution=merge-duplicates,return=minimal",
    )
    if response is None or not response.ok:
        st.session_state.progress_save_error = "Progress could not be saved to your account. Check the database setup and try again."
        return
    st.session_state["_last_saved_progress"] = serialized
    st.session_state.progress_save_error = None


def restore_progress(saved):
    """Merge bundled, saved, and server-uploaded lessons into the course."""
    lessons = {lesson["id"]: lesson for lesson in STARTER_COURSE}

    def merge_lesson(lesson_id, lesson):
        if not isinstance(lesson_id, str) or not isinstance(lesson, dict) or lesson.get("id") != lesson_id:
            return
        if validate_lesson(lesson):
            return
        conflict = next(
            (key for key, existing in lessons.items()
             if existing["number"] == lesson["number"] and key != lesson_id),
            None,
        )
        if conflict is None:
            lessons[lesson_id] = lesson

    saved_lessons = saved.get("lessons", {})
    if isinstance(saved_lessons, dict):
        for lesson_id, lesson in saved_lessons.items():
            merge_lesson(lesson_id, lesson)

    lesson_dir = Path(__file__).parent / "lessons"
    if lesson_dir.is_dir():
        for lesson_path in sorted(lesson_dir.glob("*.json")):
            try:
                lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            lesson_id = lesson.get("id") if isinstance(lesson, dict) else None
            if not lesson_id and isinstance(lesson, dict) and isinstance(lesson.get("number"), int):
                lesson_id = f"lesson-{lesson['number']:02d}"
                lesson["id"] = lesson_id
            merge_lesson(lesson_id, lesson)
    return lessons


def lesson_is_unlocked(lesson, course_lessons, completed_ids):
    """New topics depend on prior content lessons; review units never gate the course."""
    prior_content = [
        item for item in course_lessons
        if item["number"] < lesson["number"] and item["lesson_type"] != "review"
    ]
    return lesson["id"] in completed_ids or all(item["id"] in completed_ids for item in prior_content)


handle_default_recovery_callback()
authenticate_user()
if "_saved_progress" not in st.session_state:
    st.session_state["_saved_progress"] = load_user_progress()
saved_progress = st.session_state._saved_progress
if "lessons" not in st.session_state:
    st.session_state.lessons = restore_progress(saved_progress)

# Streamlit can keep an existing browser session alive during a redeploy.
# Refresh bundled lesson content on each run while keeping learner progress separate.
for bundled_lesson in STARTER_COURSE:
    existing_number = next(
        (
            current for current in st.session_state.lessons.values()
            if current.get("number") == bundled_lesson["number"]
        ),
        None,
    )
    if existing_number is None or existing_number.get("id") == bundled_lesson["id"]:
        st.session_state.lessons[bundled_lesson["id"]] = bundled_lesson

try:
    saved_xp = max(0, int(saved_progress.get("xp", 0)))
except (TypeError, ValueError):
    saved_xp = 0
if "xp" not in st.session_state: st.session_state.xp = saved_xp
for streak_key in ("day_streak", "best_day_streak"):
    if streak_key not in st.session_state:
        try:
            st.session_state[streak_key] = max(0, int(saved_progress.get(streak_key, 0)))
        except (TypeError, ValueError):
            st.session_state[streak_key] = 0
if "last_activity_date" not in st.session_state:
    saved_activity_day = saved_progress.get("last_activity_date")
    st.session_state.last_activity_date = (
        saved_activity_day if isinstance(saved_activity_day, str) else None
    )
if "lesson_correct_answers" not in st.session_state:
    saved_correct_answers = saved_progress.get("lesson_correct_answers")
    st.session_state.lesson_correct_answers = (
        saved_correct_answers
        if isinstance(saved_correct_answers, int)
        and not isinstance(saved_correct_answers, bool)
        and saved_correct_answers >= 0
        else None
    )
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
if "hint_counts" not in st.session_state:
    saved_hint_counts = saved_progress.get("hint_counts", {})
    st.session_state.hint_counts = saved_hint_counts if isinstance(saved_hint_counts, dict) else {}
saved_widgets = saved_progress.get("widget_values", {})
if not isinstance(saved_widgets, dict): saved_widgets = {}
for widget_key, widget_value in saved_widgets.items():
    if isinstance(widget_key, str) and widget_key.startswith(("answer_", "choice_")) and isinstance(widget_value, str) and widget_key not in st.session_state:
        st.session_state[widget_key] = widget_value
if "review_queue" not in st.session_state: st.session_state.review_queue = saved_progress.get("review_queue", [])
if "review_index" not in st.session_state: st.session_state.review_index = saved_progress.get("review_index", 0)
if "review_revealed" not in st.session_state: st.session_state.review_revealed = saved_progress.get("review_revealed", False)
if "review_correct" not in st.session_state: st.session_state.review_correct = saved_progress.get("review_correct")
if "review_correct_answers" not in st.session_state:
    saved_review_correct = saved_progress.get("review_correct_answers", 0)
    st.session_state.review_correct_answers = (
        saved_review_correct
        if isinstance(saved_review_correct, int)
        and not isinstance(saved_review_correct, bool)
        and saved_review_correct >= 0
        else 0
    )
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
    today = now_utc().date()
    yesterday = (today - timedelta(days=1)).isoformat()
    last_activity_day = st.session_state.last_activity_date
    current_day_streak = (
        st.session_state.day_streak
        if last_activity_day in {today.isoformat(), yesterday}
        else 0
    )
    st.metric("🔥 Day streak", current_day_streak)
    st.caption(f"Personal best: {st.session_state.best_day_streak} days")
    st.metric("🧠 Words encountered", len(st.session_state.cards))
    if st.session_state.progress_save_error:
        st.warning(st.session_state.progress_save_error)
    else:
        st.caption("Progress auto-saves to your private account.")
    st.caption(f"Signed in as {st.session_state.auth_session['user'].get('email', 'learner')}")
    def logout_callback():
        session = st.session_state.get("auth_session")
        if session and session.get("access_token"):
            supabase_request("auth/v1/logout", token=session["access_token"], params={"scope": "global"})
        st.session_state.clear()
        st.session_state["_auth_storage_action"] = "clear"
        st.session_state["_auth_storage_ready"] = False
    st.button("Log out", key="sidebar_logout", on_click=logout_callback, use_container_width=True)


header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown('<div class="brand"><span class="brand-mark">🇭🇷</span><span>Bok! Croatian Quest</span></div>', unsafe_allow_html=True)
with header_right:
    st.button("Log out", key="main_logout", on_click=logout_callback, use_container_width=True)

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
                            st.session_state.lesson_correct_answers = 0
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
        active_lesson = st.session_state.lessons.get(st.session_state.active_review_lesson)
        dialogue = active_lesson.get("dialogue") if active_lesson else None
        if dialogue and st.session_state.index == 0:
            st.markdown("### 💬 Short conversation in Croatian")
            st.caption(dialogue["context"])
            st.markdown(
                '<div class="lesson-card">' +
                "<br>".join(
                    f"<strong>{html.escape(line['speaker'])}:</strong> {html.escape(line['text'])}"
                    for line in dialogue["lines"]
                ) +
                "</div>",
                unsafe_allow_html=True,
            )
            question = dialogue["question"]
            st.markdown(f"**{question['prompt']}**")
            if st.session_state.checked is None:
                response = st.radio(
                    "Choose one",
                    question["options"],
                    key=f"review_dialogue_choice_{active_lesson['id']}",
                    label_visibility="collapsed",
                )
                if st.button("Check answer", type="primary", use_container_width=True):
                    correct = normalize(response) == normalize(question["answer"])
                    st.session_state.checked = {"correct": correct, "given": response}
                    if correct:
                        st.session_state.xp += 10
                        st.session_state.review_correct_answers += 1
                        record_study_day()
                    save_progress(); st.rerun()
            else:
                if st.session_state.checked["correct"]:
                    st.success("Correct! +10 XP 🎉")
                else:
                    st.error(f"The answer is **{question['answer']}**.")
                if st.button("Continue →", type="primary", use_container_width=True):
                    st.session_state.index = 1
                    st.session_state.checked = None
                    save_progress(); st.rerun()
        else:
            st.success("Review complete — you’re all caught up for this session! 🎉")
            st.markdown(f"### {st.session_state.review_correct_answers} correct · +{st.session_state.review_correct_answers * 10} XP")
            st.caption(f"{len(queue)} review cards completed")
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
                    with st.form(f"review_answer_form_{idx}"):
                        response = st.text_input("Your answer", key=f"answer_review_{idx}", label_visibility="collapsed", placeholder="Type in Croatian…")
                        submitted = st.form_submit_button("Check answer", type="primary", use_container_width=True)
                else:
                    options = review_choices(key, card, st.session_state.cards, idx)
                    response = st.radio("Choose the Croatian translation", options, key=f"choice_review_{idx}", label_visibility="collapsed")
                    submitted = st.button("Check answer", key=f"check_review_{idx}", type="primary", use_container_width=True)
                if submitted:
                    if not response.strip():
                        st.warning("Type an answer or choose an option first.")
                    else:
                        st.session_state.review_correct = normalize(response) == normalize(card["hr"])
                        st.session_state.review_revealed = True
                        if st.session_state.review_correct:
                            st.session_state.xp += 10
                            st.session_state.review_correct_answers += 1
                            record_study_day()
                        save_progress(); st.rerun()
            else:
                if st.session_state.review_correct is True:
                    st.success("Correct! +10 XP · Lijepo! 🎉")
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
        if st.session_state.lesson_correct_answers is not None:
            correct_count = st.session_state.lesson_correct_answers
            earned_xp = correct_count * 10
            st.markdown(f"### {correct_count}/{total} correct · +{earned_xp} XP")
        else:
            st.markdown("### Lesson complete")
            st.caption("Earn 10 XP for each correct answer.")
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
            "reorder_words": ("Arrange the words", ex["prompt"]),
            "speak": ("Speak in Croatian", ex["prompt"])
        }
        label, prompt = prompt_map[ex["type"]]
        st.markdown(f'<span class="pill">{label}</span>', unsafe_allow_html=True)
        if ex["type"] == "comprehension":
            passage = ex["passage"]
            is_final_dialogue = (
                idx == total - 1
                and ":" in passage
                and any(line.strip() for line in passage.splitlines())
            )
            if is_final_dialogue:
                turns = []
                for line in passage.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ":" in line:
                        speaker, words = line.split(":", 1)
                        turns.append(
                            f'<div class="dialogue-turn"><span class="dialogue-speaker">'
                            f'{html.escape(speaker)}:</span>{html.escape(words)}</div>'
                        )
                    else:
                        turns.append(f'<div class="dialogue-turn">{html.escape(line)}</div>')
                st.markdown(
                    '<div class="lesson-card"><div class="eyebrow">🎭 Final mini-dialogue · Croatian</div>'
                    + "".join(turns)
                    + '</div>',
                    unsafe_allow_html=True,
                )
                st.caption("Read the conversation, then answer the question below.")
            else:
                st.markdown(
                    f'<div class="lesson-card"><div class="eyebrow">Read this</div>'
                    f'<div>{html.escape(passage).replace(chr(10), "<br>")}</div></div>',
                    unsafe_allow_html=True,
                )
        st.markdown(f'<div class="lesson-card"><div class="prompt">{html.escape(prompt)}</div></div>', unsafe_allow_html=True)
        if ex["type"] == "translate_hr_to_en": pronunciation_button(ex["prompt"], f"prompt-{idx}")
        if ex["type"] == "translate_en_to_hr":
            hint_key = f"{lesson['id']}:{st.session_state.lesson_attempts}:{idx}"
            answer_text = str(ex["answer"])
            letter_count = sum(not character.isspace() for character in answer_text)
            revealed_count = min(
                letter_count,
                max(0, int(st.session_state.hint_counts.get(hint_key, 0))),
            )
            if revealed_count:
                shown_letters = 0
                clue_characters = []
                for character in answer_text:
                    if character.isspace():
                        clue_characters.append(character)
                    else:
                        clue_characters.append(
                            character if shown_letters < revealed_count else "＿"
                        )
                        shown_letters += 1
                clue = "".join(clue_characters)
                st.info(f"Clue: **{clue}**")
            if revealed_count < letter_count and st.session_state.checked is None:
                if st.button("💡 Add a letter clue", key=f"hint_{idx}", use_container_width=True):
                    st.session_state.hint_counts[hint_key] = revealed_count + 1
                    save_progress()
                    st.rerun()
            elif revealed_count >= letter_count:
                st.caption("All letters revealed.")
        typed_form_submitted = False
        typed_input_form = False
        if ex["type"] in ("multiple_choice", "comprehension"):
            answer = st.radio("Choose one", ex["options"], key=f"choice_{idx}", label_visibility="collapsed", disabled=st.session_state.checked is not None)
        elif ex["type"] == "speak":
            speech_key = f"speech-{st.session_state.lesson_id}-{st.session_state.lesson_attempts}-{idx}"
            speech_result = speech_component(lang="hr-HR", key=speech_key)
            speech_result = speech_result if isinstance(speech_result, dict) else {}
            transcript = str(speech_result.get("transcript", "")).strip()
            if transcript:
                st.markdown(f"**I heard:** {html.escape(transcript)}")
            if speech_result.get("error"):
                st.info(speech_result["error"])
            if speech_result.get("supported") is False or speech_result.get("error"):
                if st.session_state.checked is None:
                    with st.form(f"typed_speech_form_{idx}"):
                        answer = st.text_input(
                            "Type the Croatian phrase instead",
                            key=f"answer_{st.session_state.lesson_id}_{st.session_state.lesson_attempts}_{idx}",
                            placeholder="Type your answer…",
                        )
                        typed_form_submitted = st.form_submit_button("Check answer", type="primary", use_container_width=True)
                    typed_input_form = True
                else:
                    answer = ""
            else:
                answer = transcript
            st.caption("Speech recognition availability depends on your browser. You can type if it is unavailable.")
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
            if st.session_state.checked is None:
                with st.form(f"typed_answer_form_{idx}"):
                    answer = st.text_input(
                        "Your answer",
                        key=f"answer_{st.session_state.lesson_id}_{st.session_state.lesson_attempts}_{idx}",
                        placeholder="Type your answer…",
                    )
                    typed_form_submitted = st.form_submit_button("Check answer", type="primary", use_container_width=True)
                typed_input_form = True
            else:
                answer = ""
        st.caption("Scoring: +10 XP for each correct answer.")
        if st.session_state.checked is None:
            has_answer = bool(answer) if isinstance(answer, list) else bool(answer.strip())
            submitted = typed_form_submitted if typed_input_form else st.button("Check answer", type="primary", use_container_width=True, disabled=not has_answer)
            if submitted:
                if not has_answer:
                    st.warning("Type an answer or complete the exercise first.")
                else:
                    if ex["type"] == "reorder_words":
                        correct = [normalize(word) for word in answer] == [normalize(word) for word in ex["answer"]]
                    else:
                        correct = normalize(answer) == normalize(ex["answer"])
                    st.session_state.checked = {"correct": correct, "given": answer}
                    if correct:
                        st.session_state.xp += 10
                        if st.session_state.lesson_correct_answers is None:
                            st.session_state.lesson_correct_answers = 0
                        st.session_state.lesson_correct_answers += 1
                        record_study_day()
                    save_progress(); st.rerun()
        else:
            result = st.session_state.checked
            if result["correct"]: st.success("Correct! +10 XP 🎉")
            else:
                expected = " ".join(ex["answer"]) if ex["type"] == "reorder_words" else ex["answer"]
                st.error(f"Not quite. The answer is: **{expected}**")
            if ex.get("hint"): st.caption(f"💡 {ex['hint']}")
            spoken = None
            if ex["type"] in ("translate_en_to_hr", "fill_blank", "speak"): spoken = ex["answer"]
            elif ex["type"] == "translate_hr_to_en": spoken = ex["prompt"]
            elif ex["type"] == "reorder_words": spoken = " ".join(ex["answer"])
            if spoken: pronunciation_button(spoken, f"answer-{idx}")
            if st.button("Continue →", type="primary", use_container_width=True):
                st.session_state.index += 1; st.session_state.checked = None; save_progress(); st.rerun()
        if st.button("← Exit lesson"):
            st.session_state.page = "home"; st.session_state.lesson_id = None; st.session_state.checked = None; save_progress(); st.rerun()


# Persist widget-driven changes (including word-order interactions) after every render.
save_progress()
