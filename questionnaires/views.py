import os
import operator
from collections import OrderedDict
import datetime as dt
from datetime import datetime
import time

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
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render,redirect, resolve_url, render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, RedirectView
from formtools.wizard.views import SessionWizardView
from ipware.ip import get_ip
from django.contrib.auth.models import User
from django.utils import six

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
from .models import Questionnaire, Choice, TestResult, SubjectQuestionnaire,Category,SubjectVisit,Question
from .forms import AxesCaptchaForm, AnswerForm, TestResultDeleteForm, BaseQuestionFormSet, replaceTwinNames
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
        return Questionnaire.objects.order_by('order').order_by('code')

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
            qlist = self.get_queryset().distinct('code')
            #user_results = user.subjectquestionnaire_set.all() #SubjectQuestionnaire.objects.filter(subject=user)
            rlist = user.subjectquestionnaire_set.distinct('questionnaire')

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

                rlist = rlist.filter(questionnaire__category__in=catlist)
                qlist = qlist.filter(active=True).filter(category__in=catlist).filter(group__name__in=usergrouplist)
            #exclude completed
            for r in rlist:
                qlist = qlist.exclude(pk=r.questionnaire.id)
        #Reorder list by 'order' to allow manual override
        qlist = sorted(qlist, key=operator.attrgetter('order'))
        rlist = sorted(rlist, key=operator.attrgetter('date_stored'), reverse=True)
        # Reset session conditional data
        if self.request.session.get('conditionals'):
            print("DEBUG: FORM_INITIAL: Reset conditionals")
            self.request.session['conditionals'] = {}


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

    # Get subject id
    sid = kwargs.get('subjectid')
    if (sid):
        qs = SubjectQuestionnaire.objects.get(pk=sid)
    else:
        raise Exception('E100: Download report cannot find id')
    filename = "QTAB_report_%s.csv" % sid
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
    id = qs.subject.pk
    visit = "NA"
    if hasattr(qs.subject, 'subjectvisit'):
        if qs.subject.subjectvisit.xnatid:
            id = qs.subject.subjectvisit.xnatid
        visit = qs.subject.subjectvisit.category.name

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
            smart_str(u"Tested"),
     ])
    testresults = TestResult.objects.filter(test_token=qs.session_token)
    for qresult in testresults:
        testee = qresult.testee
        choicetext = ""
        choicevalue = ""
        freetext = ""
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
        elif qresult.test_result_date:
            freetext = qresult.test_result_date
        qtext = replaceTwinNames(qresult.testee,qresult.test_result_question.question_text)
        writer.writerow([
            smart_str(qtext),
            smart_str(choicetexts),
            smart_str(choicevalues),
            smart_str(choicetext),
            smart_str(choicevalue),
            smart_str(freetext),
            smart_str(testee),
        ])
        #Output any custom data as table
        if qs.questionnaire.type =='custom':
            if qs.questionnaire.code == 'BABY1':
                t = eval(qresult.test_result_text)
                if type(t) is dict:
                    for r,val in t.items():
                        writer.writerow(val)

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
        try:
            sc = SubjectQuestionnaire.objects.get(pk=fid)
        except Exception as error:
            logger.error('Unable to delete test result: ' + repr(error))
        return TestResult.objects.filter(test_token=sc.session_token)

    def get_success_url(self):
        return reverse('questionnaires:reports')




################QUESTIONNAIRE FORMS ###################################

@login_required
def load_questionnaire(request, *args, **kwargs):
    """ Prepare questionnaire wizard with required questions
        Note: initial values are reloaded every step - so need process_step with session vars to maintain conditionals
    """
    raise_exception = True
    qid = kwargs.get('pk')
    if qid is not None:
        qnaire = Questionnaire.objects.get(pk=qid)

        usergrouplist = request.user.groups.all()
        questions = qnaire.question_set.filter(
            Q(group__isnull=True)|Q(group__in=usergrouplist)).order_by('order')

        #Set initial data
        linkdata = {}
        condata = {}
        conditional_actions = {0:True, 1: 'showif_1', 2: 'skipif_1', 3: 'skip2if_2', 4: 'showchecked'}
        #conditional_actions = {1: showif_previous_0, 2: showif_previous_0}
        #Setup empty forms
        if qnaire.type == 'single':
            return singlepage_questionnaire(request, qnaire, questions)
        elif qnaire.type =='custom':
            code = qnaire.code.replace('-','')
            customurl = 'questionnaires:%s' % code
            return HttpResponseRedirect(reverse(customurl, kwargs={'code': qnaire.code}))
        else:
            num = 0
            for q in questions:
                linkdata[str(num)] = {'qid': q}
                if q.conditional:
                    condata[str(num)] = conditional_actions[q.conditional]
                num += 1
            formlist = [AnswerForm] * questions.count()
            initdata = OrderedDict(linkdata)
            #print("DEBUG: Initial Conditionals=", condata)
            form = QuestionnaireWizard.as_view(form_list=formlist, initial_dict=initdata, condition_dict =condata)
    return form(context=RequestContext(request), request=request)


class QuestionnaireWizard(LoginRequiredMixin, SessionWizardView):
    template_name = 'questionnaires/qpage.html'
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photos'))


    def dispatch(self, request, *args, **kwargs):
        return super(QuestionnaireWizard, self).dispatch(request, *args, **kwargs)

    def process_step(self, form):
        rtn = True
        currentstep = str(self.steps.current)
        nextstep = int(self.steps.current) + 1
        next2step = int(self.steps.current) + 2
        nextstep = str(nextstep)
        next2step = str(next2step)
        fdata = self.get_form_step_data(form)
        #print("DEBUG: Process step: fdata=", fdata)
        # Modify conditional dict - true/false: this is used when generating form_list
        condition = self.condition_dict.get(currentstep)
        #print("DEBUG: Process step: condition=", condition)
        if (condition is not None and not isinstance(condition,bool)):
            field = '%d-question' % int(currentstep)
            print("DEBUG: Process step: condition=", condition, " field=", field)
            check_val = condition.split('_')[-1]
            #print("DEBUG: Process step: form value=", fdata[field], " vs check=", check_val)
            if condition.split('_')[0]=='showif':
                self.condition_dict[nextstep] = (check_val == fdata[field])
            elif condition.split('_')[0]=='skipif':
                self.condition_dict[nextstep] = (check_val != fdata[field])
            elif condition.split('_')[0]=='skip2if':
                self.condition_dict[nextstep] = (check_val != fdata[field])
                self.condition_dict[next2step] = (check_val != fdata[field])
            elif condition.split('_')[0] == 'showchecked':
                # Questions must be ordered from zero to work - TODO: provide check?
                # Set every option to false then
                #print("DEBUG: Process step: options=",form.fields['question'].choices)
                choices = [k for k,v in form.fields['question'].choices]
                #print("DEBUG: Process step: keys=",choices)
                for k in choices:
                    self.condition_dict[k] = False
                #Get checked values from this step - set conditionals for matching forms
                #print("DEBUG: Process step: fdata=",fdata.getlist(field))
                for val in fdata.getlist(field):
                    #print("DEBUG: Process step: form value=",val )
                    self.condition_dict[val] = True

            #Update dict
            self.request.session['conditionals'] = self.condition_dict
            #print("DEBUG: PROCESS STEP: Conditionals=", self.condition_dict)
            #print("DEBUG: PROCESS STEP: Forms=", self.get_form_list())
        return self.get_form_step_data(form)

    def get_form_initial(self, step):
        initial = self.initial_dict.get(step)
        initial.update({'myuser': self.request.user})
        #Sesion conditionals - do not allow overwrite but need to detect new questionnaire
        #print("DEBUG: FORM_INITIAL: step=", step, " type=", type(step))
        if self.request.session.get('conditionals'):
            #print("DEBUG: FORM_INITIAL: Load conditionals from session")
            self.condition_dict = self.request.session.get('conditionals')

        return initial

    # In addition to form_list, the done() method is passed a form_dict, which allows you to access the wizard’s forms based on their step names.
    def done(self, form_list, form_dict, **kwargs):
        # Find question and questionnaire
        qn = self.initial_dict.get('0')['qid']
        qnaire = qn.qid
        store_token = self.request.POST['csrfmiddlewaretoken'] + str(time.time())
        idx = [key for key in form_dict]
        formuser =self.request.user

        for key in form_dict:
            f = form_dict.get(key)
            i = idx.index(key)
            qn = self.initial_dict.get(key)['qid']
            #Get response
            response = list(form_list)[i].cleaned_data

            if qn.duplicate:
                questions = ['question','question2']
                if (hasattr(f,'t1') and isinstance(f.t1,User)):
                    users = [f.t2,f.t1]
                else:
                    users = [formuser, formuser]
            else:
                questions = ['question']
                users = [formuser]

            for q in questions:
                choiceidx = response[q]
                if qn.question_type in [3,5]:
                    # Not choice but free text
                    answers = [choiceidx]
                elif qn.question_type == 2:
                    answers = qn.choice_set.filter(choice_value__in=choiceidx)
                else:
                    answers = qn.choice_set.filter(choice_value=choiceidx)
                testee = users.pop()
                # Load save for each choice
                for answer in answers:
                    tresult = TestResult()
                    tresult.testee = testee
                    tresult.test_questionnaire = qnaire
                    tresult.test_result_question = qn
                    if qn.question_type == 5:
                        tresult.test_result_date = answer
                    elif qn.question_type == 3:
                        tresult.test_result_text = answer
                    else:
                        tresult.test_result_choice = answer

                    tresult.test_token = store_token
                    tresult.save()

        # Store category for user
        subjectcat = SubjectQuestionnaire(subject=self.request.user, questionnaire=qnaire,
                                     session_token=store_token)
        subjectcat.save()
        return render(self.request, 'questionnaires/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'qnaire_title' : qnaire.title,
        })


###################################
# ############# SINGLE PAGE ##################

def singlepage_questionnaire(request,qnaire, questions):
    template = 'questionnaires/single.html'
    """
    Detect user
    """
    user = request.user
    messages = ''
    qbgcolor = qnaire.bgcolor
    qtextcolor = qnaire.textcolor
    # Create the formset, specifying the form and formset we want to use.
    LinkFormSet = formset_factory(AnswerForm, formset=BaseQuestionFormSet, validate_max=False)
    link_data = [{'qid': q, 'myuser': request.user} for q in questions]

    if request.method == 'POST':
        link_formset = LinkFormSet(request.POST) #cannot reload as dynamic
        token = request.POST['csrfmiddlewaretoken'] + str(time.time())
        if link_formset.is_valid():
            # Now save the data for each form in the formset
            new_data = []
            for i in range(0, len(link_data)):
                formid = 'form-%d-question' % i
                val = request.POST[formid]  # TODO Validate data input
                qn = Question.objects.get(pk=link_data[i]['qid'].pk)
                if qn.question_type in [3,5]:
                    choices = [val]
                elif qn.question_type == 2:
                    choices = qn.choice_set.filter(choice_value__in=val)
                else:
                    choices = qn.choice_set.filter(choice_value=val)

                # Load save for each choice
                for answer in choices:
                    tresult = TestResult()
                    tresult.testee = user
                    tresult.test_questionnaire = qnaire
                    tresult.test_result_question = qn
                    if qn.question_type == 5:
                        tresult.test_result_date = answer
                    elif qn.question_type == 3:
                        tresult.test_result_text = answer
                    else:
                        tresult.test_result_choice = answer

                    tresult.test_token = token
                    tresult.save()

            # Save user info with category
            template='questionnaires/done.html'
            try:
                subjectcat = SubjectQuestionnaire(subject=user, questionnaire=qnaire, session_token=token)
                subjectcat.save()
                messages='Congratulations, %s!  You have completed the questionnaire.' % user
            except IntegrityError:
                messages.error(request, 'There was an error saving your result.')




    else:
        link_formset = LinkFormSet(initial=link_data)

    context = {
        'formset': link_formset,
        'qtitle' : qnaire.title,
        'messages': messages,
        'qbgcolor' : qbgcolor,
        'qtextcolor': qtextcolor,
    }

    return render(request, template, context)

