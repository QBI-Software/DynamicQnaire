from django import forms

########## Custom Forms ######################
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

            question = qid.get('qid')
            choices = qid.get('nameslist')
            # Overwrite with choices in admin UI
            if question.choice_set.count() > 1:
                choices = []
                for c in question.choice_set.all():
                    choices.append((c.choice_value, c))
            if question.question_type == 2:
                self.fields['question'] = forms.MultipleChoiceField(
                    label=question.question_text,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
                    help_text='checkbox',
                    required=question.question_required,
                    choices=choices,
                )
            elif question.question_type == 1:
                self.fields['question'] = forms.ChoiceField(
                    label=question.question_text,
                    help_text='radio',  # use this to detect type
                    widget=forms.RadioSelect(attrs={'class': 'form-control'}),
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

    class Meta:
        fields = ('question')


############################
class BABYForm1(forms.Form):
    """
    Custom form for Baby Measurements: BABY1
    """
    CHOICES =((0,'Baby book'),(1,'Reports from Health professional'),(2,'Other'))
    measurement_age = forms.FloatField(label="Head", widget=forms.NumberInput(attrs={'class': 'form-control'}))

    measurement_head = forms.FloatField(label="Head circumference",
                                        widget=forms.NumberInput(attrs={'class': 'form-control'}))

    measurement_length = forms.FloatField(label="Body length",
                                          widget=forms.NumberInput(attrs={'class': 'form-control'}))

    measurement_weight = forms.FloatField(label="Body weight",
                                          widget=forms.NumberInput(attrs={'class': 'form-control'}))
    measurement_source = forms.ChoiceField(
                        label="Source",
                        widget=forms.Select(attrs={'class': 'form-control'}),
                        help_text='Where were these measurements gathered from?',
                        required=True,
                        choices=CHOICES,
    )
    measurement_source_other = forms.CharField(
                        label="Other Source",
                        help_text='Other source not in the list',
                        widget=forms.TextInput(attrs={'class': 'form-control'}),
                        required=False,

                    )


    class Meta:
        fields = ('measurement_date', 'measurement_age', 'measurement_head', 'measurement_length', 'measurement_weight', 'measurement_source', 'measurement_source_other')


