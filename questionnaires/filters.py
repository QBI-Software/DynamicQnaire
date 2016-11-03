import django_filters
from django.contrib.auth.models import User
from .models import TestResult,SubjectQuestionnaire,SubjectVisit

class TestResultFilter(django_filters.FilterSet):
    test_datetime = django_filters.DateFromToRangeFilter(label="Test Date (from-to)",
                                                         widget=django_filters.widgets.RangeWidget(
                                                             attrs={'class': 'myDateClass', 'type': 'date',
                                                                    'placeholder': 'Select a date'}), )

    class Meta:
        model = TestResult
        fields = ['testee', 'test_questionnaire','test_datetime']
        #order_by =['test_questionnaire']

    def __init__(self, *args, **kwargs):
        super(TestResultFilter, self).__init__(*args, **kwargs)
        self.filters['testee'].label='Subject'



class SubjectQuestionnaireFilter(django_filters.FilterSet):
    date_stored = django_filters.DateFromToRangeFilter(label="Test Date (from-to)",
                                                         widget=django_filters.widgets.RangeWidget(
                                                             attrs={'class': 'myDateClass', 'type': 'date',
                                                                    'placeholder': 'Select a date'}), )

    class Meta:
        model = SubjectQuestionnaire
        fields = ['date_stored','subject', 'questionnaire']


class SubjectVisitFilter(django_filters.FilterSet):
    date_visit = django_filters.DateFromToRangeFilter(label="Visit Date (from-to)",
                                                         widget=django_filters.widgets.RangeWidget(
                                                             attrs={'class': 'myDateClass', 'type': 'date',
                                                                    'placeholder': 'Select a date'}), )

    class Meta:
        model = SubjectVisit
        fields = ['date_visit','subject', 'category','xnatid']