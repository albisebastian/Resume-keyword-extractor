"""Resume Keyword Extractor — Flask web app serving the trained Keras model."""
import io
import os
import re
import subprocess
import sys
from collections import Counter

# Windows reads files with its own encoding (cp1252) by default, which breaks loading a model whose
# vocabulary contains characters like "–" or "é". Restart once in Python's UTF-8 mode to fix that.
if not sys.flags.utf8_mode and (sys.platform == "win32" or os.environ.get("FORCE_UTF8_RELAUNCH")):
    os.environ.pop("FORCE_UTF8_RELAUNCH", None)
    sys.exit(subprocess.call([sys.executable, "-X", "utf8", *sys.argv]))

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

import keras
import tensorflow as tf
from flask import Flask, jsonify, render_template, request

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "model", "resume_keyword_extractor.keras")
LABELS = ["O", "B-TECH", "I-TECH", "B-SKILL", "I-SKILL"]
MAXLEN = 40  # must match training
TOKEN_RE = re.compile(r"[A-Za-z0-9+#]+(?:[.\-/][A-Za-z0-9+#]+)*|[^\sA-Za-z0-9]")
ALLOWED = {".pdf", ".docx", ".txt"}
EDGE_STOP = {"on", "and", "with", "in", "of", "for", "using", "the", "to", "a", "an", "-", ",", ".", "(", ")", ":", "|"}

APP_VERSION = "2.1"
app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.context_processor
def _asset_version():
    def asset(name):  # /static/app.js?v=<mtime>  -> the browser never shows stale CSS/JS
        path = os.path.join(BASE, "static", name)
        return f"/static/{name}?v={int(os.path.getmtime(path))}"
    return {"asset": asset, "app_version": APP_VERSION}
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
model = keras.models.load_model(MODEL_PATH)

# quick self-test so a broken/mismatched model is obvious at startup
_probe = model.predict(tf.constant(["Skilled in Python and machine learning ."]), verbose=0)[0].argmax(-1)
if LABELS[_probe[2]] != "B-TECH":
    print("\n[warning] The model loaded but gives unexpected predictions. The Keras version here may differ "
          f"from the one used in Colab. Installed Keras: {keras.__version__}\n", file=sys.stderr)
else:
    print(f"Model loaded OK (Keras {keras.__version__}). Open http://localhost:{os.environ.get('PORT', 5000)}")


def spaced_ratio(text: str) -> float:
    """Share of tokens that are single letters/digits — high means 'P y t h o n' style text."""
    toks = text.split()
    return sum(len(t) == 1 and t.isalnum() for t in toks) / max(len(toks), 1)


def fix_letter_spacing(text: str) -> str:
    """Rejoin 'P y t h o n   D j a n g o' -> 'Python Django' on lines that are letter-spaced."""
    out = []
    for line in text.splitlines():
        if spaced_ratio(line) > 0.5 and len(line.split()) >= 3:
            words = re.split(r"\s{2,}", line.strip())       # 2+ spaces = real word gap
            line = " ".join(re.sub(r"(?<=\S) (?=\S)", "", w) for w in words)
        out.append(line)
    return "\n".join(out)


def rebuild_lines(page) -> str:
    """Rebuild text lines from glyph/word positions; glues letter-spaced characters into words."""
    rows = {}
    for x0, y0, x1, y1, w, *_ in page.get_text("words"):
        rows.setdefault(round((y0 + y1) / 4), []).append((x0, x1, w))  # ~2pt buckets
    lines = []
    for _, items in sorted(rows.items()):
        items.sort()
        gaps = sorted(b[0] - a[1] for a, b in zip(items, items[1:]))
        tiny = gaps[len(gaps) // 4] if gaps else 0          # typical letter gap
        line = items[0][2]
        for (_, px1, pw), (x0, _, w) in zip(items, items[1:]):
            glue = len(pw) == 1 and len(w) == 1 or (x0 - px1) <= tiny * 1.5 + 0.3
            line += ("" if glue and spaced_ratio(" ".join(i[2] for i in items)) > 0.5 else " ") + w
        lines.append(line)
    return "\n".join(lines)


def read_pdf(data: bytes) -> str:
    """Try several PDF text extractors and keep the one that looks most like real words."""
    candidates = []
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        candidates.append("\n".join(p.extract_text() or "" for p in reader.pages))
        candidates.append("\n".join(p.extract_text(extraction_mode="layout") or "" for p in reader.pages))
    except Exception:
        pass
    try:
        import pymupdf
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            candidates.append("\n".join(page.get_text() for page in doc))
            candidates.append("\n".join(rebuild_lines(page) for page in doc))
    except Exception:
        pass
    candidates = [fix_letter_spacing(c) for c in candidates if c.strip()]
    if not candidates:
        return ""
    return min(candidates, key=spaced_ratio)


def read_file(name: str, data: bytes) -> str:
    ext = os.path.splitext(name.lower())[1]
    if ext == ".pdf":
        return read_pdf(data)
    if ext == ".docx":
        import docx
        d = docx.Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append(" , ".join(c.text for c in row.cells))
        return fix_letter_spacing("\n".join(parts))
    return fix_letter_spacing(data.decode("utf-8", errors="ignore"))


def chunks(text: str):
    """Split into lines/sentences, then into token windows of MAXLEN."""
    for line in re.split(r"[\n\r]+|(?<=[.!?])\s+|\s*[•●▪◦·|]\s*", text):
        toks = TOKEN_RE.findall(line)
        for i in range(0, len(toks), MAXLEN):
            if toks[i:i + MAXLEN]:
                yield toks[i:i + MAXLEN]


# ---------------------------------------------------------------------------
# Intelligent classification: model predictions + confidence + knowledge base
# ---------------------------------------------------------------------------
import knowledge as kb

SEPARATORS = {",", "(", ")", "[", "]", "|", ";", ":", "-", "–", "—", "•", "/", "\"", "'", "?", "!"}
SUFFIXES = ("-based", "-powered", "-driven", "-enabled", "-oriented", "-related")
MIN_CONF_MULTI = 0.85     # unknown multi-word phrase from the model
MIN_CONF_SINGLE = 0.92    # unknown single word from the model


def _kb_index():
    idx = {}
    for typ, items in (("TECH", kb.TECH_LIST), ("SKILL", kb.SKILL_LIST)):
        for term in items:
            key = tuple(t.lower() for t in TOKEN_RE.findall(term))
            canon = kb.ALIASES.get(term.lower(), term)
            idx.setdefault(key, (typ, canon))
    return idx


KB = _kb_index()
KB_MAXLEN = max(len(k) for k in KB)


def _norm_token(t: str) -> str:
    low = t.lower()
    for suf in SUFFIXES:
        if low.endswith(suf) and len(low) > len(suf) + 1:
            return low[: -len(suf)]
    return low


def _kb_ok(key, toks, i, n):
    """Extra checks for ambiguous / short dictionary terms."""
    if n == 1 and key[0] in kb.AMBIGUOUS:
        t = toks[i]
        if not t[0].isupper():
            return False
        prev = toks[i - 1] if i else "."
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        # sentence-initial capital ("Excel in teamwork") isn't evidence of a name unless it's a list item
        if prev in {".", "!", "?"} and nxt and nxt not in SEPARATORS and nxt.lower() not in {"and", "or"}:
            return False
        if len(t) == 1:  # "C" / "R": only inside lists, never initials like "R. Kumar"
            prev = toks[i - 1] if i else ""
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if nxt == "." or not ({prev, nxt} & {",", "/", "|", ";", "and", "(", ")", ":", ""}):
                return False
    return True


def _validate_unknown(tokens, conf, blocked):
    low = [t.lower() for t in tokens]
    if not tokens or len(tokens) > 4:
        return False
    if any(re.fullmatch(r"[\d.,%+]+", t) for t in tokens):              # numbers, years, scores
        return False
    spoken = {l.lower() for l in SPOKEN}
    if any(t in kb.COMPANY_WORDS or t in kb.PLACES or t in spoken or t in blocked for t in low):
        return False
    if all(t in kb.GENERIC or not re.search(r"[a-z]", t) for t in low):
        return False
    if len(tokens) == 1:
        t = tokens[0]
        looks_like_name = t[0].isupper() or re.search(r"[\d+#.]", t[1:] or "")
        return bool(looks_like_name) and len(t) > 1 and conf >= MIN_CONF_SINGLE
    return conf >= MIN_CONF_MULTI


def extract(text: str, blocked=frozenset()) -> dict:
    """Return tech + skills. blocked = lowercase words that must never be keywords (e.g. the candidate's city)."""
    windows = list(chunks(text))
    found = {}   # key -> {keyword, type, count, conf, sources}

    def add(display, typ, conf, source):
        key = display.lower()
        item = found.setdefault(key, {"keyword": display, "type": typ, "count": 0, "conf": 0.0, "sources": set()})
        item["count"] += 1
        item["conf"] = max(item["conf"], conf)
        item["sources"].add(source)

    if windows:
        probs = model.predict(tf.constant([" ".join(w) for w in windows]), batch_size=64, verbose=0)
        for toks, pr in zip(windows, probs):
            pr = pr[: len(toks)]
            pred, pconf = pr.argmax(-1), pr.max(-1)
            n_tok = len(toks)
            norm = [_norm_token(t) for t in toks]
            covered = [False] * n_tok

            # 1) knowledge-base terms (longest match first); the model's opinion sets the confidence
            i = 0
            while i < n_tok:
                for n in range(min(KB_MAXLEN, n_tok - i), 0, -1):
                    key = tuple(norm[i:i + n])
                    if key in KB and _kb_ok(key, toks, i, n):
                        typ, canon = KB[key]
                        model_says = any(LABELS[p] != "O" for p in pred[i:i + n])
                        conf = float(pconf[i:i + n].mean()) if model_says else 0.75
                        add(canon, typ, conf, "model" if model_says else "knowledge base")
                        if model_says:
                            found[canon.lower()]["sources"].add("knowledge base")
                        for j in range(i, i + n):
                            covered[j] = True
                        i += n
                        break
                else:
                    i += 1

            # 2) model spans that aren't known terms: split on separators, trim, validate strictly
            spans, cur, typ = [], [], None
            for j, p in enumerate(list(pred) + [0]):
                tag = LABELS[p] if j < n_tok else "O"
                stop = j < n_tok and (covered[j] or toks[j] in SEPARATORS)
                if tag == "O" or stop or tag.startswith("B-") or (tag.startswith("I-") and typ != tag[2:]):
                    if cur:
                        spans.append((cur, typ))
                    cur, typ = ([j], tag[2:]) if tag != "O" and not stop else ([], None)
                else:
                    cur.append(j)
            for idxs, typ in spans:
                while idxs and toks[idxs[-1]].lower() in EDGE_STOP:
                    idxs = idxs[:-1]
                while idxs and toks[idxs[0]].lower() in EDGE_STOP:
                    idxs = idxs[1:]
                words = [toks[j] for j in idxs]
                if not words:
                    continue
                conf = float(pconf[idxs].mean())
                if _validate_unknown(words, conf, blocked):
                    add(" ".join(words), typ, conf, "model")

    def fmt(t):
        items = [v for v in found.values() if v["type"] == t]
        items.sort(key=lambda v: (-v["count"], -v["conf"]))
        return [{"keyword": v["keyword"], "count": v["count"], "confidence": round(v["conf"], 2),
                 "source": " + ".join(sorted(v["sources"]))} for v in items]

    return {"tech": fmt("TECH"), "skills": fmt("SKILL"), "words": len(text.split())}


# ---------------------------------------------------------------------------
# Rule-based profile fields (name, contact, address, spoken languages).
# These sit alongside the model; the model still produces tech + skills.
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![\w])(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{3,5}(?![\w])")
LINK_RE = re.compile(r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com)/[^\s|,;]+", re.I)
SPOKEN = ["English", "Hindi", "Malayalam", "Tamil", "Telugu", "Kannada", "Marathi", "Bengali", "Gujarati", "Punjabi",
          "Urdu", "Odia", "Arabic", "French", "German", "Spanish", "Portuguese", "Italian", "Dutch", "Russian",
          "Chinese", "Mandarin", "Cantonese", "Japanese", "Korean", "Turkish", "Persian", "Swahili", "Indonesian",
          "Malay", "Thai", "Vietnamese", "Polish", "Greek", "Hebrew", "Sinhala", "Nepali", "Filipino", "Tagalog", "Sanskrit"]
SPOKEN_RE = re.compile(r"\b(" + "|".join(SPOKEN) + r")\b", re.I)
NOT_NAME = {"resume", "curriculum", "vitae", "cv", "profile", "summary", "objective", "contact", "experience",
            "education", "skills", "engineer", "developer", "analyst", "scientist", "intern", "manager", "designer",
            "student", "consultant", "architect", "specialist", "trainee", "lead", "officer", "projects"}
HEADER_RE = re.compile(r"^\s*(experience|education|projects|skills|certifications|summary|profile|objective|"
                       r"achievements|hobbies|interests|references|declaration|work experience|internships)\b", re.I)


def extract_profile(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    emails = list(dict.fromkeys(EMAIL_RE.findall(text)))
    links = list(dict.fromkeys(m.rstrip(".") for m in LINK_RE.findall(text)))
    no_mail = EMAIL_RE.sub(" ", LINK_RE.sub(" ", text))
    phones = []
    for m in PHONE_RE.findall(no_mail):
        digits = re.sub(r"\D", "", m)
        if 10 <= len(digits) <= 13 and not re.fullmatch(r"(19|20)\d{2}(19|20)\d{2}", digits):
            phones.append(m.strip())
    phones = list(dict.fromkeys(phones))

    name = ""
    def _clean_name(cand):
        cand = re.sub(r"^(?:name|full name)\s*[:\-–]\s*", "", cand.strip(), flags=re.I)
        cand = re.split(r"\s[|•·,]\s?|\s{2,}|\t|,", cand)[0].strip()
        kept = []
        for w in cand.split():
            low = w.lower().strip(".")
            if (low in NOT_NAME or low in kb.GENERIC or low in kb.PLACES or (low,) in KB
                    or not re.fullmatch(r"[^\W\d_][^\W\d_.'-]*\.?(?:[-'][^\W\d_]+)*", w)
                    or (kept and kept[0].isupper() and len(kept[0]) > 1 and not w.isupper())):
                break                      # stop at job titles, places, skills, digits, or a change of letter case
            kept.append(w)
        return " ".join(kept)

    for i, line in enumerate(lines[:25]):
        if EMAIL_RE.search(line) or HEADER_RE.match(line) or line.lower() in {"resume", "cv", "curriculum vitae"}:
            continue
        cand = _clean_name(line)
        if i < 3 and len(cand.split()) == 1 and len(line.split()) == 1 and i + 1 < len(lines):
            nxt = _clean_name(lines[i + 1])
            if len(nxt.split()) == 1 and len(lines[i + 1].split()) == 1 and cand.isupper() and nxt.isupper():
                cand = f"{cand} {nxt}"      # name split over two lines at the top: ALBIN / JOSEPH
        if 2 <= len(cand.split()) <= 5 and cand[0].isupper():
            name = cand.title() if cand.isupper() else cand
            break

    if not name and emails:                 # fallback: build it from the email, albin.joseph92@ -> Albin Joseph
        user = re.sub(r"\d+", "", emails[0].split("@")[0])
        parts = [p for p in re.split(r"[._\-]+", user) if len(p) > 1]
        if len(parts) >= 2:
            name = " ".join(p.capitalize() for p in parts[:3])
        elif parts:
            name = parts[0].capitalize()

    address = ""
    for line in lines:
        m = re.search(r"\b(?:address|location|residence)\b\s*[:\-–]\s*(.+)", line, re.I)
        if m:
            address = re.split(r"\s[|•]\s", m.group(1))[0].strip(" ,"); break
    if not address:
        city_re = re.compile(r"^[A-Z][A-Za-z .'-]+,\s*[A-Z][A-Za-z .'-]+(?:,\s*[A-Za-z .'-]+)?(?:\s*[-–]?\s*\d{5,6})?$")
        for line in lines[:12]:
            for seg in re.split(r"\s*[|•·]\s*", line):
                seg = seg.strip()
                if seg and not EMAIL_RE.search(seg) and not LINK_RE.search(seg) and city_re.match(seg):
                    address = seg; break
            if address: break
    if not address:
        for line in lines:
            if re.search(r"\b\d{6}\b", line) and "," in line and not EMAIL_RE.search(line) and len(line) < 120:
                address = line; break

    languages, zone = [], []
    for i, line in enumerate(lines):
        if re.search(r"\blanguages?\b", line, re.I):
            zone.append(line)
            for nxt in lines[i + 1:i + 4]:
                if HEADER_RE.match(nxt): break
                zone.append(nxt)
    for z in zone:
        for m in SPOKEN_RE.findall(z):
            lang = m.capitalize()
            if lang not in languages:
                languages.append(lang)

    return {"name": name, "emails": emails, "phones": phones, "links": links,
            "address": address, "languages": languages}


@app.get("/")
def index():
    resp = app.make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/api/health")
def health():
    return jsonify(ok=True, version=APP_VERSION, folder=BASE, keras=keras.__version__)


@app.post("/api/extract")
def api_extract():
    if "file" in request.files and request.files["file"].filename:
        f = request.files["file"]
        if os.path.splitext(f.filename.lower())[1] not in ALLOWED:
            return jsonify(error="Unsupported file. Use PDF, DOCX or TXT."), 400
        try:
            text = read_file(f.filename, f.read())
        except Exception:
            return jsonify(error="Couldn't read that file. Is it a valid document?"), 400
        source = f.filename
    else:
        text = (request.form.get("text") or "").strip()
        source = "Pasted text"
    if not text.strip() or spaced_ratio(text) > 0.4:
        return jsonify(error="No readable text found. Scanned PDFs (images) aren't supported."), 400
    profile = extract_profile(text)
    blocked = {w.lower() for w in re.findall(r"[A-Za-z]+", " ".join([profile["address"], profile["name"]]))}
    return jsonify(source=source, version=APP_VERSION, profile=profile, **extract(text, blocked))


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is larger than 5 MB."), 413


if __name__ == "__main__":
    import socket
    port = int(os.environ.get("PORT", 5000))
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            print(f"\n[error] Port {port} is already in use - probably an OLD copy of this app is still running "
                  "in another terminal.\nClose that terminal (or press Ctrl+C in it), or start this one on another "
                  f"port:  set PORT=5001  then  python app.py\n", file=sys.stderr)
            sys.exit(1)
    print(f"Resume Keyword Extractor v{APP_VERSION}  |  folder: {BASE}")
    app.run(host="127.0.0.1", port=port, debug=False)
