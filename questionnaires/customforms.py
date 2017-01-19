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
