"""Rule + NLP based resume parser (name, contact, education, experience, projects, certifications, skills)."""
import re
from dataclasses import asdict, dataclass, field
from datetime import date

from .skills import extract_skills, unknown_skill_tokens

SECTION_ALIASES = {
    "summary": ["summary", "professional summary", "career objective", "objective", "profile", "about me", "about"],
    "education": ["education", "academic background", "academics", "educational qualification", "educational qualifications", "qualifications"],
    "experience": ["experience", "work experience", "professional experience", "internship", "internships",
                   "work history", "employment history", "employment", "internship experience"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project work", "major projects"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "skills summary", "technologies", "tech stack"],
    "certifications": ["certifications", "certificates", "licenses", "courses", "certifications and courses",
                       "licenses and certifications", "training"],
    "achievements": ["achievements", "awards", "honors", "accomplishments", "extracurricular", "extracurricular activities",
                     "activities", "positions of responsibility", "publications", "interests", "hobbies", "languages"],
}
_HEADING_LOOKUP = {a: k for k, v in SECTION_ALIASES.items() for a in v}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\d{5}[\s-]?\d{5}|\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4})(?!\d)")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s,|]+", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s,|]+", re.I)
YEAR_RE = re.compile(r"\b(19[89]\d|20[0-4]\d)\b")
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
DATE_TOKEN = rf"(?:(?:{MONTHS})[a-z]*\.?\s*\d{{4}}|\d{{1,2}}/\d{{4}}|\d{{4}})"
DATE_RANGE_RE = re.compile(rf"({DATE_TOKEN})\s*(?:-|–|—|to)\s*({DATE_TOKEN}|present|current|ongoing|now)", re.I)
DEGREE_RE = re.compile(
    r"\b(b\.?\s?e\.?|b\.?\s?tech|b\.?\s?sc|b\.?\s?c\.?a|b\.?\s?com|b\.?\s?a\b|m\.?\s?tech|m\.?\s?sc|m\.?\s?c\.?a|m\.?\s?b\.?\s?a|"
    r"m\.?\s?e\b|ph\.?\s?d|bachelor[s]?|master[s]?|diploma|hsc|ssc|(?:12|10)th\b|higher secondary|secondary school)\b", re.I)
INSTITUTION_RE = re.compile(r"\b(college|university|institute|school|academy|polytechnic|vidyalaya|iit|nit)\b", re.I)
SCORE_RE = re.compile(r"(?:cgpa|gpa|percentage|grade)?\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?\s*(?:%|/\s*10|cgpa|gpa)|\d{1,2}\.\d{1,2})", re.I)
BULLET_RE = re.compile(r"^\s*(?:•|\*|-|–|▪|>)\s*")
WEAK_STARTS = ("responsible for", "worked on", "helped", "involved in", "assisted", "tasked with", "duties included")
ACTION_VERBS = {"built", "developed", "designed", "implemented", "created", "led", "optimized", "reduced", "improved",
                "automated", "deployed", "engineered", "architected", "integrated", "launched", "migrated", "analyzed",
                "analysed", "delivered", "managed", "streamlined", "refactored", "mentored", "collaborated", "trained",
                "achieved", "increased", "designed", "authored", "established", "researched", "tested", "configured"}
_MONTH_NUM = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}


@dataclass
class ParsedResume:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    summary: str = ""
    education: list = field(default_factory=list)
    experience: list = field(default_factory=list)
    projects: list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    skills: list = field(default_factory=list)      # list[dict(name, category, count)]
    unmapped_skills: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


# ------------------------------------------------------------------ helpers
_nlp = {"model": None, "tried": False}


def _spacy_model():
    """Optional spaCy NER for names. Returns None when spaCy / model is not installed."""
    if not _nlp["tried"]:
        _nlp["tried"] = True
        try:
            import spacy
            _nlp["model"] = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
        except Exception:
            _nlp["model"] = None
    return _nlp["model"]


def _heading_key(line: str):
    clean = re.sub(r"[^a-zA-Z& ]", " ", line).strip().lower()
    clean = re.sub(r"\s+", " ", clean)
    if not clean or len(clean.split()) > 5 or len(line) > 45:
        return None
    return _HEADING_LOOKUP.get(clean.replace(" & ", " and "))


def split_sections(text: str) -> dict:
    """Return {section: [lines]}; the lines before the first heading go into 'header'."""
    sections = {"header": []}
    current = "header"
    for line in text.split("\n"):
        key = _heading_key(line) if line.strip() else None
        if key:
            current = key
            sections.setdefault(current, [])
        else:
            sections[current].append(line)
    return sections


def _parse_date(tok: str):
    tok = tok.lower().strip()
    if tok in ("present", "current", "ongoing", "now"):
        return date.today()
    m = re.match(rf"({MONTHS})[a-z]*\.?\s*(\d{{4}})", tok)
    if m:
        return date(int(m.group(2)), _MONTH_NUM[m.group(1)[:3]], 1)
    m = re.match(r"(\d{1,2})/(\d{4})", tok)
    if m and 1 <= int(m.group(1)) <= 12:
        return date(int(m.group(2)), int(m.group(1)), 1)
    m = re.match(r"(\d{4})", tok)
    return date(int(m.group(1)), 1, 1) if m else None


def _chunks(lines):
    """Group lines into entries: split on blank lines, and on a new dated header after bullets."""
    chunks, cur, prev_bullet = [], [], False
    for line in lines:
        s = line.strip()
        if not s:
            if cur:
                chunks.append(cur)
                cur, prev_bullet = [], False
            continue
        is_bullet = bool(BULLET_RE.match(s))
        if cur and not is_bullet and prev_bullet and DATE_RANGE_RE.search(s):
            chunks.append(cur)
            cur = []
        cur.append(s)
        prev_bullet = is_bullet
    if cur:
        chunks.append(cur)
    return chunks


# ------------------------------------------------------------------ field extractors
def extract_name(text: str, header_lines, email: str) -> str:
    nlp = _spacy_model()
    if nlp:
        doc = nlp(text[:400])
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 4 and "\n" not in ent.text:
                return ent.text.strip().title()
    for line in [l.strip() for l in header_lines if l.strip()][:8]:
        if re.search(r"[\d@/:|]", line) or _heading_key(line):
            continue
        words = re.sub(r"[^A-Za-z .'-]", "", line).split()
        if 2 <= len(words) <= 4 and all(w[0].isalpha() for w in words):
            if line.isupper() or all(w[0].isupper() for w in words):
                return " ".join(w.capitalize() if line.isupper() else w for w in words)
    if email:
        local = re.split(r"[._\d]+", email.split("@")[0])
        parts = [p for p in local if len(p) > 1][:3]
        if parts:
            return " ".join(p.capitalize() for p in parts)
    return ""


def parse_education(lines):
    entries = []
    for chunk in _chunks(lines) or []:
        # inside one chunk, a new degree line starts a new entry
        current = None
        for line in chunk:
            clean = BULLET_RE.sub("", line)
            if DEGREE_RE.search(clean) and (current is None or current.get("degree")):
                current = {"degree": "", "institution": "", "year": "", "score": ""}
                entries.append(current)
            if current is None:
                current = {"degree": "", "institution": "", "year": "", "score": ""}
                entries.append(current)
            if DEGREE_RE.search(clean) and not current["degree"]:
                current["degree"] = re.split(r"\s+(?:\||–|—|-)\s+|,\s*(?=[A-Z])", clean)[0][:120].strip()
            if INSTITUTION_RE.search(clean) and not current["institution"]:
                inst = [p for p in re.split(r"\s+\|\s+|\s+[–—-]\s+|,\s*", clean) if INSTITUTION_RE.search(p)]
                current["institution"] = re.sub(YEAR_RE, "", (inst[0] if inst else clean)).strip(" ,-|()")[:140]
            years = YEAR_RE.findall(clean)
            if years and not current["year"]:
                current["year"] = " - ".join(dict.fromkeys(years))
            sc = SCORE_RE.search(clean)
            if sc and re.search(r"cgpa|gpa|%|percent|/\s*10", clean, re.I) and not current["score"]:
                current["score"] = sc.group(1).strip()
    return [e for e in entries if e["degree"] or e["institution"]]


def parse_experience(lines):
    entries, total_months = [], 0
    for chunk in _chunks(lines):
        head = chunk[0]
        body = chunk[1:]
        dates = DATE_RANGE_RE.search(" ".join(chunk[:3]))
        title, company = head, ""
        head_clean = DATE_RANGE_RE.sub("", head).strip(" |–—-,")
        parts = [p.strip() for p in re.split(r"\s+\|\s+|\s+[–—]\s+|\s+@\s+|\s+at\s+|,\s+(?=[A-Z])", head_clean) if p.strip()]
        if parts:
            title = parts[0]
            company = parts[1] if len(parts) > 1 else ""
        if not company and body and not BULLET_RE.match(body[0]) and len(body[0].split()) <= 8:
            company = DATE_RANGE_RE.sub("", body[0]).strip(" |–—-,")
            body = body[1:]
        bullets = [BULLET_RE.sub("", b) for b in body if b]
        period = ""
        if dates:
            period = f"{dates.group(1)} - {dates.group(2)}"
            a, b = _parse_date(dates.group(1)), _parse_date(dates.group(2))
            if a and b and b >= a:
                total_months += (b.year - a.year) * 12 + (b.month - a.month) + 1
        entries.append({"title": title[:140], "company": company[:140], "period": period, "bullets": bullets[:12]})
    return entries, round(total_months / 12, 1)


def parse_projects(lines):
    entries = []
    for chunk in _chunks(lines):
        head = BULLET_RE.sub("", chunk[0])
        name, inline = head, ""
        m = re.match(r"^(.{3,80}?)\s*(?:\||–|—|:|\()\s*(.+)$", head)
        if m and len(m.group(1).split()) <= 8:
            name, inline = m.group(1).strip(), m.group(2).strip(" )")
        bullets = [BULLET_RE.sub("", b) for b in chunk[1:]]
        text = " ".join([head] + bullets)
        techs = [h.name for h in extract_skills(text)]
        entries.append({"name": name[:120], "description": (inline + " " + " ".join(bullets)).strip()[:600],
                        "bullets": bullets[:8], "technologies": techs})
    return entries


def parse_certifications(lines):
    out = []
    for line in lines:
        s = BULLET_RE.sub("", line.strip())
        if len(s) < 4:
            continue
        issuer = ""
        m = re.split(r"\s+[–—|]\s+|\s+-\s+|\s+by\s+|\s+from\s+", s, maxsplit=1)
        name = m[0].strip()
        if len(m) > 1:
            issuer = m[1].strip()
        out.append({"name": name[:140], "issuer": issuer[:100], "year": (YEAR_RE.findall(s) or [""])[-1]})
    return out


# ------------------------------------------------------------------ main entrypoint
def parse_resume(text: str) -> ParsedResume:
    sections = split_sections(text)
    p = ParsedResume()
    head_text = "\n".join(sections["header"][:12]) or text[:500]

    m = EMAIL_RE.search(text)
    p.email = m.group(0).lower() if m else ""
    m = PHONE_RE.search(head_text) or PHONE_RE.search(text)
    p.phone = re.sub(r"\s+", " ", m.group(0)).strip() if m and len(re.sub(r"\D", "", m.group(0))) >= 10 else ""
    m = LINKEDIN_RE.search(text)
    p.linkedin = m.group(0) if m else ""
    m = GITHUB_RE.search(text)
    p.github = m.group(0) if m else ""
    p.full_name = extract_name(text, sections["header"], p.email)
    p.summary = " ".join(l.strip() for l in sections.get("summary", []) if l.strip())[:600]
    p.education = parse_education(sections.get("education", []))
    p.experience, years = parse_experience(sections.get("experience", []))
    p.projects = parse_projects(sections.get("projects", []))
    p.certifications = parse_certifications(sections.get("certifications", []))

    hits = extract_skills(text)
    p.skills = [{"name": h.name, "category": h.category, "count": h.count} for h in hits]
    p.unmapped_skills = unknown_skill_tokens("\n".join(sections.get("skills", [])), [h.name for h in hits])

    all_bullets = [BULLET_RE.sub("", l) for sec in ("experience", "projects") for l in sections.get(sec, [])
                   if BULLET_RE.match(l.strip())]
    metric_bullets = [b for b in all_bullets if re.search(r"\d+\s*(%|x|\+|k\b|users|ms|hrs|hours|requests|records|clients)|\b\d{2,}\b", b)]
    weak = [b for b in all_bullets if b.lower().startswith(WEAK_STARTS)]
    strong = [b for b in all_bullets if b.split() and b.split()[0].lower().rstrip(",") in ACTION_VERBS]
    p.stats = {
        "word_count": len(text.split()),
        "sections_found": sorted(k for k, v in sections.items() if k != "header" and any(x.strip() for x in v)),
        "bullet_count": len(all_bullets),
        "metric_bullets": len(metric_bullets),
        "weak_bullets": weak[:5],
        "strong_verb_bullets": len(strong),
        "experience_years": years,
        "has_linkedin": bool(p.linkedin),
        "has_github": bool(p.github),
    }
    return p
