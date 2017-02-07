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



    class Meta:
        fields=['mainquestion', 'subquestion1', 'subquestion2']

###################################################
GENDERS = [(0, 'Unknown'), (1, 'Male'), (2, 'Female')]
class FamilyHistoryForm(forms.Form):
    type = forms.CharField(label="Type", required=True,
                              help_text="Person type",
                              widget=forms.HiddenInput())
    person = forms.CharField(label="First Name", required=True,
                              help_text="Enter their first name",
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(label="Gender", choices=GENDERS, required=True,
                             help_text="Select person's gender at birth",
                             widget=forms.Select(attrs={'class': 'form-control'}))
    age = forms.IntegerField(label="Current Age", required=True,
                            help_text="Enter person's current age or age at death",
                            widget=forms.NumberInput(attrs={'class': 'form-control'}))
    decd = forms.BooleanField(label="Person is deceased", required=False,
                            help_text="Check box if this person is deceased",
                            widget=forms.CheckboxInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_permitted = True

class FamilyChoiceForm(forms.Form):

    """Loads a question and multiple choice answer """
    def __init__(self, *args, **kwargs):
        qid = kwargs.get('initial')
        super().__init__(*args, **kwargs)
        if (qid):
            #TODO Populate Question with names options
            question = qid.get('qid')
            choices = qid.get('nameslist')
            if question.question_type == 2:
                self.fields['question'] = forms.MultipleChoiceField(
                    label=question.question_text,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
                    help_text='checkbox',
                    required=question.question_required,
                    choices=choices,
                )
            else:
                self.fields['question'] = forms.CharField(
                    label=question.question_text,
                    help_text='text',
                    widget=forms.TextInput(attrs={'class': 'form-control'}),
                    required=question.question_required,

                )

    class Meta:
        fields = ('question')

############################
class BABYForm1(forms.Form):
    """
    Custom form for Baby Measurements: BABY1
    """
    LENGTH_UNITS=[{0,'cm'},{1,'inches'}]
    WEIGHT_UNITS = [{0, 'g'}, {1, 'lb'}]
    measurement_date = forms.DateField(label="Date",widget=forms.DateInput(format=('%d-%m-%Y'),
                                        attrs={'class': 'form-control','type': 'date',
                                             'placeholder': 'Select a date'}
                                      ))
    measurement_age = forms.FloatField(label="Head", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    #measurement_age_units = forms.ChoiceField(label="Age units", choices=[{0, 'Days'}, {1, 'Weeks'},{2, 'Months'},{3, 'Years'}],
    #                                 widget=forms.Select(attrs={'class': 'form-control'}))
    measurement_head = forms.FloatField(label="Head circumference", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    #measurement_head_units = forms.ChoiceField(label="Head units",
    #                                          choices=LENGTH_UNITS,
    #                                          widget=forms.Select(attrs={'class': 'form-control'}))
    measurement_length = forms.FloatField(label="Body length", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    #measurement_length_units = forms.ChoiceField(label="Length/Height units",
    #                                           choices=LENGTH_UNITS,
    #                                           widget=forms.Select(attrs={'class': 'form-control'}))
    measurement_weight = forms.FloatField(label="Body weight",widget=forms.NumberInput(attrs={'class': 'form-control'}))
    #measurement_weight_units = forms.ChoiceField(label="Weight units",
    #                                           choices=WEIGHT_UNITS,
    #                                           widget=forms.Select(attrs={'class': 'form-control'}))


    class Meta:
        fields =('measurement_date','measurement_age','measurement_head','measurement_length','measurement_weight')
