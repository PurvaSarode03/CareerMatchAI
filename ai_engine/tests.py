from django.test import SimpleTestCase

from ai_engine.parser import parse_resume
from ai_engine.skills import extract_skills, seed_vocab
from ai_engine.suggestions import build_suggestions

SAMPLE = """JOHN DOE
john.doe@example.com | +91 98765 43210 | github.com/johndoe

EDUCATION
B.Tech Computer Science
Sample Institute of Technology, Pune | 2020 - 2024 | CGPA: 8.1/10

EXPERIENCE
Software Intern | Acme Corp | Jun 2023 - Aug 2023
• Built REST APIs using Django and PostgreSQL for 1,000+ users

PROJECTS
Chat App | React, Node.js
• Developed a realtime chat app

SKILLS
Python, Django, React, Node.js, Git, C++, C#
"""


class ParserTests(SimpleTestCase):
    def test_contact_and_sections(self):
        p = parse_resume(SAMPLE)
        self.assertEqual(p.full_name, "John Doe")
        self.assertEqual(p.email, "john.doe@example.com")
        self.assertTrue(p.phone.startswith("+91"))
        self.assertEqual(p.education[0]["institution"], "Sample Institute of Technology")
        self.assertEqual(p.experience[0]["company"], "Acme Corp")
        self.assertEqual(p.projects[0]["name"], "Chat App")

    def test_skill_boundaries(self):
        names = {h.name for h in extract_skills("I know JavaScript, C++, C# and Node.js.", seed_vocab())}
        self.assertIn("JavaScript", names)
        self.assertIn("C++", names)
        self.assertIn("C#", names)
        self.assertIn("Node.js", names)
        self.assertNotIn("Java", names)   # 'JavaScript' must not trigger 'Java'
        self.assertIn("Java", {h.name for h in extract_skills("Core Java and Spring Boot", seed_vocab())})

    def test_suggestions_never_invent(self):
        s = build_suggestions({"skills": [], "stats": {}}, [{"name": "Kubernetes", "priority": "high", "related_have": []}])
        text = " ".join(x["text"] for x in s)
        self.assertIn("only if you have real experience", text)
