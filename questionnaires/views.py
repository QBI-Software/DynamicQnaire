import os
from collections import OrderedDict

from axes.utils import reset
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import password_change
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.db.models import Count
from django.forms.formsets import formset_factory
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
from .models import Questionnaire, Question, Choice, TestResult, SubjectCategory,Category
from .forms import SinglepageQuestionForm, BaseQuestionFormSet, AxesCaptchaForm, AnswerForm


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
####
class IndexView(generic.ListView):
    template_name = 'questionnaires/index.html'
    context_object_name = 'questionnaire_list'

    def get_queryset(self):
        return Questionnaire.objects.all()

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        user = self.request.user
        rlist = {}
        qlist = {}
        grouplist = {}
        if (user is not None and user.is_active):
            user_results = TestResult.objects.filter(testee=user).distinct('test_questionnaire') #.order_by('test_datetime')
            usergrouplist = user.groups.values_list('name') #ALL: Group.objects.values_list('name')
            usercategory = self.getCurrentSubjectCategory(usergrouplist)
            qlist=self.get_queryset()
            if (not user.is_superuser):
                qlist = qlist.filter(category=usercategory).filter(group__name__in=usergrouplist) #q.group.all() for each group

            for r in user_results:
                rlist[r.test_questionnaire.id] = (r.test_datetime, r.test_questionnaire.title, r.test_questionnaire.category)
                qlist = qlist.exclude(pk=r.test_questionnaire.id)
        context['questionnaire_list'] = qlist
        context['result_list']= rlist

        return context

    def getCurrentSubjectCategory(self, usergrouplist):
        catlist = SubjectCategory.objects.filter(subject=self.request.user)
        cat = Category.objects.filter(code='W1')  # Wave 1 default
        if (catlist):
            #For each category, check number of entries matches number in questionnaires
            checklist = Category.objects.all().order_by('code')
            for c in checklist:
                cat = c
                num = catlist.filter(questionnaire__category=c).count()
                print("DEBUG: CAT=", c,' has done', num, ' tests')
                qnum = Questionnaire.objects.filter(category=c).filter(group__name__in=usergrouplist).count()
                if (num < qnum):
                    break
        return cat




class DetailView(generic.DetailView):
    model = Questionnaire
    template_name = 'questionnaires/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context

# #Generic filtered table
# class FilteredSingleTableView(tables.SingleTableView):
#     filter_class = None
#
#     def get_table_data(self):
#         data = super(FilteredSingleTableView, self).get_table_data()
#         self.filter = self.filter_class(self.request.GET, queryset=data)
#         return self.filter
#
#     def get_context_data(self, **kwargs):
#         context = super(FilteredSingleTableView, self).get_context_data(**kwargs)
#         context['filter'] = self.filter
#         return context

class ResultsView(generic.TemplateView):
    template_name = 'questionnaires/results.html'
    raise_exception = True

    def get_queryset(self, **kwargs):
        qchoices = Choice.objects.annotate(choice_count=Count('testresult'))

        return qchoices.order_by('question')

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        table = self.get_queryset() #ResultsReportTable(self.get_queryset())
        #RequestConfig(self.request).configure(table)
        context['results_table'] = table

        return context


def load_questionnaire(request, *args, **kwargs):
    """ Prepare questionnaire wizard with required questions """
    qid = kwargs.get('pk')
    if qid is not None:
        qnaire = Questionnaire.objects.get(pk=qid)
        if qnaire.type =='single':
            return singlepage_questionnaire(request, *args, **kwargs)

        formlist=[AnswerForm] * qnaire.question_set.count()
        questions = qnaire.question_set.order_by('order')
        linkdata = {}
        for q in questions:
            linkdata[str(q.order-1)] = {'qid': q}
        initdata = OrderedDict(linkdata)

    form = QuestionnaireWizard.as_view(form_list=formlist, initial_dict=initdata)
    return form(context=RequestContext(request), request=request)

class QuestionnaireWizard(SessionWizardView):
    template_name = 'questionnaires/qpage.html'
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photos'))

    def dispatch(self, request, *args, **kwargs):
    #     self.sheet_id_initial = kwargs.get('sheet_id_initial', None)
        return super(QuestionnaireWizard, self).dispatch(request, *args, **kwargs)


    def get_form_initial(self, step):
        initial = self.initial_dict.get(step)
        initial.update({'myuser': self.request.user})
        return initial

    # In addition to form_list, the done() method is passed a form_dict, which allows you to access the wizard’s forms based on their step names.
    def done(self, form_list, form_dict, **kwargs):

        # Find question and questionnaire
        qn = self.initial_dict.get('0')['qid']
        qnaire = qn.qid
        # Store category for user
        subjectcat = SubjectCategory(subject=self.request.user, questionnaire=qnaire)
        subjectcat.save()
        for key in form_dict:

            #Get response
            response = list(form_list)[int(key)].cleaned_data
            choiceidx = response['question']
            qntype = qn.question_type
            if qntype == 3:
                # Not choice but free text
                answerstring = True
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

                print('TESTRESULT:', " Qnaire:", tresult.test_questionnaire.title,
                      " Qn:", tresult.test_result_question.question_text)
                if qntype == 3:
                    print(" ValText:", tresult.test_result_text)
                else:
                    print(" ValChoice:", tresult.test_result_choice.choice_text)

        return render(self.request, 'questionnaires/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'qnaire_title' : qnaire.title,
        })


###################################
# ############# SINGLE PAGE ##################

def singlepage_questionnaire(request,*args,**kwargs):
    template = 'questionnaires/test.html'
    """
    Detect user
    """
    user = request.user
    messages = ''
    #Questionnaire ID
    qid = kwargs.get('pk')
    qnaire = Questionnaire.objects.get(pk=qid)

    # Create the formset, specifying the form and formset we want to use.
    LinkFormSet = formset_factory(SinglepageQuestionForm, formset=BaseQuestionFormSet, validate_max=True)
    # Get our existing link data for this user.  This is used as initial data.
    questions = qnaire.question_set.order_by('order') #Question.objects.order_by('order')
    link_data = [{'qid': q.id} for q in questions]

    if request.method == 'POST':

        link_formset = LinkFormSet(request.POST) #cannot reload as dynamic

        if link_formset.is_valid():
            # Now save the data for each form in the formset
            new_data = []
            for i in range(0, len(link_data)):
                formid = 'form-%d-question' % i
                val = request.POST[formid]  # TODO Validate data input
                tresult = TestResult()
                tresult.testee = user
                tresult.test_questionnaire = qnaire
                qn = Question.objects.get(pk=link_data[i]['qid'])
                tresult.test_result_question = qn
                q1 = qn.choice_set.filter(choice_value=val)[0]
                # print(q1)
                tresult.test_result_choice = q1
                tresult.test_token = request.POST['csrfmiddlewaretoken']
                tresult.save()
                print('SINGLEPAGE: TESTRESULT:', " Qnaire:", tresult.test_questionnaire.title,
                      " Qn:", tresult.test_result_question.question_text,
                      " Val:", tresult.test_result_choice.choice_text)

            # Save user info with category
            template='questionnaires/done.html'
            try:
                subjectcat = SubjectCategory(subject=user, questionnaire=qnaire)
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
    }

    return render(request, template, context)