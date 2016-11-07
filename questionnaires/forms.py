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
            self.qbgcolor= question.bgcolor
            self.textcolor = question.textcolor
            self.usegrid = question.usegrid
            csslist = dict(question.CSSCLASSES)
            self.tdcss = csslist[question.css]
            choices = []
            #Filter for user groups - ignore for superuser
            usergrouplist = user.groups.values_list('name')

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
########## Custom Forms ######################

class ContactForm1(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()
    leave_message = forms.BooleanField(required=False)


class ContactForm2(forms.Form):
    message = forms.CharField(widget=forms.Textarea)

#Load questions and choices from database
class CustomForm1(forms.Form):
    mainquestion = forms.ChoiceField(label="Has anyone teased you?", choices=[{0, 'No'}, {1, 'Yes'}],
                                     widget=forms.RadioSelect(attrs={'class': 'form-control'}))
    subquestion1 = forms.ChoiceField(label="How often?", choices=[{1, 'Most days'}, {2, 'Once a week'}],
                                     widget=forms.RadioSelect(attrs={'class': 'form-control'}))
    subquestion2 = forms.ChoiceField(label="How upset were you?", choices=[{1, 'Not at all'}, {2, 'A bit'}],
                                     widget=forms.RadioSelect(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        code = kwargs.pop('code', None)
        print("debug: form code=", code)
        super().__init__(*args, **kwargs)
        qs = Questionnaire.objects.get(code=code)
        questions = qs.question_set.filter(order=1)
        print("Debug: questions=",questions)
        # self.fields['mainquestion'].label= questions[0]
        # self.fields['mainquestion'].qs = questions[0].choice_set.all()
        # self.fields['subquestion1'].label = questions[1]
        # self.fields['subquestion1'].qs = questions[1].choice_set.all()
        # self.fields['subquestion2'].label = questions[2]
        # self.fields['subquestion2'].qs = questions[2].choice_set.all()

    class Meta:
        fields=['mainquestion', 'subquestion1', 'subquestion2']