from django import forms
from django.forms import Form, ModelForm, DateInput
from .models import *

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

class QuestionForm(ModelForm):
    qid = 1
    question = Question.objects.get(pk=qid)
    question_text = forms.ModelChoiceField(label=question.question_text, queryset=question.choice_set.all())

    def __init__(self, *args, **kwargs):
        print('DEBUG:Qform: kwargs=', kwargs)
        initvals = kwargs.get('initial')
        qid = initvals.get('qid')
        print("DEBUG: QformTEXT=", qid)
        #print("FIELDS=", self.fields)
        super().__init__(*args, **kwargs)
        #print("DEBUG: QformTEXT2=", len(qtext))
        #print("FIELDS2=", self.fields['question_text'])
        #self.fields['question_text'].label = initvals.get('qtext')
        #self.fields['question_text'].queryset = initvals.get('qchoices')


    class Meta:
        model = Question
        fields = ['question_text']

# Test form wizard
class ContactForm1(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()

class ContactForm2(forms.Form):
    message = forms.CharField(widget=forms.Textarea)