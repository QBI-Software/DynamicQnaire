from django import forms
from django.forms import Form, ModelForm, DateInput
from .models import Question


class BaseForm(Form):
    def is_valid(self):
        return super(BaseForm, self).is_valid()


class ParentForm1(BaseForm):
    dob = forms.DateField()
    spouse_dob = forms.DateField()
    maiden_name = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        qns = Question.objects.filter(qid__code='DEM001').filter(order=1)
        super().__init__(*args, **kwargs)


class ParentForm2(BaseForm):
    message = forms.CharField(widget=forms.Textarea)
    multivalue = forms.MultipleChoiceField(choices=[('testa', 'Test A'), ('testb', 'Test B')])


class ParentForm3(BaseForm):
    field1 = forms.CharField(max_length=100)
    field2 = forms.CharField(max_length=100)


class ParentForm4(BaseForm):
    field1 = forms.IntegerField()


class ParentForm5(BaseForm):
    name = forms.ChoiceField(choices=[('test1', 'Test 1'), ('test2', 'Test 2')])