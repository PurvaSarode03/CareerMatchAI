from django import forms

from .validators import validate_resume_file


class ResumeUploadForm(forms.Form):
    title = forms.CharField(max_length=120, required=False, help_text="Optional label, e.g. 'Java Developer resume'")
    file = forms.FileField(validators=[validate_resume_file], widget=forms.ClearableFileInput(
        attrs={"accept": ".pdf,.docx", "class": "form-control"}))
