from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import Form, ModelForm
from django.forms.formsets import BaseFormSet
import re
from itertools import chain
from .models import *


class LoginForm(AuthenticationForm):
    class Meta:
        fields = ('username', 'password')
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control', 'name': 'username'}),
                   'password': forms.PasswordInput(attrs={'class': 'form-control', 'name': 'password'})
                   }


class AxesCaptchaForm(Form):
    captcha = CaptchaField()

def replaceTwinNames(user,question_text):
    # Replace Twin1 and Twin2 with appropriate names
    # question.question_text
    pattern1 = 'Twin\s?1'
    pattern2 = 'Twin\s?2'
    twins = SubjectVisit.objects.filter(parent1=user)
    if not twins:
        twins = SubjectVisit.objects.filter(parent2=user)
    elif len(twins) == 1:
        twins = list(chain(twins, SubjectVisit.objects.filter(parent2=user)))
    if len(twins) == 2:
        print('DEBUG: QTEXT1=', question_text)
        question_text = re.sub(pattern1, twins[0].subject.first_name, question_text,
                                        flags=re.IGNORECASE)
        question_text = re.sub(pattern2, twins[1].subject.first_name, question_text,
                                        flags=re.IGNORECASE)
        print('DEBUG: QTEXT2=', question_text)
    return question_text

class AnswerForm(Form):
    qimage = None
    qbgcolor = "white"
    textcolor = "gray"
    usegrid = False
    tdcss = ''
    """Loads a question and multiple choice answer """
    def __init__(self, *args, **kwargs):
        qid = kwargs.get('initial')
        super().__init__(*args, **kwargs)
        if (qid):
            question = qid.get('qid')
            user = qid.get('myuser')
            if (type(question) is not Question):
                question = Question.objects.get(pk=question)
            #Check type
            if question.question_image is not None:
                self.qimage = question.question_image
            #Set bgcolor and text color - questions override questionnaire settings
            self.qbgcolor= question.qid.bgcolor
            if self.qbgcolor != question.bgcolor and question.bgcolor != BGDEFAULT:
                self.qbgcolor = question.bgcolor
            self.textcolor = question.qid.textcolor
            if self.textcolor != question.textcolor and question.textcolor != TCDEFAULT:
                self.textcolor = question.textcolor
            self.usegrid = question.usegrid
            csslist = dict(question.CSSCLASSES)
            self.tdcss = csslist[question.css]
            choices = []
            #Filter for user groups - ignore for superuser
            usergrouplist = user.groups.values_list('name')
            #Replace Twin1 and Twin2 with appropriate names
            question.question_text = replaceTwinNames(user, question.question_text)


            for c in question.choice_set.order_by('pk'):
                includeflag = 1
                #If choice has groups - check they are in user groups
                if (not user.is_superuser and c.group.count() > 0):
                    choicegroups = c.group.values_list('name')
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
                self.fields['question'] = forms.ChoiceField(
                    label=question.question_text,
                    widget=forms.Select(attrs={'class': 'form-control'}),
                    help_text='select',
                    required=question.question_required,
                    choices=choices,
                )
            elif question.question_type == 5:
                self.fields['question'] = forms.DateField(
                    label=question.question_text,
                    widget=forms.DateInput(format=('%d-%m-%Y'),
                                           attrs={'class': 'form-control',
                                             'type': 'date',
                                             'placeholder': 'Select a date'}
                                      ),
                    help_text='date',
                    required=question.question_required,
                )


    class Meta:
        fields =('question')

############### SINGLE PAGE #################
class BaseQuestionFormSet(BaseFormSet):
    """ Use for multiple questions per page as formset """

    def clean(self):
        """
        Adds validation to check that no two links have the same anchor or URL
        and that all links have both an anchor and URL.
        """
        if any(self.errors):
            return
        results = []
        for form in self.forms:
            title = form.cleaned_data

        results.append(title)
        return results


class TestResultDeleteForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = TestResult
        fields = '__all__'

##############################################
