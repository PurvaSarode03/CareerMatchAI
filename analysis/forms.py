from django import forms

from ai_engine.text_extraction import ExtractionError, extract_text
from jobs.models import Job
from resumes.validators import validate_resume_file


class AnalysisForm(forms.Form):
    resume = forms.ModelChoiceField(queryset=None, empty_label=None)
    job = forms.ModelChoiceField(queryset=Job.objects.filter(is_active=True), required=False,
                                 empty_label="— Paste / upload a job description instead —")
    job_title = forms.CharField(max_length=160, required=False)
    job_description = forms.CharField(widget=forms.Textarea(attrs={"rows": 9}), required=False)
    jd_file = forms.FileField(required=False, validators=[validate_resume_file],
                              widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.docx"}))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["resume"].queryset = user.resumes.all()
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-select" if isinstance(f, forms.ModelChoiceField) else "form-control")

    def clean(self):
        data = super().clean()
        text = (data.get("job_description") or "").strip()
        f = data.get("jd_file")
        if f and not text:
            try:
                text = extract_text(f, f.name)
            except ExtractionError as exc:
                self.add_error("jd_file", str(exc))
        job = data.get("job")
        if job and not text:
            text = f"{job.title}. {job.description}"
        if len(text) < 30 and not self.errors:
            raise forms.ValidationError("Provide a job description: paste text, upload a file, or pick a job.")
        data["jd_text"] = text
        return data
