from django.conf.urls import url
from django import forms

from .views import QuestionnaireWizard
from django.contrib.auth.views import password_change,password_change_done,password_reset,password_reset_complete, password_reset_confirm, password_reset_done
from axes.decorators import watch_login


from . import views
app_name = 'questionnaires'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^login/$', watch_login(views.LoginView.as_view()), name='loginform'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    url(r'^locked/$', views.locked_out, name='locked_out'),
    url('^password_change/$', password_change, {'template_name': 'admin/password_change_form.html', 'post_change_redirect': 'questionnaires:index'}, name='password_change'),
    url('^password_reset/$', password_reset, {'post_reset_redirect': 'questionnaires:index'},name='password_reset'),
    url('^password_reset/done/$', password_reset_done, name='password_reset_done'),
    url('^reset/(?P<uidb64>[0-9A-Za-z\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, {'template_name':'admin/password_reset_email.html'}, name='password_reset_confirm'),
    url('^reset/done/$', password_reset_complete, {'template_name':'admin/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    #url(r'^(?P<pk>[0-9]+)/results/$', views.ResultsView.as_view(), name='results'),
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
    #url(r'^(?P<pk>[0-9]+)/q/$', views.test_questionnaire, name='q'),
    url(r'^(?P<pk>[0-9]+)/q/$', views.load_questionnaire, name='q'),
    #url(r'^post/$', QuestionnaireFormPreview(QuestionnaireForm)),
    #url(r'^contact/$', ContactWizard.as_view([ContactForm1, ContactForm2])),
]