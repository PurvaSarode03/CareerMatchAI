"""Skill vocabulary loading and phrase-based skill extraction."""
import re
from dataclasses import dataclass, field

from .seed_data import RELATED_GROUPS, SKILLS


@dataclass(frozen=True)
class SkillDef:
    name: str
    category: str = "other"
    aliases: tuple = ()


@dataclass
class SkillHit:
    name: str
    category: str
    count: int = 1


_cache = {"key": None, "compiled": None}


def seed_vocab():
    return [SkillDef(n, c, tuple(a)) for n, c, a in SKILLS]


def db_vocab():
    """Skills from the DB (admin-managed). Falls back to the seed vocabulary."""
    try:
        from jobs.models import Skill
        rows = list(Skill.objects.filter(is_active=True).values_list("name", "category", "aliases"))
    except Exception:  # DB not ready / not migrated
        rows = []
    if not rows:
        return seed_vocab()
    return [SkillDef(n, c, tuple(a.strip() for a in (al or "").split(",") if a.strip())) for n, c, al in rows]


def load_related_map():
    """name -> set(related names). From DB when available, otherwise from seed groups."""
    try:
        from jobs.models import Skill
        mapping = {}
        for s in Skill.objects.prefetch_related("related"):
            mapping[s.name] = {r.name for r in s.related.all()}
        if any(mapping.values()):
            return mapping
    except Exception:
        pass
    mapping = {}
    for group in RELATED_GROUPS:
        for n in group:
            mapping.setdefault(n, set()).update(x for x in group if x != n)
    return mapping


def _term_pattern(term: str) -> str:
    # Boundaries that also work for C++, C#, Node.js, CI/CD.
    return rf"(?<![\w+#]){re.escape(term)}(?![\w+#]|\.\w)"


def _compile(vocab):
    key = tuple((v.name, v.category, v.aliases) for v in vocab)
    if _cache["key"] == key:
        return _cache["compiled"]
    term_to_skill, terms = {}, []
    for v in vocab:
        candidates = list(v.aliases)
        if len(v.name) > 2 or not v.name.isalpha():  # bare "C", "R", "Go" match only via longer aliases
            candidates.append(v.name)
        for t in candidates:
            t = t.strip().lower()
            if t:
                term_to_skill[t] = v
                terms.append(t)
    terms = sorted(set(terms), key=len, reverse=True)  # longest first: "spring boot" before "spring"
    pattern = re.compile("|".join(_term_pattern(t) for t in terms), re.IGNORECASE) if terms else None
    _cache.update(key=key, compiled=(pattern, term_to_skill))
    return _cache["compiled"]


def extract_skills(text: str, vocab=None):
    """Return list[SkillHit] sorted by (count desc, name)."""
    vocab = vocab or db_vocab()
    pattern, term_to_skill = _compile(vocab)
    if not pattern or not text:
        return []
    hits = {}
    for m in pattern.finditer(text):
        sk = term_to_skill.get(m.group(0).lower())
        if not sk:
            continue
        if sk.name in hits:
            hits[sk.name].count += 1
        else:
            hits[sk.name] = SkillHit(sk.name, sk.category, 1)
    return sorted(hits.values(), key=lambda h: (-h.count, h.name))


def unknown_skill_tokens(skills_section: str, known_names, limit=25):
    """Tokens listed in a Skills section that are not in the vocabulary (helps admins grow it)."""
    known = {k.lower() for k in known_names}
    out = []
    for chunk in re.split(r"[,\n•|;/]", skills_section or ""):
        tok = re.sub(r"^[A-Za-z &]{2,25}:\s*", "", chunk).strip(" .:-")
        if 1 < len(tok) <= 30 and len(tok.split()) <= 3 and tok.lower() not in known and re.search(r"[A-Za-z]", tok):
            out.append(tok)
    seen, uniq = set(), []
    for t in out:
        if t.lower() not in seen:
            seen.add(t.lower())
            uniq.append(t)
    return uniq[:limit]
