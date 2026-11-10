# Resume Keyword Extractor

Extracts **skills, technologies, name, contact details, address and spoken languages** from resumes
(PDF, DOCX or TXT), using a Keras BiLSTM token-classification model.

| Folder | What's inside |
|---|---|
| `resume_extractor_app/` | Flask web app (black + neon UI) that serves the trained model |
| `colab_training/` | Google Colab notebook, training dataset and the extra-dataset cell |

## Run the web app
```bash
cd resume_extractor_app
python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000 — the badge at the top shows the running version.

## Retrain the model
1. Open `colab_training/Resume_Keyword_Extractor.ipynb` in Google Colab.
2. Run the cells; upload `resume_keywords_dataset.csv` when asked (and an extra dataset in Cell 1b if you have one).
3. The last cell downloads `resume_keyword_extractor.keras` — put it in `resume_extractor_app/model/`.

## How classification works
1. The model tags each word as TECH / SKILL / other, with a confidence score.
2. `resume_extractor_app/knowledge.py` (~400 known terms) corrects categories and adds terms the model missed.
3. Unknown suggestions are kept only when confident and not a date, number, company, place, spoken language or everyday word.
4. Name, contact, address and languages are found with text patterns.
