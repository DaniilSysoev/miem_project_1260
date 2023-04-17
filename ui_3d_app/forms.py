from django import forms


class PostPrintJobForm(forms.Form):
    job_name = forms.CharField(max_length=100, placeholder="Job name")
    file = forms.FileField()
