"""Resume improvement suggestions.

Hard rule: never invent skills, experience or numbers. Suggestions only (a) point out real gaps in
presentation and (b) tell the user to add a skill *only if they genuinely have it*.
"""
import re

STRONG_VERBS = "Built, Developed, Designed, Implemented, Optimized, Automated, Led, Reduced, Integrated"


def resume_health(r: dict) -> dict:
    """r: dict with full_name,email,phone,summary,education,experience,projects,certifications,skills,stats,linkedin,github."""
    st = r.get("stats", {})
    checks = [
        ("Contact details (email + phone)", 10, bool(r.get("email")) and bool(r.get("phone"))),
        ("Professional links (LinkedIn / GitHub)", 5, st.get("has_linkedin") or st.get("has_github")),
        ("Summary / objective", 10, bool(r.get("summary"))),
        ("Education section", 10, bool(r.get("education"))),
        ("Experience or internship section", 15, bool(r.get("experience"))),
        ("Projects section", 10, bool(r.get("projects"))),
        ("8+ recognisable skills", 15, len(r.get("skills", [])) >= 8),
        ("Quantified achievements (numbers / %)", 10, st.get("metric_bullets", 0) >= 2),
        ("Strong action verbs", 5, st.get("strong_verb_bullets", 0) >= 3),
        ("Certifications", 5, bool(r.get("certifications"))),
        ("Reasonable length (250-900 words)", 5, 250 <= st.get("word_count", 0) <= 900),
    ]
    score = sum(w for _, w, ok in checks if ok)
    return {"score": score, "checks": [{"label": l, "weight": w, "ok": bool(ok)} for l, w, ok in checks]}


def build_suggestions(r: dict, missing=None, related=None, jd_title="") -> list:
    st = r.get("stats", {})
    out = []

    def add(kind, priority, text):
        out.append({"type": kind, "priority": priority, "text": text})

    # ---- JD-specific (skills: honest wording, never "add X" blindly)
    for m in (missing or [])[:6]:
        if m["priority"] == "low" and len(out) >= 4:
            continue
        rel = m.get("related_have") or []
        if rel:
            add("skill", "high" if m["priority"] == "high" else "medium",
                f"The job asks for {m['name']}. You list {', '.join(rel)}, which is related — if you've actually used {m['name']}, "
                f"add it with where you used it; otherwise describe your {rel[0]} work clearly and mention you're learning {m['name']}.")
        else:
            add("skill", "high" if m["priority"] == "high" else "medium",
                f"The job asks for {m['name']}. Add it only if you have real experience (coursework and personal projects count). "
                f"If not, treat it as a learning goal — don't list it on the resume.")

    # ---- generic quality
    if not r.get("email") or not r.get("phone"):
        add("contact", "high", "Add a professional email and phone number at the top so recruiters can reach you.")
    if not (st.get("has_linkedin") or st.get("has_github")):
        add("links", "medium", "Add your LinkedIn and/or GitHub link — recruiters for tech roles usually check them.")
    if not r.get("summary"):
        tail = f" for {jd_title}" if jd_title else ""
        add("summary", "medium", f"Add a 2-3 line summary{tail} built only from what's already on your resume: your degree, main stack and one strongest project.")
    if len(r.get("skills", [])) < 8:
        add("skills", "medium", "Your skills section looks thin. List the tools you have genuinely used, grouped by category (Languages, Backend, Databases, Tools).")
    bullets = st.get("bullet_count", 0)
    if bullets and st.get("metric_bullets", 0) / bullets < 0.3:
        add("impact", "high", "Few bullets contain measurable results. Where you truly have numbers (users, % faster, records handled, team size), add them. Don't estimate figures you can't back up.")
    if st.get("weak_bullets"):
        ex = st["weak_bullets"][0][:70]
        add("wording", "medium", f"Start bullets with action verbs instead of phrases like \"{ex}…\". Options: {STRONG_VERBS}.")
    if not r.get("experience") and not r.get("projects"):
        add("content", "high", "No experience or projects detected. Add internships, academic or personal projects with the tech used and your role.")
    elif not r.get("projects"):
        add("projects", "medium", "Add 2-3 projects: what it does, your stack, and one concrete outcome.")
    for p in (r.get("projects") or [])[:4]:
        if not p.get("technologies"):
            add("projects", "low", f"Project \"{p['name'][:40]}\" doesn't mention its tech stack — add the technologies you used.")
            break
    if not r.get("certifications"):
        add("certs", "low", "Optional: relevant certifications or completed courses (only ones you have finished) can strengthen the profile.")
    wc = st.get("word_count", 0)
    if wc and wc < 250:
        add("length", "medium", "The resume is quite short. Expand descriptions of your projects and internships with what you built and how.")
    elif wc > 900:
        add("length", "medium", "The resume is long. Aim for one page (two at most) — cut older or less relevant items.")
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda s: order[s["priority"]])
    return out[:12]
