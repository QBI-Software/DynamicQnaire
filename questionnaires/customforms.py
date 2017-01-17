from django import forms
from .models import Questionnaire

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


############################
class BABYForm1(forms.Form):
    """
    Custom form for Baby Measurements: BABY1
    """
    measurement_date = forms.DateField(label="Date")
    measurement_head = forms.IntegerField(label="Head")
    measurement_length = forms.IntegerField(label="Body length")
    measurement_weight = forms.IntegerField(label="Body weight")
    count = forms.IntegerField(required=False, widget = forms.HiddenInput())
    qtitle = 'Baby Measurements'


    def __init__(self, *args, **kwargs):
        code = 'BABY1'
        print("debug: form code=", code)
        super(BABYForm1, self).__init__(*args, **kwargs)
        qs = Questionnaire.objects.get(code=code)
        print("DEBUG: qs=", qs.title)
        self.qtitle = qs.title

    class Meta:
        fields =('measurement_date','measurement_head','measurement_length','measurement_weight','count')
