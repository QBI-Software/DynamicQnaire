import ast
from datetime import datetime
import os
import re
import string
import time
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import IntegrityError
from django.forms import formset_factory
from django.shortcuts import render
from django.template import RequestContext
from django.utils import timezone

from .customforms import BABYForm1,FamilyHistoryForm, FamilyChoiceForm
from .forms import AnswerForm, BaseQuestionFormSet
from .models import Questionnaire, TestResult, SubjectQuestionnaire, SubjectVisit
from .views import get_conditional_string, QuestionnaireWizard


#################CUSTOM QUESTIONNAIRES - HARD-CODED ###############
# Some questionnaires have very different formats so this is used to define these

### BABY MEASUREMENTS ####
@login_required
def baby_measurements(request, code):
    """
    Baby measurements questionnaire to be filled out by a parent (only)
    :param request: HTTP request URL
    :param code: Questionnaire code from URL
    :return: custom questionnaire form
    """

    messages = ''
    template = 'custom/baby.html'
    error_template = 'custom/error.html'
    user = request.user

    try:
        qnaire = Questionnaire.objects.get(code=code)
    except ObjectDoesNotExist:
        raise ValueError('Unable to find questionnaire')

    visit = SubjectVisit.objects.filter(parent1=user) | SubjectVisit.objects.filter(parent2=user)
    if visit:
        twin1 = visit[0].subject
        twin2 = visit[1].subject
        t1 = twin1.username
        if twin1.first_name:
            t1 = twin1.first_name
        t2 = twin2.username
        if twin2.first_name:
            t2 = twin2.first_name
        twins = [twin2, twin1]
    else:
        t1 = 'Twin 1'
        t2 = 'Twin 2'
        messages = 'No twins found for this user: %s' % user.username
        return render(request, error_template, {
            'qtitle': qnaire.title,
            'messages': messages,
        })

    #Allow question text to be edited
    if qnaire.question_set.count() != 2:
        messages ='Two questions need to be set up for this custom questionnaire'
        return render(request, error_template, {
            'qtitle': qnaire.title,
            'messages': messages,
        })
    else:
        Twin_questions = qnaire.question_set.all().order_by('order')
        q1 = re.sub('Twin1', t1, Twin_questions[0].question_text, flags=re.IGNORECASE)
        q2 = re.sub('Twin2', t2, Twin_questions[1].question_text, flags=re.IGNORECASE)
        questions = [Twin_questions[1],Twin_questions[0]]

    #Both twins on one page
    Twin1FormSet = formset_factory(BABYForm1, extra=5)
    Twin2FormSet = formset_factory(BABYForm1, extra=5)
    if request.method == 'POST':
        t1_formset = Twin1FormSet(request.POST, request.FILES, prefix='twin1')
        t2_formset = Twin2FormSet(request.POST, request.FILES, prefix='twin2')
        token = request.POST['csrfmiddlewaretoken'] + str(time.time())
        if t1_formset.is_valid() and t2_formset.is_valid():
            start = request.session.get('start')
            if start:
                start = datetime.fromtimestamp(float(start))
            else:
                start = timezone.now()
            headers = ['Twin', 'Age', 'Head', 'Length', 'Weight', 'Source','Other']

            for fmset in [t1_formset, t2_formset]:
                t_answer = {}
                t_answer[0] = headers
                rnum = 1
                if visit:
                    testee = twins.pop()
                else:
                    testee = user
                for form in fmset:
                    t_answer[rnum] = [testee.username,
                                      form.cleaned_data.get('measurement_age'),
                                      form.cleaned_data.get('measurement_head'),
                                      form.cleaned_data.get('measurement_length'),
                                      form.cleaned_data.get('measurement_weight'),
                                      form.cleaned_data.get('measurement_source'),
                                      form.cleaned_data.get('measurement_source_other'),
                                      ]
                    rnum += 1

                tresult = TestResult()
                tresult.testee = testee
                tresult.test_questionnaire = qnaire
                tresult.test_result_question = questions.pop()
                tresult.test_result_text = t_answer
                tresult.test_token = token
                tresult.save()

            # Save user info with category
            template = 'questionnaires/done.html'
            try:
                subjectcat = SubjectQuestionnaire(subject=user, questionnaire=qnaire, start=start,
                                                  session_token=token)
                subjectcat.save()
                messages = 'Congratulations, %s!  You have completed the questionnaire.' % user
            except IntegrityError:
                messages='ERROR: There was an error saving your result.'
        else:
            messages='All fields must have values. Please enter zero if not available.'
    else:
        t1_formset = Twin1FormSet(prefix='twin1')
        t2_formset = Twin2FormSet(prefix='twin2')
        request.session['start'] = str(time.time())

    return render(request, template, {
        't1_formset': t1_formset,
        't2_formset': t2_formset,
        'qtitle': qnaire.title,
        'twin1': t1,
        'twin2': t2,
        'q1' : q1,
        'q2' : q2,
        'messages': messages,
    })

##########################Both twins per page ######################
@login_required
def maturation(request, code):
    """
    Sexual maturation questionnaire to be filled out by a parent (only)
    :param request: HTTP request URL
    :param code: Questionnaire code from URL
    :return: custom questionnaire form
    """
    user = request.user
    #print("DEBUG: code=", code)

    messages = ''
    #template = 'custom/maturation.html'
    template = 'custom/panelviewer.html'
    error_template = 'custom/error.html'
    try:
        qnaire = Questionnaire.objects.get(code=code)
    except ObjectDoesNotExist:
        raise ValueError('Unable to find questionnaire')

    visit = SubjectVisit.objects.filter(parent1=user) | SubjectVisit.objects.filter(parent2=user)
    if visit:
        twin1 = visit[0].subject
        twin2 = visit[1].subject
        t1 = twin1.username
        if twin1.first_name:
            t1 = twin1.first_name
        t2 = twin2.username
        if twin2.first_name:
            t2 = twin2.first_name
    else:
        messages ='No twins found for this user: %s' % user.username
        return render(request, error_template, {
        'qtitle': qnaire.title,
        'messages': messages,
    })

    #Both twins on one page - determine male or female
    pattern1 = 'Twin'

    Twin1FormSet = formset_factory(AnswerForm, formset=BaseQuestionFormSet, validate_max=False)
    Twin1_questions = qnaire.question_set.filter(group__in=twin1.groups.all()).order_by('order').distinct()
    for q in Twin1_questions:
        q.question_text=re.sub(pattern1, t1, q.question_text, flags=re.IGNORECASE)
    Twin1_data = [{'qid': q, 'myuser': twin1} for q in Twin1_questions]

    Twin2FormSet = formset_factory(AnswerForm, formset=BaseQuestionFormSet, validate_max=False)
    Twin2_questions = qnaire.question_set.filter(group__in=twin2.groups.all()).order_by('order').distinct()
    for q in Twin2_questions:
        q.question_text = re.sub(pattern1, t2, q.question_text, flags=re.IGNORECASE)
    Twin2_data = [{'qid': q, 'myuser': twin2} for q in Twin2_questions]
    #print("debug: t2=", Twin2_questions)
    if request.method == 'POST':
        t1_formset = Twin1FormSet(request.POST, prefix='twin1')
        t2_formset = Twin2FormSet(request.POST, prefix='twin2')
        token = request.POST['csrfmiddlewaretoken'] + str(time.time())
        if t1_formset.is_valid() and t2_formset.is_valid():
            start = request.session.get('start')
            if start:
                start = datetime.fromtimestamp(float(start))
            else:
                start = timezone.now()
            for i in range(1, len(Twin1_data)):
                formid = 'twin1-%d-question' % i
                if not request.POST.get(formid, False):
                    continue
                val = request.POST[formid]
                qn = Twin1_questions[i]
                tresult = TestResult()
                if visit:
                    tresult.testee = twin1

                tresult.test_questionnaire = qnaire
                tresult.test_result_question = qn
                tresult.test_result_text = [t1,val]
                tresult.test_token = token
                tresult.save()

            # t2
            for i in range(1, len(Twin2_data)):
                formid = 'twin2-%d-question' % i
                if not request.POST.get(formid, False):
                    continue
                val = request.POST[formid]
                qn = Twin2_questions[i]
                tresult = TestResult()
                if visit:
                    tresult.testee = twin2

                tresult.test_questionnaire = qnaire
                tresult.test_result_question = qn
                tresult.test_result_text = [t2,val]
                tresult.test_token = token
                tresult.save()

            # Save user info with category
            template = 'questionnaires/done.html'
            try:
                subjectcat = SubjectQuestionnaire(subject=user, questionnaire=qnaire, start=start,
                                                  session_token=token)
                subjectcat.save()
                messages = 'Congratulations, %s!  You have completed the questionnaire.' % user
            except IntegrityError:
                messages = "ERROR: Error saving results - please tell Admin"
                #messages.error(request, 'There was an error saving your result.')
    else:
        t1_formset = Twin1FormSet(prefix='twin1', initial=Twin1_data)
        t2_formset = Twin2FormSet(prefix='twin2', initial=Twin2_data)
        request.session['start'] = str(time.time())
    return render(request, template, {
        't1_formset': t1_formset,
        't2_formset': t2_formset,
        'qtitle': qnaire.title,
        'twin1': t1,
        'twin2': t2,
        'messages': messages,
    })

##########################################
@login_required
def familyHistoryPart1(request, code):
    """
    Family History questionnaire to be filled out by a parent
    :param request: HTTP request URL
    :param code: Questionnaire code from URL
    :return: custom questionnaire form
    """
    user = request.user
    messages = ''
    template = 'custom/history.html'
    error_template = 'custom/error.html'
    try:
        qnaire = Questionnaire.objects.get(code=code)
    except ObjectDoesNotExist:
        raise ValueError('Unable to find questionnaire')
    ParentFormSet = formset_factory(FamilyHistoryForm, formset=BaseQuestionFormSet, max_num=1,validate_max=True)
    FamilyFormSet = formset_factory(FamilyHistoryForm, formset=BaseQuestionFormSet, extra=0, max_num=50, min_num=0, validate_min=True,  validate_max=False, can_order=True)
    mother_data = [{'type': 'Mother','gender': 2,'name':'','age':'','decd':''}]
    father_data = [{'type': 'Father', 'gender': 1,'name':'','age':'','decd':''}]
    sibling_data = [{'type': 'Sibling', 'gender': 0,'name':'','age':'','decd':''},
                    {'type': 'Sibling', 'gender': 0, 'name': '', 'age': '', 'decd': ''}]
    children_data = [{'type': 'Children', 'gender': 0,'name':'','age':'','decd':''},
                     {'type': 'Children', 'gender': 0,'name':'','age':'','decd':''}]
    followup = None

    if request.method == 'POST':
        mother_formset = ParentFormSet(request.POST, prefix='mother')
        father_formset = ParentFormSet(request.POST, prefix='father')
        sibling_formset = FamilyFormSet(request.POST, prefix='sibling')
        children_formset = FamilyFormSet(request.POST, prefix='children')
        token = request.POST['csrfmiddlewaretoken'] + str(time.time())
        #Reloads for every question - no processing until questionnaire completed
        if request.POST['completed']== '1':

            if mother_formset.is_valid() and father_formset.is_valid() and sibling_formset.is_valid() and children_formset.is_valid():
                start = request.session.get('start')
                if start:
                    start = datetime.fromtimestamp(float(start))
                else:
                    start = timezone.now()
                for data in [mother_formset.cleaned_data, father_formset.cleaned_data]:
                    #names.append((data[0]['type'].lower(),data[0]['person']))
                    tresult = TestResult()
                    tresult.testee = user
                    tresult.test_questionnaire = qnaire
                    tresult.test_result_question = qnaire.question_set.order_by('order')[0]
                    tresult.test_result_text = (data[0]['type'].lower(),data[0])
                    tresult.test_token = token
                    tresult.save()

                for data in [sibling_formset.cleaned_data, children_formset.cleaned_data]:
                    num = 1
                    for n in data:
                        #names.append((n['type'].lower() + "-" + str(num),n['person']))
                        tresult = TestResult()
                        tresult.testee = user
                        tresult.test_questionnaire = qnaire
                        tresult.test_result_question = qnaire.question_set.order_by('order')[0]
                        tresult.test_result_text = (n['type'].lower() + "-" + str(num),n)
                        tresult.test_token = token
                        tresult.save()
                        num += 1

                #Proceed to Second step - Multi-page wizard
                nextcode = qnaire.code.replace('A','B')
                nextq = Questionnaire.objects.filter(code=nextcode)
                if nextq:
                    followup = nextq[0].id

                # Save user info with category
                template = 'questionnaires/done.html'
                try:
                    subjectcat = SubjectQuestionnaire(subject=user, questionnaire=qnaire, start=start,
                                                      session_token=token)
                    subjectcat.save()
                    messages = 'Congratulations, %s!  You have completed the questionnaire.' % user
                except IntegrityError:
                    messages = "ERROR: Error saving results - please tell Admin"
                    # messages.error(request, 'There was an error saving your result.')
            else:
                messages = 'ERROR: All fields should be completed.  Please remove any empty rows.'

    else:
        mother_formset = ParentFormSet(prefix='mother', initial=mother_data)
        father_formset = ParentFormSet(prefix='father', initial=father_data)
        sibling_formset = FamilyFormSet(prefix='sibling', initial=sibling_data)
        children_formset = FamilyFormSet(prefix='children', initial=children_data)
        request.session['start'] = str(time.time())

    return render(request, template, {
        'mother_formset': mother_formset,
        'father_formset': father_formset,
        'sibling_formset': sibling_formset,
        'children_formset': children_formset,
        'qtitle': qnaire.title,
        'messages': messages,
        'followup': followup,
    })

@login_required
def familyHistoryPart2(request, code):
    """
        Family History questionnaire to be filled out by a parent
        :param request: HTTP request URL
        :param code: Questionnaire code from URL
        :return: custom questionnaire form
        """
    user = request.user
    messages = ''

    try:
        qnaire = Questionnaire.objects.get(code=code)
    except ObjectDoesNotExist:
        messages='Unable to find questionnaire'
        raise ValueError(messages)
    #Assume previous questionnaire has been done
    # get choices or None
    names = [('0','Not sure'),('1','No')]
    try:
        prevcode = re.sub(r'[A-Z]$','A',qnaire.code)
        prevq = Questionnaire.objects.filter(code=prevcode)
        results = prevq[0].testresult_set.all().filter(testee=user).order_by('-test_datetime')[:1].get()
        token = results.test_token
        results = prevq[0].testresult_set.all().filter(testee=user).filter(test_token=token)
        num = 1
        for tresult in results:
            n = tresult.test_result_text
            n1 = n.replace("\\","")
            n1 = n1.replace("[","")
            n1 = n1.replace("]","")
            n = ast.literal_eval(n1)
            #names.append((n['person'].lower(), n['person']))
            names.append((n[0], n[1]['person'] + " (" + n[1]['type'] + ")"))


    except ObjectDoesNotExist:
        defaultnames=[('mother','Mother'),('father','Father'),
               ('sibling-1','Sibling #1'),('sibling-2','Sibling #2'),('sibling-3','Sibling #3'),('sibling-4','Sibling #4'),('sibling-5','Sibling #5'),('children-1','Child #1'),('children-2','Child #2'),('children-3','Child #3'),('children-4','Child #4'),('children-5','Child #5')]
        for n in defaultnames:
            names.append(n)


    linkdata = {}
    condata = {}
    #All questions - no filtering
    num = 0
    for q in qnaire.question_set.all().order_by('order'):
        linkdata[str(num)] = {'qid': q, 'nameslist': names}
        if q.conditional:
            condata[str(num)] = get_conditional_string(q)
        num += 1
    formlist = [FamilyChoiceForm] * qnaire.question_set.count()
    initdata = OrderedDict(linkdata)
    form = FamilyChoiceWizard.as_view(form_list=formlist, initial_dict=initdata, condition_dict =condata)
    return form(context=RequestContext(request), request=request)



class FamilyChoiceWizard(QuestionnaireWizard):
    template_name = 'custom/history_qpage.html'
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'photos'))

    def get_context_data(self, form, **kwargs):
        context = super(QuestionnaireWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.current == '0':
            self.request.session['start'] = str(time.time())
        return context

    def done(self, form_list, form_dict, **kwargs):
        template = 'questionnaires/done.html'
        qn = self.initial_dict.get('0')['qid']
        qnaire = qn.qid
        store_token = self.request.POST['csrfmiddlewaretoken'] + str(time.time())
        formuser = self.request.user
        followup = None;
        start = self.request.session.get('start')
        if start:
            start = datetime.fromtimestamp(float(start))
        else:
            start = timezone.now()
        # Save question results as string
        #form_data =[form.cleaned_data for form in form_list]
        for key in form_dict:
            f = form_dict.get(key)
            #print("DEBUG: F=", f)
            #print("DEBUG: F is bound=", f.is_bound)
            i = int(key)
            qn = self.initial_dict.get(key)['qid']
            t_answer = {}
            if qn.choice_set.count() ==0:
                t_answer['choices'] = self.initial_dict.get(key)['nameslist']
            else:
                choicelist = []
                for c in qn.choice_set.all():
                    choicelist.append((c.choice_value, c.choice_text))
                t_answer['choices'] = choicelist
            #Save choice list separately
            tresult = TestResult()
            tresult.testee = formuser
            tresult.test_questionnaire = qnaire
            tresult.test_result_question = qn
            tresult.test_result_text = t_answer
            tresult.test_token = store_token
            tresult.save()
            num = 1

            #Get responses
            response = f.cleaned_data
            if response:
                if (isinstance(response['question'], str)):
                    t_answer = 'response-' + str(num) + ": " + response['question']
                    tresult = TestResult()
                    tresult.testee = formuser
                    tresult.test_questionnaire = qnaire
                    tresult.test_result_question = qn
                    tresult.test_result_text = t_answer
                    tresult.test_token = store_token
                    tresult.save()
                else:  #multiplechoice
                    for r in response['question']:
                        t_answer = 'response-'+ str(num) + ": " +  r
                        num += 1
                        #Separate responses
                        tresult = TestResult()
                        tresult.testee = formuser
                        tresult.test_questionnaire = qnaire
                        tresult.test_result_question = qn
                        tresult.test_result_text = t_answer
                        tresult.test_token = store_token
                        tresult.save()

        try:
            subjectcat = SubjectQuestionnaire(subject=formuser, questionnaire=qnaire, start=start,
                                              session_token=store_token)
            subjectcat.save()
            messages = 'Congratulations, %s!  You have completed the questionnaire.' % formuser
            # Proceed to Next step if exists - Multi-page wizard
            nextcode = qnaire.code
            a = string.ascii_uppercase
            b = a.find(nextcode[-1])
            nextcode = re.sub(r'[A-Z]$',a[b+1],nextcode)

            nextq = Questionnaire.objects.filter(code=nextcode)
            if nextq:
                followup = nextq[0].id
        except IntegrityError:
            messages = "ERROR: Error saving results - please tell Admin"

        return render(self.request, template, {
            'form_data': [form.cleaned_data for form in form_list],
            'qnaire_title': qnaire.title,
            'messages': messages,
            'followup':followup,
        })