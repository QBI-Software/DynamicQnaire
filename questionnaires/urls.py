from axes.decorators import watch_login
from django.conf.urls import url
from django.contrib.auth.views import password_change, password_reset,password_reset_complete, password_reset_confirm, password_reset_done
#from .forms import ContactForm1, ContactForm2
from .views import ContactWizard, show_message_form_condition, BABYWizard
from . import views


#contact_forms = [ContactForm1, ContactForm2]

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
    url(r'^results/$', views.ResultFilterView.as_view(), name='results'),
    url(r'^reports/$', views.SubjectReportView.as_view(), name='reports'),
    url(r'^visits/$', views.VisitView.as_view(), name='visits'),
    url(r'^(?P<subjectid>[0-9]+)/download/$', views.download_report, name='download'),
    url(r'^(?P<pk>[0-9]+)/qintro/$', views.DetailView.as_view(), name='qintro'),
    url(r'^(?P<pk>[0-9]+)/q/$', views.load_questionnaire, name='q'),
    url(r'^(?P<token>[0-9]+)/deleteresults/$', views.TestResultDelete.as_view(), name='deleteresults'),
    url(r'^custom/BABY1/$', BABYWizard.as_view(), name='BABY1'),
    #url(r'^custom/(?P<code>\w+)/$', CustomWizard.as_view(),name='custom'),
    #url(r'^contact/$', ContactWizard.as_view(contact_forms,  condition_dict={'1': show_message_form_condition} ),name='contact'),

]