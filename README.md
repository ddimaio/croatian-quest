# Bok! Croatian Quest

A Duolingo-inspired Croatian course built with Python and Streamlit. The numbered course mixes themed vocabulary, grammar explanations, and course-wide review. Most content lessons have eight short activities and combine typing, multiple choice, reading comprehension, fill-in-the-blank, and drag-to-order sentence building. On touch devices, arrow controls are available for word ordering.

## Run on Windows

```powershell
cd C:\cq
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

Keep the virtual environment in a short path if Windows reports a path-length or `streamlit.exe` access error. For example, create it at `C:\venvs\croatian` and run `C:\venvs\croatian\Scripts\python.exe -m streamlit run "C:\path\to\project\app.py"`.

## Run on macOS or Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Course progression and spaced repetition

Lessons display a number, topic, type, and difficulty. Numbered content lessons unlock in order; review lessons do not block new topics. Content lessons have a 1–5 difficulty rating that should stay level or rise as topics advance. Review lessons repeat due words from one course-wide deck. New or less-secure words use multiple choice; established words switch to typed recall after two successful reviews, or after one review rated Easy. After checking your answer, rate your recall **Again**, **Hard**, **Good**, or **Easy**; this schedules the next review. Progress auto-saves to `progress.json` beside `app.py` and is restored after a browser refresh or app restart. Keep the project folder writable and do not delete that file if you want to retain progress. This file-based save is intended for one learner using a local app; learners sharing a hosted server would share the same save file.

## Upload lessons

Upload one JSON file from the sidebar. Every lesson needs `number`, `title`, `topic`, `lesson_type` (`vocabulary`, `grammar`, or `review`), and `difficulty` (1–5). Optional fields include `id`, `description`, and `level`.

Vocabulary and grammar lessons need `vocabulary` entries formatted as `{ "hr": "Croatian", "en": "English" }` and an `exercises` array. Grammar lessons also need `grammar_note`. Review lessons use the shared due-word deck and may have an empty `exercises` array.

Exercise types:

- `multiple_choice`: `prompt`, `options`, and string `answer`
- `translate_en_to_hr`, `translate_hr_to_en`, `fill_blank`: string `prompt` and `answer`
- `comprehension`: `passage`, `prompt`, `options`, and string `answer`
- `reorder_words`: `prompt`, a shuffled `words` array, and `answer` as the same words in the correct order

Seven sample JSON lessons are in `lessons/` and are included in the starter course. **Hear pronunciation** generates a Croatian MP3 on the Streamlit server with the `edge-tts` package, then plays it in the browser. This works across operating systems and does not depend on voices installed on the learner's device. The server needs an internet connection to generate each phrase, and the phrase text is sent to the online speech service. Generated audio is cached by Streamlit to avoid repeat requests. The Croatian voice is `hr-HR-GabrijelaNeural`.
