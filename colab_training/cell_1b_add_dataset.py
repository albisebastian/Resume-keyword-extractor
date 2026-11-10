# Cell 1b: Add your second dataset (CSV / XLSX / JSON / JSONL) and merge it with df
# Supported layouts (detected automatically):
#   A) columns "tokens" + "tags"                  -> same format as our dataset, used as-is
#   B) a resume-text column (+ optional skills col) -> auto-labelled with keyword matching
#   C) Dataturks-style JSON(L): {"content": ..., "annotation": [{"label": ["Skills"], "points": [...]}]}
import json, random
from google.colab import files

up = files.upload()
NEW_FILE = list(up.keys())[0]
MAX_NEW_SENTENCES = 20000       # cap so training stays fast
TOK = re.compile(r"[A-Za-z0-9+#]+(?:[.\-/][A-Za-z0-9+#]+)*|[^\sA-Za-z0-9]")

# 1) Load the file
ext = NEW_FILE.lower().rsplit(".", 1)[-1]
if ext == "csv":
    new = pd.read_csv(NEW_FILE, encoding_errors="ignore")
elif ext in ("xlsx", "xls"):
    new = pd.read_excel(NEW_FILE)
else:
    raw = open(NEW_FILE, encoding="utf-8", errors="ignore").read().strip()
    recs = json.loads(raw) if raw.startswith("[") else [json.loads(l) for l in raw.splitlines() if l.strip()]
    new = pd.DataFrame(recs)
print("Loaded", NEW_FILE, new.shape, "columns:", list(new.columns))

if {"tokens", "tags"} <= set(new.columns):                       # ---- layout A
    new_df = new[["tokens", "tags"]].dropna().astype(str)
    new_df = new_df[[len(t.split()) == len(g.split()) for t, g in zip(new_df.tokens, new_df.tags)]]
else:                                                              # ---- layouts B / C
    # keyword dictionary from the existing dataset: phrase (lowercase tokens) -> TECH / SKILL
    lex = {}
    for toks, tags in zip(df["tokens"], df["tags"]):
        cur, typ = [], None
        for w, t in list(zip(toks.split(), tags.split())) + [("", "O")]:
            if t.startswith("I-") and cur:
                cur.append(w); continue
            if cur: lex.setdefault(tuple(x.lower() for x in cur), typ)
            cur, typ = ([w], t[2:]) if t.startswith("B-") else ([], None)

    def add_phrases(text, label="SKILL"):
        for p in re.split(r"[,;|\n•●▪]+", str(text)):
            t = tuple(w.lower() for w in TOK.findall(p.strip()))
            if 0 < len(t) <= 4 and any(c.isalpha() for c in "".join(t)) and len(" ".join(t)) > 1:
                lex.setdefault(t, label)

    texts = []
    if "content" in new.columns and "annotation" in new.columns:   # layout C
        for content, anns in zip(new["content"], new["annotation"]):
            texts.append(str(content))
            for a in (anns or []):
                if any("skill" in str(l).lower() for l in (a.get("label") or [])):
                    for pt in a.get("points") or []:
                        add_phrases(pt.get("text", ""))
    else:                                                          # layout B
        names = ["Resume_str", "resume_text", "Resume", "resume", "text", "Text", "content", "Description"]
        text_col = next((c for c in names if c in new.columns), None) or \
                   max(new.select_dtypes("object").columns, key=lambda c: new[c].astype(str).str.len().mean())
        texts = new[text_col].dropna().astype(str).tolist()
        for c in [c for c in new.columns if "skill" in c.lower() and c != text_col]:
            new[c].dropna().map(add_phrases)
        print("Text column:", text_col)

    maxn = max(len(k) for k in lex)
    def label_sentence(toks):
        tags, i, low = ["O"] * len(toks), 0, [t.lower() for t in toks]
        while i < len(toks):
            for n in range(min(maxn, len(toks) - i), 0, -1):
                key = tuple(low[i:i + n])
                if key in lex and (len(toks[i]) > 2 or n > 1 or toks[i] in ("R", "C", "Go", "AI", "ML")):
                    typ = lex[key]; tags[i] = "B-" + typ
                    for j in range(i + 1, i + n): tags[j] = "I-" + typ
                    i += n; break
            else:
                i += 1
        return tags

    pos, neg = [], []
    for text in texts:
        for sent in re.split(r"[\n\r]+|(?<=[.!?])\s+|\s*[•●▪|]\s*", text):
            toks = TOK.findall(sent)[:MAXLEN] if "MAXLEN" in globals() else TOK.findall(sent)[:40]
            if len(toks) < 3: continue
            tags = label_sentence(toks)
            (pos if any(t != "O" for t in tags) else neg).append((" ".join(toks), " ".join(tags)))
    random.seed(0); random.shuffle(pos); random.shuffle(neg)
    pos = pos[:int(MAX_NEW_SENTENCES * 0.7)]
    neg = neg[:min(len(neg), MAX_NEW_SENTENCES - len(pos), len(pos))]  # keep some keyword-free lines too
    new_df = pd.DataFrame(pos + neg, columns=["tokens", "tags"])

new_df = new_df.drop_duplicates()
print(f"New labelled sentences: {len(new_df)}")
print(new_df.sample(min(3, len(new_df)), random_state=1).to_string())
df = pd.concat([df, new_df], ignore_index=True).drop_duplicates().sample(frac=1, random_state=0).reset_index(drop=True)
print("Combined training data:", df.shape)
df.to_csv("combined_dataset.csv", index=False)   # optional: download this to reuse later
