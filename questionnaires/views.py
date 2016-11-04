import os
from collections import OrderedDict
from datetime import datetime

from axes.utils import reset
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import password_change
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse_lazy, reverse
from django.db import IntegrityError
from django.db.models import Count
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render,redirect, resolve_url, render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView
from django.template import loader, Context
from django_tables2_reports.config import RequestConfigReport as RequestConfig
from django_tables2_reports.views import ReportTableView
from django_tables2_reports import utils as reportutils
from formtools.wizard.views import SessionWizardView
from ipware.ip import get_ip

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse # python3 support
# import the logging library
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
###Local classes
from .models import Questionnaire, Question, Choice, TestResult, SubjectQuestionnaire,Category,SubjectVisit,Demographic
from .forms import AxesCaptchaForm, AnswerForm,DemographicForm, TestResultDeleteForm
from .tables import FilteredSingleTableView, TestResultTable,SubjectQuestionnaireTable,SubjectVisitTable
from .filters import TestResultFilter,SubjectQuestionnaireFilter,SubjectVisitFilter


## Login
class LoginView(FormView):
    """
    Provides the ability to login as a user with a username and password
    """
    template_name = 'questionnaires/index.html'
    success_url = '/questionnaires'
    form_class = AuthenticationForm
    redirect_field_name = REDIRECT_FIELD_NAME

    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        # Sets a test cookie to make sure the user has cookies enabled
        request.session.set_test_cookie()

        return super(LoginView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if user is not None:
            msg = 'User: %s' % user
            if user.is_active:
                login(self.request, user)
                msg = '% has logged in' % msg
                logger.info(msg)
            else:
                # Return a 'disabled account' error message
                form.add_error = 'Your account has been disabled. Please contact admin.'
                msg = '% has disabled account' % msg
                logger.warning(msg)

        else:
            # Return an 'invalid login' error message.
            form.add_error = 'Login credentials are invalid. Please try again'
            msg = 'Login failed with invalid credentials'
            logger.error(msg)

        # If the test cookie worked, go ahead and
        # delete it since its no longer needed
        self.check_and_delete_test_cookie()
        return super(LoginView, self).form_valid(form)

    def form_invalid(self, form):
        """
        The user has provided invalid credentials (this was checked in AuthenticationForm.is_valid()). So now we
        set the test cookie again and re-render the form with errors.
        """
        self.set_test_cookie()
        return super(LoginView, self).form_invalid(form)

    def set_test_cookie(self):
        self.request.session.set_test_cookie()

    def check_and_delete_test_cookie(self):
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
            return True
        return False

    def get_success_url(self):
        if self.success_url:
            redirect_to = self.success_url
        else:
            redirect_to = self.request.POST.get(
                self.redirect_field_name,
                self.request.GET.get(self.redirect_field_name, ''))

        netloc = urlparse.urlparse(redirect_to)[1]
        if not redirect_to:
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        # Security check -- don't allow redirection to a different host.
        elif netloc and netloc != self.request.get_host():
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        return redirect_to
        #return reverse(redirect_to)


class LogoutView(RedirectView):
    """
    Provides users the ability to logout
    """
    #template_name = 'questionnaires/index.html'
    successurl = '/questionnaires'

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(self.successurl)

def locked_out(request):
    if request.POST:
        form = AxesCaptchaForm(request.POST)
        if form.is_valid():
            ip = get_ip(request)
            if ip is not None:
                msg = "User locked out with IP address=%s" % ip
                logger.warning(msg)
                reset(ip=ip)

            return HttpResponseRedirect(reverse_lazy('questionnaires:index'))
    else:
        form = AxesCaptchaForm()

    return render(request,'questionnaires/locked.html', dict(form=form))
    #deprecated return render_to_response('questionnaires/locked.html', dict(form=form), context=RequestContext(request))

def change_password(request):
    template_response = password_change(request)
    # Do something with `template_response`
    return template_response

def csrf_failure(request, reason=""):
    ctx = {'title': 'CSRF Failure', 'message': 'Your browser does not accept cookies and this can be a problem in ensuring a secure connection.'}
    template_name= 'admin/csrf_failure.html'
    return render_to_response(template_name, ctx)
###########################################################################################

class IndexView(generic.ListView):
    template_name = 'questionnaires/index.html'
    context_object_name = 'questionnaire_list'
    raise_exception = True

    def get_queryset(self):
        return Questionnaire.objects.order_by('code')

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        user = self.request.user
        rlist = []
        qlist = {}
        cat1 = None
        if user is not None and user.is_active:
            # set defaults
            cat1 = Category.objects.get(name='Wave 1')  # Wave 1
            catlist = [c for c in Category.objects.filter(name__icontains='all')]  # include ALL
            qlist = self.get_queryset()
            #user_results = user.subjectquestionnaire_set.all() #SubjectQuestionnaire.objects.filter(subject=user)
            rlist = user.subjectquestionnaire_set.all()

            if not user.is_superuser:
                visit = SubjectVisit.objects.filter(subject=user)
                #If missing, create visit and set to first category
                if len(visit)==0:
                    visit = SubjectVisit(subject=user, category=cat1, date_visit=datetime.now())
                    visit.save()
                else:
                    visit = visit[0]
                cat1 = visit.category
                catlist.append(cat1)
                usergrouplist = user.groups.values_list('name')

                rlist = rlist.filter(questionnaire__category__in=catlist).distinct('questionnaire')
                qlist = qlist.filter(active=True).filter(category__in=catlist).filter(group__name__in=usergrouplist)
            #exclude completed
            for r in rlist:
                qlist = qlist.exclude(pk=r.questionnaire.id)

        context['questionnaire_list'] = qlist
        context['result_list']= rlist
        context['visit'] = cat1

        return context


# Questionnaire Intro page
class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Questionnaire
    template_name = 'questionnaires/intro.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

################REPORT TABLES ##########################################
##Reports
class SubjectReportView(LoginRequiredMixin, FilteredSingleTableView):
    template_name = 'questionnaires/results_summary.html'
    model = SubjectQuestionnaire
    table_class = SubjectQuestionnaireTable
    filter_class = SubjectQuestionnaireFilter
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(SubjectReportView, self).get_context_data(**kwargs)
        context['title'] = "Subject Reports"
        return context


##Results
class ResultFilterView(LoginRequiredMixin, FilteredSingleTableView):
    template_name = 'questionnaires/results_summary.html'
    model = TestResult
    table_class = TestResultTable
    filter_class = TestResultFilter
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(ResultFilterView, self).get_context_data(**kwargs)
        context['title'] = "Questionnaire Results"
        return context

##Visits
class VisitView(LoginRequiredMixin, FilteredSingleTableView):
    template_name = 'questionnaires/results_summary.html'
    model = SubjectVisit
    table_class = SubjectVisitTable
    filter_class = SubjectVisitFilter
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super(VisitView, self).get_context_data(**kwargs)
        context['title'] = "Subject Visits"
        return context

## ACTIONS ##

def download_report(request, *args, **kwargs):
    filename="qtab_report.csv"
    # Get subject id
    sid = kwargs.get('subjectid')
    #if (sid):
    qs = SubjectQuestionnaire.objects.get(pk=sid)
    filename = "qtab_report_%s.csv" % sid
    # Create the HttpResponse object with the appropriate CSV header.
    import csv
    from django.utils.encoding import smart_str
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response.write(u'\ufeff'.encode('utf8'))  # BOM (optional...Excel needs it to open UTF-8 file properly)
    writer = csv.writer(response, csv.excel)
    writer.writerow([
        smart_str(u"ID"),
        smart_str(u"Date"),
        smart_str(u"Questionnaire"),
        smart_str(u"Code"),
        smart_str(u"Description"),
        smart_str(u"Visit"),
        smart_str(u"Total Qns"),
    ])

    if hasattr(qs.subject, 'subjectvisit'):
        id = qs.subject.subjectvisit.xnatid
        visit = qs.subject.subjectvisit.category.name
    else:
        id = qs.subject
        visit = "Unknown"
    writer.writerow([
        smart_str(id),
        smart_str(qs.date_stored),
        smart_str(qs.questionnaire.title),
        smart_str(qs.questionnaire.code),
        smart_str(qs.questionnaire.description),
        smart_str(visit),
        smart_str(qs.questionnaire.question_set.count()),
    ])
    #Output question results
    writer.writerow([smart_str(u"**Results**")])
    writer.writerow([
            smart_str(u"Question"),
            smart_str(u"Options"),
            smart_str(u"Option values"),
            smart_str(u"Choice"),
            smart_str(u"Value"),
            smart_str(u"Text"),
     ])
    testresults = TestResult.objects.filter(test_token=qs.session_token)
    for qresult in testresults:
        #check testee == user
        choicetext = ""
        choicevalue = ""
        freetext = ""
        if qresult.testee == qs.subject:
            choices = ""
            choicetexts = ""
            choicevalues = ""
            if qresult.test_result_choice:
                choices = qresult.test_result_question.choice_set.all()
                choicetexts = [choice.choice_text for choice in choices]
                choicevalues = [choice.choice_value for choice in choices]
                choicetext = qresult.test_result_choice.choice_text
                choicevalue = qresult.test_result_choice.choice_value
            elif qresult.test_result_text:
                freetext = qresult.test_result_text

            writer.writerow([
                smart_str(qresult.test_result_question.question_text),
                smart_str(choicetexts),
                smart_str(choicevalues),
                smart_str(choicetext),
                smart_str(choicevalue),
                smart_str(freetext),
            ])
    return response



class ResultsView(LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView):
    template_name = 'questionnaires/results.html'
    raise_exception = True
    permission_required = 'questionnaires.choice.can_add_choice'

    def get_queryset(self, **kwargs):
        qchoices = Choice.objects.annotate(choice_count=Count('testresult'))

        return qchoices.order_by('question')

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        table = self.get_queryset() #ResultsReportTable(self.get_queryset())
        #RequestConfig(self.request).configure(table)
        context['results_table'] = table

        return context


class TestResultDelete(LoginRequiredMixin, PermissionRequiredMixin, generic.FormView):
    """Delete a result set"""
    template_name = 'questionnaires/confirm_delete.html'
    form_class=TestResultDeleteForm
    raise_exception = True
    permission_required = 'questionnaires.delete_testresult'

    def post(self, request, *args, **kwargs):
        mylist = self.get_queryset()
        token = mylist[0].test_token
        sc = SubjectQuestionnaire.objects.get(session_token = token)
        try:
            r = mylist.delete()
            sc.delete()
            message = 'Successfully deleted questionnaire with ' + str(r[0]) + ' questions'
        except IntegrityError:
            message = 'Unable to delete - please refer to db administrator'
            #transaction.rollback()
            #print('DELETED: ', message, ' r=', r)
            message = message + ' ' + token
        logger.info(message)
        return render(request, self.template_name, {'msg': message})

    def get_context_data(self, **kwargs):
        context = super(TestResultDelete, self).get_context_data(**kwargs)
        resultlist = self.get_queryset()
        if resultlist.count() > 0:
            context.update({
                'qnaire': resultlist[0].test_questionnaire,
                'subject' : resultlist[0].testee,
                'date': resultlist[0].test_datetime
            })
        else:
            context['msg'] = 'There are NO results to delete'
        return context

    def get_queryset(self):
        fid = self.kwargs.get('token')
        sc = SubjectQuestionnaire.objects.get(pk=fid)
        return TestResult.objects.filter(test_token=sc.session_token)

    def get_success_url(self):
        return reverse('questionnaires:reports')




################QUESTIONNAIRE FORMS ###################################
@login_required
def load_questionnaire(request, *args, **kwargs):
    """ Prepare questionnaire wizard with required questions """
    raise_exception = True
    print("DEBUG: load_q request=", request)
    qid = kwargs.get('pk')
    if qid is not None:
        qnaire = Questionnaire.objects.get(pk=qid)
        if qnaire.type =='single':
            print('DEBUG: single PAGE questionnaire')
            #return singlepage_questionnaire(request, *args, **kwargs)
        elif qnaire.type =='custom':
            customurl = 'questionnaires:%s' % qnaire.code
            return HttpResponseRedirect(reverse(customurl))

        formlist=[AnswerForm] * qnaire.question_set.count()
        questions = qnaire.question_set.order_by('order')
        linkdata = {}
        condata = {}
        for q in questions:
            linkdata[str(q.order-1)] = {'qid': q}
            if q.skip_value:
                condata[str(q.order-1)] = {'val': q.skip_value}

        initdata = OrderedDict(linkdata)
        cond_data = OrderedDict(condata)
        print("DEBUG: Cond data=", cond_data)

    form = QuestionnaireWizard.as_view(form_list=formlist, initial_dict=initdata, condition_dict =cond_data)
    return form(context=RequestContext(request), request=request)

class QuestionnaireWizard(LoginRequiredMixin, SessionWizardView):
    template_name = 'questionnaires/qpage.html'
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photos'))

    def dispatch(self, request, *args, **kwargs):
    #     self.sheet_id_initial = kwargs.get('sheet_id_initial', None)
        return super(QuestionnaireWizard, self).dispatch(request, *args, **kwargs)

    # def process_step(self, form):
    #     rtn = True
    #     print("Process step: list=", self.form_list)
    #     currentstep = str(self.get_step_index())
    #     fdata = self.get_form_step_data(form)
    #     print("Process step: fdata=",fdata)
    #     qn = "%s-question" % currentstep
    #     if (fdata[qn]):
    #         print("Process step: ", qn," form value=", fdata[qn])
    #         if (self.condition_dict.get(currentstep)):
    #             qn_val = self.condition_dict.get(currentstep)['val']
    #             print("Process step: value=", qn_val)
    #             if fdata[qn] != qn_val:
    #                 print("DEBUG: conditional val: ", qn_val, " form value=", fdata[qn])
    #                 next = int(self.steps.next)
    #                 self.form_list.pop(next)
    #     return self.get_form_step_data(form)

    def get_form_initial(self, step):
        initial = self.initial_dict.get(step)
        initial.update({'myuser': self.request.user})
        return initial

    # In addition to form_list, the done() method is passed a form_dict, which allows you to access the wizard’s forms based on their step names.
    def done(self, form_list, form_dict, **kwargs):

        # Find question and questionnaire
        qn = self.initial_dict.get('0')['qid']
        qnaire = qn.qid

        for key in form_dict:
            qn = self.initial_dict.get(key)['qid']
            #Get response
            response = list(form_list)[int(key)].cleaned_data
            choiceidx = response['question']
            qntype = qn.question_type
            if qntype == 3:
                # Not choice but free text
                answers = [choiceidx]
            elif qntype == 2:
                answers = qn.choice_set.filter(choice_value__in=choiceidx)
            else:
                answers = qn.choice_set.filter(choice_value=choiceidx)
            # Load save for each choice
            for answer in answers:
                tresult = TestResult()
                tresult.testee = self.request.user
                tresult.test_questionnaire = qnaire
                tresult.test_result_question = qn
                if qntype == 3:
                    tresult.test_result_text = answer
                else:
                    tresult.test_result_choice = answer

                tresult.test_token = self.request.POST['csrfmiddlewaretoken']
                tresult.save()

                print('DEBUG: TESTRESULT:', " Qnaire:", tresult.test_questionnaire.title,
                      " Qn:", tresult.test_result_question.question_text)
                if qntype == 3:
                    print(" ValText:", tresult.test_result_text)
                else:
                    print(" ValChoice:", tresult.test_result_choice.choice_text)
        # Store category for user
        subjectcat = SubjectQuestionnaire(subject=self.request.user, questionnaire=qnaire,
                                     session_token=self.request.POST['csrfmiddlewaretoken'])
        subjectcat.save()
        return render(self.request, 'questionnaires/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'qnaire_title' : qnaire.title,
        })


###################################
# ############# SINGLE PAGE ##################

# def singlepage_questionnaire(request,*args,**kwargs):
#     template = 'questionnaires/single.html'
#     """
#     Detect user
#     """
#     user = request.user
#     messages = ''
#     #Questionnaire ID
#     qid = kwargs.get('pk')
#     qnaire = Questionnaire.objects.get(pk=qid)
#
#     # Create the formset, specifying the form and formset we want to use.
#     LinkFormSet = formset_factory(AnswerForm, formset=BaseQuestionFormSet, validate_max=True)
#     # Get our existing link data for this user.  This is used as initial data.
#     questions = qnaire.question_set.order_by('order') #Question.objects.order_by('order')
#     link_data = [{'qid': q.id} for q in questions]
#
#     if request.method == 'POST':
#         link_formset = LinkFormSet(request.POST) #cannot reload as dynamic
#
#         if link_formset.is_valid():
#             # Now save the data for each form in the formset
#             new_data = []
#             for i in range(0, len(link_data)):
#                 formid = 'form-%d-question' % i
#                 val = request.POST[formid]  # TODO Validate data input
#                 tresult = TestResult()
#                 tresult.testee = user
#                 tresult.test_questionnaire = qnaire
#                 qn = Question.objects.get(pk=link_data[i]['qid'])
#                 tresult.test_result_question = qn
#                 q1 = qn.choice_set.filter(choice_value=val)[0]
#                 # print(q1)
#                 tresult.test_result_choice = q1
#                 tresult.test_token = request.POST['csrfmiddlewaretoken']
#                 tresult.save()
#                 print('SINGLEPAGE: TESTRESULT:', " Qnaire:", tresult.test_questionnaire.title,
#                       " Qn:", tresult.test_result_question.question_text,
#                       " Val:", tresult.test_result_choice.choice_text)
#
#             # Save user info with category
#             template='questionnaires/done.html'
#             try:
#                 subjectcat = SubjectQuestionnaire(subject=user, questionnaire=qnaire, session_token=request.POST['csrfmiddlewaretoken'])
#                 subjectcat.save()
#                 messages='Congratulations, %s!  You have completed the questionnaire.' % user
#             except IntegrityError:
#                 messages.error(request, 'There was an error saving your result.')
#
#
#     else:
#         link_formset = LinkFormSet(initial=link_data)
#
#     context = {
#         'formset': link_formset,
#         'qtitle' : qnaire.title,
#         'messages': messages,
#     }
#
#     return render(request, template, context)

#################CUSTOM QUESTIONNAIRES - HARD-CODED ###############
def show_message_form_condition(wizard):
    # try to get the cleaned data of step 1
    cleaned_data = wizard.get_cleaned_data_for_step('0') or {}
    # check if the field ``leave_message`` was checked.
    return cleaned_data.get('leave_message', True)

class ContactWizard(SessionWizardView):
    template = 'questionnaires/test.html'

    def done(self, form_list, **kwargs):
        return render(self.request, 'questionnaires/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
        })

class DemographicDetail(LoginRequiredMixin, generic.DetailView):
    model = Demographic
    context_object_name = 'obj'
    template_name = 'questionnaires/detail.html'
    raise_exception = True

class DemographicCreate(LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView):
    model = Demographic
    template_name = 'questionnaires/create.html'
    form_class = DemographicForm
    raise_exception = True
    permission_required = 'questionnaires.add_demographic'

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(DemographicCreate, self).get_initial()
        # Copy the dictionary so we don't accidentally change a mutable dict
        initial = initial.copy()
        initial['subject'] = self.request.user.pk
        if self.request.user.groups.filter(name='Parent').exists():
            initial['subjecttype'] = 1
        elif self.request.user.groups.filter(name='Teenager').exists():
            initial['subjecttype'] = 2
        if self.request.user.groups.filter(name='Female').exists():
            initial['gender'] = 2
        elif self.request.user.groups.filter(name='Male').exists():
            initial['gender'] = 1
        print("DEBUG: initial form=", initial)
        return initial

    def form_valid(self, form):
        try:
            return super(DemographicCreate, self).form_valid(form)
        except IntegrityError as e:
            msg = 'Database Error: Unable to create Demographic data - see Administrator'
            form.add_error(msg)
            logger.warning(msg)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('questionnaires:demographic_detail', args=[self.object.id])

class DemographicUpdate(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Demographic
    form_class = DemographicForm
    template_name = 'questionnaires/create.html'
    raise_exception = True
    permission_required = 'questionnaires.change_demographic'

    def get_success_url(self):
        return reverse('questionnaires:demographic_detail', args=[self.object.id])

