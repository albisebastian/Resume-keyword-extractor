# Resume Keyword Extractor — Web App

Upload a resume (PDF, DOCX or TXT) or paste its text. The trained Keras model
(`model/resume_keyword_extractor.keras`) labels each word and the app lists the
**technologies** and **skills** it finds.

## Run
```bash
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000

## Structure
```
app.py                 Flask server: reads files, runs the model, returns JSON
model/                 trained .keras model (replace with a retrained one anytime)
templates/index.html   page
static/style.css       styles (light + dark mode, subtle animations)
static/app.js          upload, drag & drop, results, copy, JSON download
```

API: `POST /api/extract` with form field `file` (upload) or `text` (pasted text).
Scanned/image-only PDFs have no text layer and aren't supported.

## How keywords are classified (v2.1)
1. The Keras model labels every word (TECH / SKILL / other) with a confidence score.
2. `knowledge.py` holds ~400 known technologies and skills. Known terms are always put in the
   right category, and ones the model missed are added.
3. Anything else the model suggests is kept only if it is confident (85%+) and isn't a date,
   number, company name, place, spoken language or everyday word.

Add your own terms to `TECH` / `SKILLS` in `knowledge.py` - no retraining needed.

Check which version is running: http://localhost:5000/api/health
