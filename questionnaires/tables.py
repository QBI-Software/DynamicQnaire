import django_tables2 as tables
from django_tables2.utils import A
from django.utils.html import format_html
from .models import *


#Generic filtered table
class FilteredSingleTableView(tables.SingleTableView):
    filter_class = None

    def get_table_data(self):
        data = super(FilteredSingleTableView, self).get_table_data()
        self.filter = self.filter_class(self.request.GET, queryset=data)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(FilteredSingleTableView, self).get_context_data(**kwargs)
        context['filter'] = self.filter
        return context

class SummingColumn(tables.Column):
    def render_footer(self, bound_column, table):
        return sum(bound_column.accessor.resolve(row) for row in table.data)


class SubjectQuestionnaireTable(tables.Table):
    total = tables.LinkColumn('questionnaires:deleteresults', accessor=A('session_token'),  args=[A('session_token')], verbose_name='Delete')
    date_stored = tables.Column(verbose_name="Date")
    questionnaire = tables.Column(verbose_name="Questionnaire")
    subject = tables.Column(verbose_name="Subject")

    def render_total(self,value):
        print('DEBUG: render_total=',value)
        sc = SubjectQuestionnaire.objects.get(session_token=value)
        return format_html('<a href="/{}/deleteresults"><span class="glyphicon glyphicon-remove"></span></a>', sc.pk)

    class Meta:
        model = SubjectQuestionnaire
        attrs = {"class": "ui-responsive table table-hover"}
        fields =['date_stored','questionnaire','subject','total']
        sortable = True


class TestResultTable(tables.Table):
    testee = tables.Column(verbose_name="Subject")
    test_datetime = tables.Column(verbose_name="Timestamp")


    class Meta:
        model = TestResult
        attrs = {"class": "ui-responsive table table-hover"}
        fields =['test_datetime','testee','test_questionnaire','test_result_question','test_result_choice']
        sortable = True

