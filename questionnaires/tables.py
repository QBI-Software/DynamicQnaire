import django_tables2 as tables
import os
from django_tables2.utils import A, AttributeDict
from django.utils.html import format_html, escape
from datetime import date

from .models import TestResult,Questionnaire

class SummingColumn(tables.Column):
    def render_footer(self, bound_column, table):
        return sum(bound_column.accessor.resolve(row) for row in table.data)

class ResultsReportTable(tables.Table):
    qnaire = tables.LinkColumn('questionnaires:q', accessor=A('title'),  args=[A('pk')], verbose_name='Questionnaire')
    total = tables.Column(verbose_name="Total")


    class Meta:
        model = Questionnaire
        attrs = {"class": "ui-responsive table table-hover"}
        fields =['qnaire','title','total']
        sortable = True

