from django.conf.urls import url
from django import forms

from .forms import QuestionnaireForm
from .preview import QuestionnaireFormPreview
from .forms import ContactForm1, ContactForm2, MultipageQuestionForm
from .views import ContactWizard


from . import views
app_name = 'questionnaires'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
    url(r'^(?P<pk>[0-9]+)/q/$', views.test_questionnaire, name='q'),
    #url(r'^post/$', QuestionnaireFormPreview(QuestionnaireForm)),
    url(r'^contact/$', ContactWizard.as_view([ContactForm1, ContactForm2])),
]