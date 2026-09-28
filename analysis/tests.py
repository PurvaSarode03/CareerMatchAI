import io
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from docx import Document

from analysis.models import Analysis
from jobs.models import Job
from resumes.models import Resume

TMP_MEDIA = tempfile.mkdtemp()


def make_docx():
    d = Document()
    for line in ["Asha Rao", "asha@example.com | 9876543210", "SKILLS", "Python, Django, MySQL, Git, HTML, CSS, Bootstrap, JavaScript",
                 "PROJECTS", "Shop | Django, MySQL", "• Built an online store with Django and MySQL supporting 200+ orders",
                 "EDUCATION", "B.E. Information Technology", "Mumbai University College | 2022 - 2026"]:
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class EndToEnd(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("seed_data", verbosity=0)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def register(self, name="asha"):
        return self.client.post(reverse("accounts:register"), {
            "username": name, "first_name": "Asha", "email": f"{name}@example.com",
            "password1": "S3cure-pass-987", "password2": "S3cure-pass-987"})

    def upload(self, content=None, name="cv.docx"):
        return self.client.post(reverse("resumes:upload"), {"title": "My CV", "file": SimpleUploadedFile(name, content or make_docx())})

    def test_full_flow(self):
        self.assertEqual(self.register().status_code, 302)
        r = self.upload()
        resume = Resume.objects.get()
        self.assertRedirects(r, reverse("resumes:detail", args=[resume.pk]))
        self.assertIn("Django", [s.name for s in resume.skills.all()])
        self.assertEqual(resume.full_name, "Asha Rao")

        job = Job.objects.get(title__startswith="Full Stack Developer (Django")
        r = self.client.post(reverse("analysis:new"), {"resume": resume.pk, "job": job.pk})
        a = Analysis.objects.get()
        self.assertRedirects(r, reverse("analysis:detail", args=[a.pk]))
        self.assertTrue(0 <= a.score <= 100)
        self.assertIn("Django", a.matched_skills)

        # pasted JD
        self.client.post(reverse("analysis:new"), {"resume": resume.pk, "job_title": "X", "job_description": "We need Kubernetes, Docker and AWS engineers for cloud work."})
        self.assertEqual(Analysis.objects.count(), 2)
        for name in ("dashboard:home", "analysis:history", "jobs:list", "jobs:recommended", "resumes:list"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("analysis:detail", args=[a.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("jobs:list"), {"q": "django"}).status_code, 200)

    def test_upload_rejects_bad_files(self):
        self.register()
        self.upload(b"MZ\x90\x00 not a pdf", "evil.pdf")
        self.upload(b"hello", "notes.txt")
        self.assertEqual(Resume.objects.count(), 0)

    def test_privacy_between_users(self):
        self.register("alice")
        self.upload()
        pk = Resume.objects.get().pk
        self.client.logout()
        self.register("bob")
        self.assertEqual(self.client.get(reverse("resumes:detail", args=[pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("resumes:download", args=[pk])).status_code, 404)

    def test_login_required(self):
        r = self.client.get(reverse("dashboard:home"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r["Location"])
