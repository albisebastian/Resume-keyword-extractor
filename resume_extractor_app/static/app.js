const $ = (s, r = document) => r.querySelector(s);
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;

const fileInput = $("#file"), drop = $("#drop"), fileRow = $("#file-row");
const text = $("#text"), go = $("#go"), err = $("#error"), results = $("#results");
const panel = $("#input-card"), busyText = $("#busy-text");
const tabs = [...document.querySelectorAll(".tab")], ink = $(".tab-ink");
let mode = "upload", file = null, lastResult = null;

/* ---------------- tabs ---------------- */
function moveInk(tab) { ink.style.width = tab.offsetWidth + "px"; ink.style.transform = `translateX(${tab.offsetLeft - 3}px)`; }
function selectTab(tab) {
  tabs.forEach((t) => {
    const on = t === tab;
    t.classList.toggle("is-active", on); t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1;
    document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
  });
  mode = tab.id === "tab-upload" ? "upload" : "paste";
  moveInk(tab); hideError(); update();
}
tabs.forEach((t, i) => {
  t.addEventListener("click", () => selectTab(t));
  t.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const n = tabs[(i + (e.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length];
    selectTab(n); n.focus();
  });
});
addEventListener("resize", () => moveInk($(".tab.is-active")));
document.fonts?.ready.then(() => moveInk($(".tab.is-active")));
moveInk(tabs[0]);

/* ---------------- file selection ---------------- */
const OK = /\.(pdf|docx|txt)$/i;
const fmtSize = (b) => (b < 1024 * 1024 ? (b / 1024).toFixed(0) + " KB" : (b / 1048576).toFixed(1) + " MB");
function setFile(f) {
  hideError();
  if (f && !OK.test(f.name)) { showError("Unsupported file. Use PDF, DOCX or TXT."); f = null; }
  else if (f && f.size > 5 * 1024 * 1024) { showError("File is larger than 5 MB."); f = null; }
  file = f || null;
  fileRow.hidden = !file; drop.hidden = !!file;
  if (file) { $("#file-name").textContent = file.name; $("#file-size").textContent = fmtSize(file.size); }
  update();
}
fileInput.addEventListener("change", () => setFile(fileInput.files[0]));
$("#file-clear").addEventListener("click", () => { fileInput.value = ""; setFile(null); });
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("is-over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("is-over"); }));
drop.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));
text.addEventListener("input", update);

function update() { if (!go.classList.contains("is-loading")) go.disabled = mode === "upload" ? !file : !text.value.trim(); }
function showError(m) { err.textContent = m; err.hidden = false; }
function hideError() { err.hidden = true; }

/* ---------------- button: ripple + loading ---------------- */
go.addEventListener("pointerdown", (e) => {
  if (go.disabled || REDUCED) return;
  const r = go.getBoundingClientRect(), dot = document.createElement("span");
  dot.className = "ripple"; dot.style.left = e.clientX - r.left + "px"; dot.style.top = e.clientY - r.top + "px";
  go.append(dot); setTimeout(() => dot.remove(), 750);
});

const STEPS = ["Reading document", "Cleaning text", "Running model", "Finding keywords", "Sorting by category"];
let stepTimer;
function startLoading() {
  go.classList.add("is-loading"); go.disabled = true; go.setAttribute("aria-busy", "true");
  panel.style.setProperty("--panel-h", panel.offsetHeight + "px"); panel.classList.add("is-scanning");
  let i = 0; busyText.textContent = STEPS[0];
  stepTimer = setInterval(() => {
    i = Math.min(i + 1, STEPS.length - 1);
    busyText.classList.add("swap");
    setTimeout(() => { busyText.textContent = STEPS[i]; busyText.classList.remove("swap"); }, 250);
  }, 700);
}
function stopLoading() {
  clearInterval(stepTimer);
  go.classList.remove("is-loading"); go.removeAttribute("aria-busy"); panel.classList.remove("is-scanning"); update();
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
go.addEventListener("click", async () => {
  if (go.disabled) return;
  hideError();
  const fd = new FormData();
  if (mode === "upload") fd.append("file", file); else fd.append("text", text.value);
  startLoading();
  try {
    const [res] = await Promise.all([fetch("/api/extract", { method: "POST", body: fd }), wait(REDUCED ? 0 : 1800)]);
    const data = await res.json().catch(() => ({ error: "Server error. Please try again." }));
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    stopLoading(); render(data);
  } catch (e) {
    stopLoading(); showError(e.message || "Network error. Is the server running?");
  }
});

/* ---------------- render with timeline ---------------- */
const ICON = {
  mail: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
  phone: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h3l2 5-2.5 1.5a11 11 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>',
  link: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1"/><path d="M14 10a4 4 0 0 0-5.66 0l-3 3a4 4 0 0 0 5.66 5.66l1-1"/></svg>',
};
const GROUPS = [
  { key: "skills", title: "Skills", cls: "g-skills", idx: "04" },
  { key: "tech", title: "Technologies", cls: "g-tech", idx: "05" },
  { key: "languages", title: "Languages", cls: "g-lang", idx: "06" },
];

function reveal(el, t) { el.style.setProperty("--t", t + "ms"); el.classList.add("rv"); requestAnimationFrame(() => el.classList.add("on")); }

function typeName(el, name, startAt) {
  const caret = $(".caret");
  caret.classList.remove("done");
  el.textContent = "";
  if (REDUCED) { el.textContent = name; caret.classList.add("done"); return; }
  setTimeout(() => {
    let i = 0;
    const tick = () => {
      el.textContent = name.slice(0, ++i);
      if (i < name.length) setTimeout(tick, 55 + Math.random() * 45); else caret.classList.add("done");
    };
    tick();
  }, startAt);
}

function countUp(el, to, startAt) {
  if (REDUCED || to === 0) { el.textContent = to; return; }
  el.textContent = "0";
  setTimeout(() => {
    const t0 = performance.now(), dur = 1100;
    const step = (t) => {
      const p = Math.min(1, (t - t0) / dur);
      el.textContent = Math.round(to * (1 - Math.pow(1 - p, 4)));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, startAt);
}

function render(data) {
  const p = data.profile || {};
  lastResult = data;
  const langs = (p.languages || []).map((l) => ({ keyword: l, count: 1 }));
  const isLang = new Set(langs.map((l) => l.keyword.toLowerCase()));   // show spoken languages only once
  const notLang = (x) => !isLang.has(x.keyword.toLowerCase());
  const lists = { skills: (data.skills || []).filter(notLang), tech: (data.tech || []).filter(notLang), languages: langs };

  results.hidden = false;
  results.querySelectorAll(".rv").forEach((el) => el.classList.remove("rv", "on"));
  $("#source").textContent = data.source || "";

  let t = 0;                                // master timeline (ms)
  const S = REDUCED ? 0 : 1;

  // header + profile card
  reveal($(".results-head"), t); t += 150 * S;
  reveal($("#profile"), t); t += 350 * S;

  const nameEl = $("#name-text"), nameH = $("#name");
  nameH.classList.toggle("is-empty", !p.name);
  typeName(nameEl, p.name || "Name not found", t);
  t += (p.name ? p.name.length * 75 : 400) * S + 200 * S;

  // contact
  const contact = $("#contact"); contact.innerHTML = "";
  const items = [
    ...(p.emails || []).map((v) => ({ icon: "mail", v, href: "mailto:" + v })),
    ...(p.phones || []).map((v) => ({ icon: "phone", v, href: "tel:" + v.replace(/[^\d+]/g, "") })),
    ...(p.links || []).map((v) => ({ icon: "link", v, href: /^https?:/i.test(v) ? v : "https://" + v })),
  ];
  reveal($('[data-field="contact"] .cat-label'), t);
  if (!items.length) contact.innerHTML = '<li class="none">No contact details found</li>';
  items.forEach((it) => {
    const li = document.createElement("li");
    li.innerHTML = ICON[it.icon];
    const a = document.createElement("a");
    a.href = it.href; a.textContent = it.v; if (it.icon === "link") { a.target = "_blank"; a.rel = "noopener"; }
    li.append(a); contact.append(li);
  });
  [...contact.children].forEach((li) => { t += 160 * S; reveal(li, t); });

  // address
  t += 200 * S;
  reveal($('[data-field="address"] .cat-label'), t);
  const addr = $("#address");
  addr.textContent = p.address || "No address found"; addr.classList.toggle("none", !p.address);
  t += 150 * S; reveal(addr, t);

  // stats
  t += 300 * S; reveal($("#stats"), t);
  countUp($("#n-skill"), lists.skills.length, t);
  countUp($("#n-tech"), lists.tech.length, t + 100 * S);
  countUp($("#n-lang"), lists.languages.length, t + 200 * S);
  countUp($("#n-words"), data.words || 0, t + 300 * S);
  t += 450 * S;

  // keyword groups – chips appear one by one
  const total = lists.skills.length + lists.tech.length + lists.languages.length;
  const stepMs = Math.max(55, Math.min(140, 4200 / Math.max(total, 1))) * S;
  const groups = $("#groups"); groups.innerHTML = "";
  GROUPS.forEach((g) => {
    const items = lists[g.key];
    const sec = document.createElement("section");
    sec.className = `group ${g.cls}`;
    sec.setAttribute("aria-label", g.title);
    sec.innerHTML = `
      <div class="group-head">
        <h3 class="group-title"><span class="idx">${g.idx}</span>${g.title}</h3>
        <div class="group-tools">
          <span class="group-count">${String(items.length).padStart(2, "0")}</span>
          ${items.length ? `<button class="ghost" type="button" data-copy="${g.key}">Copy</button>` : ""}
        </div>
      </div>
      <span class="group-line" aria-hidden="true"></span>
      <ul class="chips"></ul>`;
    groups.append(sec);
    reveal(sec, t); sec.style.setProperty("--t", t + "ms");
    t += 380 * S;

    const ul = $(".chips", sec);
    if (!items.length) { ul.innerHTML = `<li class="none">None found</li>`; }
    items.forEach((it) => {
      const li = document.createElement("li");
      li.className = "chip";
      li.textContent = it.keyword;
      if (it.confidence != null) li.title = `${Math.round(it.confidence * 100)}% confidence · ${it.source}`;
      if (it.count > 1) {
        const s = document.createElement("small"); s.textContent = "×" + it.count;
        s.setAttribute("aria-label", `mentioned ${it.count} times`); li.append(s);
      }
      li.style.setProperty("--t", t + "ms");
      ul.append(li);
      requestAnimationFrame(() => li.classList.add("on"));
      t += stepMs;
    });
    t += 250 * S;
  });

  results.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", () => copy(lists[b.dataset.copy])));
  setTimeout(() => results.scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "start" }), REDUCED ? 0 : 120);
}

/* ---------------- actions ---------------- */
const toastEl = $("#toast");
function toast(m) { toastEl.textContent = m; toastEl.classList.add("show"); clearTimeout(toast.t); toast.t = setTimeout(() => toastEl.classList.remove("show"), 1800); }
async function copy(list) {
  try { await navigator.clipboard.writeText(list.map((x) => x.keyword).join(", ")); toast("Copied to clipboard"); }
  catch { toast("Couldn't copy"); }
}
$("#download").addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: "application/json" });
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: "resume_keywords.json" });
  a.click(); URL.revokeObjectURL(a.href);
});
$("#reset").addEventListener("click", () => {
  results.hidden = true; fileInput.value = ""; setFile(null); text.value = ""; update();
  scrollTo({ top: 0, behavior: REDUCED ? "auto" : "smooth" });
});
