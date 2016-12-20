import django_tables2 as tables
from django.utils.html import format_html
from django_tables2.utils import A

from .models import *
from .forms import replaceTwinNames


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
    download = tables.LinkColumn('questionnaires:download', accessor=A('pk'), args=[A('pk')], verbose_name='Download')
    date_stored = tables.Column(verbose_name="Date")
    questionnaire = tables.Column(verbose_name="Questionnaire")
    subject = tables.Column(verbose_name="Subject")

    def render_download(self,value):
        return format_html('<a href="/{}/download"><span class="glyphicon glyphicon-download"></span></a>', value)

    def render_total(self,value):
        sc = SubjectQuestionnaire.objects.get(session_token=value)
        return format_html('<a href="/{}/deleteresults"><span class="glyphicon glyphicon-remove"></span></a>', sc.pk)

    class Meta:
        model = SubjectQuestionnaire
        attrs = {"class": "ui-responsive table table-hover"}
        fields =['date_stored','questionnaire','subject','total','download']
        sortable = True


class TestResultTable(tables.Table):
    testee = tables.Column(verbose_name="Subject")
    test_datetime = tables.Column(verbose_name="Timestamp")
    twin_choice = tables.Column(verbose_name="Twin Response", accessor=A('pk'))
    parent1_choice = tables.Column(verbose_name="Parent 1 Response", accessor=A('pk'))
    parent2_choice = tables.Column(verbose_name="Parent 2 Response", accessor=A('pk'))
    test_result_question = tables.Column(verbose_name="Question", accessor=A('pk'))

    def getchoices(self, twinresults):
        choice = []
        for t in twinresults:
            if t.test_result_choice:
                choice.append(t.test_result_choice.choice_text)
            elif t.test_result_text:
                choice.append(t.test_result_text)
        return choice

    def render_twin_choice(self,value):
        choice = "-"
        result = TestResult.objects.get(pk=value)
        subject = result.testee
        if (hasattr(subject,'subjectvisit') and subject.subjectvisit.twin):
            twin = subject.subjectvisit.twin
            twinresults = TestResult.objects.filter(test_result_question=result.test_result_question).filter(testee=twin)
            choice = self.getchoices(twinresults)
        return choice

    def render_parent1_choice(self,value):
        choice = "-"
        result = TestResult.objects.get(pk=value)
        subject = result.testee
        if (hasattr(subject,'subjectvisit') and subject.subjectvisit.parent1):
            parent = subject.subjectvisit.parent1
            twinresults = TestResult.objects.filter(test_result_question=result.test_result_question).filter(testee=parent)
            choice = self.getchoices(twinresults)

        return choice

    def render_parent2_choice(self,value):
        choice = "-"
        result = TestResult.objects.get(pk=value)
        subject = result.testee
        if (hasattr(subject,'subjectvisit') and subject.subjectvisit.parent2):
            parent = subject.subjectvisit.parent2
            twinresults = TestResult.objects.filter(test_result_question=result.test_result_question).filter(testee=parent)
            choice = self.getchoices(twinresults)
        return choice

    def render_test_result_question(self,value):
        result = TestResult.objects.get(pk=value)
        qtext = replaceTwinNames(result.testee, result.test_result_question.question_text)

        return qtext



    class Meta:
        model = TestResult
        attrs = {"class": "ui-responsive table table-condensed"}
        fields =['test_datetime','testee','test_questionnaire','test_result_question','test_result_choice','test_result_text', 'test_result_date',
                 'twin_choice','parent1_choice','parent2_choice']
        sortable = True


class SubjectVisitTable(tables.Table):
    date_visit = tables.DateColumn(verbose_name='Visit date', format='d-M-Y')
    total = tables.Column(verbose_name="Total Q's", accessor=A('pk'))
    done = tables.Column(verbose_name="Completed", accessor=A('pk'))

    def render_total(self,value):
        visit = SubjectVisit.objects.get(pk=value)
        cat = visit.category
        usergrouplist = visit.subject.groups.all()
        qlist = Questionnaire.objects.filter(active=True).filter(category=cat).filter(group__in=usergrouplist)
        return qlist.count()

    def render_done(self, value):
        visit = SubjectVisit.objects.get(pk=value)
        cat = visit.category
        return visit.subject.subjectquestionnaire_set.filter(questionnaire__category=cat).count()


    class Meta:
        model = SubjectVisit
        fields=['subject','date_visit','category','xnatid', 'total','done']
        attrs = {"class": "ui-responsive table table-condensed"}
        sortable = True
        order_by_field = '-date_visit'
