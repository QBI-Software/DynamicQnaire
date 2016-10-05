from django.shortcuts import get_object_or_404, render,redirect, resolve_url, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from formtools.wizard.views import SessionWizardView
from django.views.generic import FormView, RedirectView
from formtools_addons import WizardAPIView
from django.forms.formsets import formset_factory
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import REDIRECT_FIELD_NAME, login, logout, authenticate
from django.contrib.auth.views import password_change
from django.contrib.auth.models import User, Group
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.conf import settings
from collections import OrderedDict
from django.utils import six
from django.template import RequestContext
from ipware.ip import get_ip
from axes.utils import reset
import os
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
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
import datetime
###Local classes
from .models import Questionnaire, Question, Choice, TestResult
from .forms import BaseQuestionFormSet, AxesCaptchaForm, AnswerForm


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
            print("DEBUG: User=", user)
            user_results = TestResult.objects.filter(testee=user).order_by('test_datetime')
            print("DEBUG: user_results=", user_results)
            usergrouplist = user.groups.values_list('name') #ALL: Group.objects.values_list('name')
            print("DEBUG: user groups=", usergrouplist)
            qlist=self.get_queryset()
            if (not user.is_superuser):
                qlist = qlist.filter(group__name__in=usergrouplist) #q.group.all() for each group

            for r in user_results:
                rlist[r.test_questionnaire.id] = (r.test_datetime, r.test_questionnaire.title)
                qlist = qlist.exclude(pk=r.test_questionnaire.id)
        context['questionnaire_list'] = qlist
        context['result_list']= rlist

        return context


class DetailView(generic.DetailView):
    model = Questionnaire
    template_name = 'questionnaires/detail.html'


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'questionnaires/results.html'

def load_questionnaire(request, *args, **kwargs):
    """ Prepare questionnaire wizard with required questions """
    #print('DEBUG: load kwargs=', kwargs)
    qid = kwargs.pop('pk')
    if qid is not None:
        qnaire = Questionnaire.objects.get(pk=qid)
        formlist=[AnswerForm] * qnaire.question_set.count()
        questions = qnaire.question_set.order_by('order')
        linkdata = {}
        for q in questions:
            linkdata[str(q.order-1)] = {'qid': q}
        initdata = OrderedDict(linkdata)
        print("DEBUG:initdata=", initdata)

    else:
        print('DEBUG: qid is none')
    print('DEBUG:form_list: ', formlist)

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
        print('DEBUG: form init: step=',step)
        print('DEBUG: form init: current=', self.steps.current)
        print('DEBUG: form init: self=', self)
        print('DEBUG: form init: kwargs=', self.kwargs)
        print('DEBUG: form init: dict=', self.initial_dict)
        #print('DEBUG: form init: conditional=', self.condition_dict)
        return initial

    # def get_context_data(self, form, **kwargs):
    #     context = super(QuestionnaireWizard, self).get_context_data(form=form, **kwargs)
    #     if self.steps.current == '0':
    #         context.update({'user': self.request.user})
    #     return context


    # def process_formdata(self,form):
    #     print('DEBUG:processformdata form=', form)
    #     #print('DEBUG: processformdata: user=', self.request.user)
    #     fdata = self.process_step(form)
    #     print("DEBUG: cleaned data: ", fdata) #THIS ONE GIVES VALUES
    #     #fdata1 = self.get_form_step_data(fdata)
    #     #print("DEBUG: form data: ", fdata1)
    #     #save to database
    #     return fdata

    # In addition to form_list, the done() method is passed a form_dict, which allows you to access the wizard’s forms based on their step names.
    def done(self, form_list, form_dict, **kwargs):
        #print('DEBUG: form done: self=', self)
        #print('DEBUG: form done: kwargs=', kwargs)
        print('DEBUG: form init: formlist=', form_list)
        print('DEBUG: form done: init=', self.initial_dict)
        print('DEBUG: form done: formdict=', form_dict)
        #fdata = self.process_formdata(form_list)
        for key in form_dict:
            print('DEBUG:key=', key)
            print('DEBUG:q=',self.initial_dict.get(key)['qid'] )
            #Find question and questionnaire
            qn = self.initial_dict.get(key)['qid']
            print('DEBUG:questionid=', qn.id)
            qnaire = qn.qid
            print('DEBUG: questionnaire=', qnaire.title)
            #Get response
            response = list(form_list)[int(key)].cleaned_data
            choiceidx = int(response['question'])
            print('DEBUG: formdata=', response['question'])  # response {'question',: '0'}
            answer = qn.choice_set.filter(choice_value=choiceidx)[0]
            print('DEBUG: answer=', answer)
            # Load save
            tresult = TestResult()
            tresult.testee = self.request.user
            tresult.test_questionnaire = qnaire
            tresult.test_result_question = qn
            tresult.test_result_choice = answer
            tresult.test_token = self.request.POST['csrfmiddlewaretoken']
            tresult.save()
            print('TESTRESULT:', " Qnaire:", tresult.test_questionnaire.title,
                  " Qn:", tresult.test_result_question.question_text,
                  " Val:", tresult.test_result_choice.choice_text)

        return render(self.request, 'questionnaires/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'qnaire_title' : qnaire.title,
        })







############## TESTING ##################
class OnepageQuestionnaireWizard(generic.FormView):
    #model = Questionnaire
    template_name = 'contact.html'
    form_class = AnswerForm
    form_list={}
    templates={'q-info':'questionnaires/results.html'}

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def get_form_initial(self, step):
        print('DEBUG: initial step=', step)
        return self.initial_dict.get(step, {})

    def get_form_instance(self, step):
        print('DEBUG: instance=', step)
        return self.instance_dict.get(step, None)

    def get_context_data(self, **kwargs):
        context = super(QuestionnaireWizard, self).get_context_data(**kwargs)

        print('DEBUG: context=', context)
        if self.steps.current == 0:
            print("DEBUG:Initial step")
            qid = self.kwargs.get('pk')
            print("DEBUG: Qid=", qid)
            #get forms from Questions
            qnaire = Questionnaire.objects.get(pk=qid)
            flist=[0] * qnaire.question_set.count() #initialize
            num = 1
            for q in qnaire.question_set.all.order_by('order'):
                print("DEBUG: Q=", q.question_text)
                step = 'step-%d' % q.order - 1
                flist[step] = AnswerForm(prefix='q_info', initial={'qid':q.id,'qtext':q.question_text, 'qchoices': q.choice_set.all()})
            #self.form_list = flist
            print("DEBUG: form_list=", flist)
            context.update({'form_list': flist})
        print('DEBUG: context2=', context)
        return context



    def done(self, form_list, **kwargs):
        print("DEBUG: DONE")
        return render(self.request, 'questionnaires/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
        })


class ContactWizard(SessionWizardView):


    def done(self, form_list, form_dict, **kwargs):
        print("DEBUG: form_dict=", form_dict)
        print("DEBUG: form_list=", form_list)
        form_data = self.process_formdata(form_dict)

        return self.render('/questionnaires/done.html')

    def process_formdata(self,form):
        print('DEBUG:process_step', form)
        fdata = self.get_all_cleaned_data()
        print("DEBUG: cleaned data: ", fdata) #THIS ONE GIVES VALUES
        #fdata1 = self.get_form_step_data(fdata)
        #print("DEBUG: form data: ", fdata1)
        #save to database
        return fdata


def test_questionnaire(request,*args,**kwargs):
    """
    Detect user
    """
    user = request.user
    print('DEBUG: user=', user)
    messages = ''
    #Questionnaire ID
    print("DEBUG:kwargs=",kwargs)
    qid = kwargs.get('pk')
    qnaire = Questionnaire.objects.get(pk=qid)

    # Create the formset, specifying the form and formset we want to use.
    LinkFormSet = formset_factory(AnswerForm, formset=BaseQuestionFormSet, validate_max=True)
    print("DEBUG: formset=",LinkFormSet)
    # Get our existing link data for this user.  This is used as initial data.
    questions = qnaire.question_set.order_by('order') #Question.objects.order_by('order')
    link_data = [{'qid': q.id} for q in questions]
    print("DEBUG:linkdata=",link_data)

    if request.method == 'POST':
        print("POST=",request.POST)
        for f in request.POST:
            print("POST ITEM=",f)
        # Now save the data for each form in the formset TODO Validate data input
        new_data = []
        for i in range(0,len(link_data)):
            formid = 'form-%d-question' % i
            val = request.POST[formid]
            print(formid, "=" , val ) #need to validate
            tresult = TestResult()
            tresult.testee = user
            #tresult.test_datetime = datetime.now() #?defaultdatetime.datetime.fromtimestamp(tresult.test_datetime),
            tresult.test_questionnaire = qnaire
            qn = Question.objects.get(pk=link_data[i]['qid'])
            tresult.test_result_question = qn
            q1 = qn.choice_set.filter(choice_value=val)[0]
            #print(q1)
            tresult.test_result_choice = q1
            tresult.test_token = request.POST['csrfmiddlewaretoken']
            tresult.save()
            print('TESTRESULT:',  " Qnaire:", tresult.test_questionnaire.title,
                  " Qn:", tresult.test_result_question.question_text,
                  " Val:", tresult.test_result_choice.choice_text)

        link_formset = LinkFormSet(request.POST) #cannot reload as dynamic

        if link_formset.is_valid():

            # Save user info
            messages ='Congratulations, %s!  You have completed the questionnaire.' % user
           # print("DATASET=", link_formset)


            # for f in link_formset:
            #     cd = f.cleaned_data
            #     print("DATA=",cd.get('form-0-question'))

                #if question:
                 #   print("DEBUG: Adding question data:", question.label)
                    #new_links.append(UserLink(user=user, anchor=anchor, url=url))

            # try:
            #     with transaction.atomic():
            #         #Replace the old with the new
            #         UserLink.objects.filter(user=user).delete()
            #         UserLink.objects.bulk_create(new_links)
            #
            #         # And notify our users that it worked
            #         messages.success(request, 'You have updated your profile.')
            #
            # except IntegrityError: #If the transaction failed
            #     messages.error(request, 'There was an error saving your profile.')
            #     return redirect(reverse('profile-settings'))

    else:
        link_formset = LinkFormSet(initial=link_data)

    context = {
        'formset': link_formset,
        'qtitle' : qnaire.title,
        'messages': messages,
    }

    return render(request, 'questionnaires/test.html', context)