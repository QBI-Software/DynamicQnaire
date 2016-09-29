from django import forms
from django.forms import Form, ModelForm, DateInput
from django.forms.formsets import BaseFormSet
from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField

from .models import *

class LoginForm(AuthenticationForm):
    class Meta:
        fields = ('username', 'password')
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control', 'name': 'username'}),
                   'password': forms.PasswordInput(attrs={'class': 'form-control', 'name': 'password'})
                   }


class AxesCaptchaForm(Form):
    captcha = CaptchaField()

class QuestionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = TestResult
        fields = ['test_result_question','test_result_choice']

class QuestionnaireForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = Questionnaire
        fields = '__all__'

class MultipageQuestionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        print('DEBUG: Qform: kwargs=', kwargs)
        initvals = kwargs.get('initial')
        #print("DEBUG: initvals=", initvals)
        super().__init__(*args, **kwargs)
        if (initvals):
            qid = initvals.get('qid')
            #print("DEBUG: Qid=", qid)

            question = Question.objects.get(pk=qid)
            print("DEBUG: Qn=", question.id)

            self.fields['question'] = forms.ChoiceField(label=question.question_text,
                                                        widget=forms.RadioSelect, required=True,
                                                        choices=[(c.choice_value, c.choice_text) for c in question.choice_set.all()])
            for field in iter(self.fields):
                self.fields[field].widget.attrs.update({
                    'class': 'form-check'
                })



#Form for questionnaire test
class BaseQuestionFormSet(BaseFormSet):
    def get_form_kwargs(self, index):
        kwargs = super(BaseQuestionFormSet, self).get_form_kwargs(index)
        print('BASEFORM kwargs:', kwargs)
        return kwargs

    def clean(self):
        """
        Adds validation to check that no two links have the same anchor or URL
        and that all links have both an anchor and URL.
        """
        if any(self.errors):
            return
        results = []
        for form in self.forms:
            print("FORM:", self)
            title = form.cleaned_data #['question']

        results.append(title)
        return results



# Test form wizard
class ContactForm1(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()

class ContactForm2(forms.Form):
    message = forms.CharField(widget=forms.Textarea)