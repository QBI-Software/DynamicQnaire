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


class AnswerForm(Form):
    """Loads a question and multiple choice answer - WORKING """
    def __init__(self, *args, **kwargs):
        #print('DEBUG: Qform: kwargs=', kwargs)
        qid = kwargs.get('initial')
        #print("DEBUG: Qid=", qid)
        super().__init__(*args, **kwargs)
        if (qid):
            question = qid.get('qid')
            #print("DEBUG: Qn=", question.id)
            self.fields['question'] = forms.ChoiceField(
                        label=question.question_text,
                        widget=forms.RadioSelect(attrs={'class': 'form-check'}),
                        required=True,
                        choices=[(c.choice_value, c.choice_text) for c in question.choice_set.all()],

            )


    class Meta:
        fields =('question')



class BaseQuestionFormSet(BaseFormSet):
    """ Use for multiple questions per page as formset """
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

