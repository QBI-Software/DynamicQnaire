from axes.decorators import watch_login
from django.conf.urls import url
from django.contrib.auth.views import password_change, password_reset,password_reset_complete, password_reset_confirm, password_reset_done

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
    url(r'^results/$', views.TestResultFilterView.as_view(), name='results'),
    #url(r'^tests/$', views.TestResultFilterView.as_view(), name='tests'),
    url(r'^subjects/$', views.SubjectFilterView.as_view(), name='subjects'),
    url(r'^reports/$', views.SubjectReportView.as_view(), name='reports'),
    url(r'^(?P<subjectid>[0-9]+)/download/$', views.download_report, name='download'),
    url(r'^(?P<pk>[0-9]+)/qintro/$', views.DetailView.as_view(), name='qintro'),
    url(r'^(?P<pk>[0-9]+)/q/$', views.load_questionnaire, name='q'),
    url(r'^(?P<token>[0-9]+)/deleteresults/$', views.TestResultBulkDelete.as_view(), name='deleteresults'),
]