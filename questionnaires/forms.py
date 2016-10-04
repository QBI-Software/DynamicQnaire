from django import forms
from django.forms import Form, ModelForm, DateInput
from django.forms.formsets import BaseFormSet
from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField
#from django.newforms.widgets import RadioFieldRenderer, RadioInput
#from django.utils.encoding import StrAndUnicode, force_unicode

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
    qimage = None
    """Loads a question and multiple choice answer - WORKING """
    def __init__(self, *args, **kwargs):
        #print('DEBUG: Qform: kwargs=', kwargs)
        qid = kwargs.get('initial')
        #print("DEBUG: Qid=", qid)
        super().__init__(*args, **kwargs)
        if (qid):
            question = qid.get('qid')
            user = qid.get('u')
            print("DEBUG: Qn=", question.id)
            #Check type
            if question.question_image is not None:
                self.qimage = '/static/media/%s' % question.question_image
            choices = []
            #Filter for user groups
            usergrouplist = user.groups.values_list('name')
            clist = question.choice_set.all() #filter(group__name__in=usergrouplist)
            for c in clist:
                print('DEBUG: Groups=',c.group.count())# > 0 && c.groups.values_list('name')
                index = (c.choice_value, c)
                choices.append(index)
            self.fields['question'] = forms.ChoiceField(
                        label=question.question_text,
                        widget=forms.RadioSelect(attrs={'class': 'form-check'}),
                        required=True,
                        choices=choices,
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

