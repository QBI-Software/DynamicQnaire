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
    """Loads a question and multiple choice answer """
    def __init__(self, *args, **kwargs):
        qid = kwargs.get('initial')
        super().__init__(*args, **kwargs)
        if (qid):
            question = qid.get('qid')
            user = qid.get('myuser')
            print("DEBUG: Qn=", question.id)
            #Check type
            if question.question_image is not None:
                self.qimage = question.question_image
            choices = []
            #Filter for user groups - ignore for superuser
            usergrouplist = user.groups.values_list('name')
            print('DEBUG: user groups=', usergrouplist)

            for c in question.choice_set.order_by('pk'):
                includeflag = 1
                #If choice has groups - check they are in user groups
                if (not user.is_superuser and c.group.count() > 0):
                    choicegroups = c.group.values_list('name')
                    print('DEBUG: choice groups=',choicegroups)
                    includeflag = (set(choicegroups) <= set(usergrouplist))

                if includeflag:
                    index = (c.choice_value, c)
                    choices.append(index)
            #Options for choices

            if question.question_type == 1:
                self.fields['question'] = forms.ChoiceField(
                    label=question.question_text,
                    help_text='radio',  # use this to detect type
                    widget=forms.RadioSelect(attrs={'class': 'form-control'}),
                    required=question.question_required,
                    choices=choices,
                )
            elif question.question_type == 2:
                self.fields['question'] = forms.MultipleChoiceField(
                label=question.question_text,
                help_text='checkbox',
                widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
                required=question.question_required,
                choices=choices,
            )
            elif question.question_type == 3:
                self.fields['question'] = forms.CharField(
                    label=question.question_text,
                    help_text='text',
                    widget=forms.TextInput(attrs={'class': 'form-control'}),
                    required=question.question_required,

                )
            elif question.question_type == 4:
                print('DEBUG: Dropdown list')
                self.fields['question'] = forms.CharField(
                    label=question.question_text,
                    widget=forms.Select(attrs={'class': 'form-control'}),
                    help_text='select',
                    required=question.question_required,
                    choices=choices,
                )


    class Meta:
        fields =('question')

############### SINGLE PAGE #################
class SinglepageQuestionForm(forms.Form):

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

class TestResultBulkDeleteForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = TestResult
        fields = '__all__'

