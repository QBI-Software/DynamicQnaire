import datetime
import time
import re

from django.db import IntegrityError
from django.forms import formset_factory
from django.shortcuts import render
from formtools.wizard.views import SessionWizardView
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from .forms import AnswerForm, BaseQuestionFormSet
from .customforms import BABYForm1
from .models import Questionnaire, Question, TestResult, SubjectQuestionnaire, SubjectVisit


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

### BABY MEASUREMENTS ####
def baby_measurements(request, code):
    """
    Baby measurements questionnaire to be filled out by a parent (only)
    :param request: HTTP request URL
    :param code: Questionnaire code from URL
    :return: custom questionnaire form
    """
    user = request.user
    #print("DEBUG: code=", code)
    visit = SubjectVisit.objects.filter(parent1=user) | SubjectVisit.objects.filter(parent2=user)
    messages = ''
    template = 'custom/baby.html'
    if visit:
        t1 = visit[0].subject.username
        if visit[0].subject.first_name:
            t1 = visit[0].subject.first_name
        t2 = visit[1].subject.username
        if visit[1].subject.first_name:
            t2 = visit[1].subject.first_name

    else:
        t1 = 'Twin1'
        t2 = 'Twin2'
        messages ='No twins found for this user'

    qnaire = Questionnaire.objects.get(code=code)
    #Both twins on one page
    Twin1FormSet = formset_factory(BABYForm1, extra=5)
    Twin2FormSet = formset_factory(BABYForm1, extra=5)
    if request.method == 'POST':
        t1_formset = Twin1FormSet(request.POST, request.FILES, prefix='twin1')
        t2_formset = Twin2FormSet(request.POST, request.FILES, prefix='twin2')
        token = request.POST['csrfmiddlewaretoken'] + str(time.time())
        if t1_formset.is_valid() and t2_formset.is_valid():
            headers = ['Twin', 'Date','Age', 'Head', 'Length', 'Weight']
            #t1
            t1_answer = {}
            rnum = 1
            t1_answer[0] = headers
            for form in t1_formset:
                #if form.has_changed():
                tdate = form.cleaned_data.get('measurement_date')
                if isinstance(tdate, datetime.date):
                    tfdate = tdate.strftime('%d-%m-%Y')
                    t1_answer[rnum] = [t1, tfdate,
                                       form.cleaned_data.get('measurement_age'),
                                       form.cleaned_data.get('measurement_head'),
                                       form.cleaned_data.get('measurement_length'),
                                       form.cleaned_data.get('measurement_weight'),
                                       ]
                    rnum += 1

            tresult = TestResult()
            if visit:
                tresult.testee = visit[0].subject
            else:
                tresult.testee = user
            tresult.test_questionnaire = qnaire
            tresult.test_result_question = qnaire.question_set.all()[0] #check these exist
            tresult.test_result_text = t1_answer
            tresult.test_token = token
            tresult.save()

            # t2
            t2_answer = {}
            rnum = 1
            t2_answer[0] = headers
            for form in t2_formset:
                #if form.has_changed():
                tdate = form.cleaned_data.get('measurement_date')
                if type(tdate) is datetime:
                    tfdate = tdate.strftime('%d-%m-%Y')
                    t2_answer[rnum] = [t2, tfdate,
                                        form.cleaned_data.get('measurement_age'),
                                        form.cleaned_data.get('measurement_head'),
                                        form.cleaned_data.get('measurement_length'),
                                        form.cleaned_data.get('measurement_weight'),
                                       ]
                    rnum += 1

            tresult = TestResult()
            if visit:
                tresult.testee = visit[1].subject
            else:
                tresult.testee = user
            tresult.test_questionnaire = qnaire
            tresult.test_result_question = qnaire.question_set.all()[1]
            tresult.test_result_text = t2_answer
            tresult.test_token = token
            tresult.save()

            # Save user info with category
            template = 'questionnaires/done.html'
            try:
                subjectcat = SubjectQuestionnaire(subject=user, questionnaire=qnaire,
                                                  session_token=token)
                subjectcat.save()
                messages = 'Congratulations, %s!  You have completed the questionnaire.' % user
            except IntegrityError:
                print("ERROR: Error saving results")
                messages.error(request, 'There was an error saving your result.')
    else:
        t1_formset = Twin1FormSet(prefix='twin1')
        t2_formset = Twin2FormSet(prefix='twin2')
    return render(request, template, {
        't1_formset': t1_formset,
        't2_formset': t2_formset,
        'qtitle': qnaire.title,
        'twin1': t1,
        'twin2': t2,
        'messages': messages,
    })

##########################Both twins per page ######################
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
        raise ValueError('No twins found for this user')

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
    print("debug: t2=", Twin2_questions)
    if request.method == 'POST':
        t1_formset = Twin1FormSet(request.POST, prefix='twin1')
        t2_formset = Twin2FormSet(request.POST, prefix='twin2')
        token = request.POST['csrfmiddlewaretoken'] + str(time.time())
        if t1_formset.is_valid() and t2_formset.is_valid():
            #data in form.data['twin1-0-question'] etc
            for i in range(1, len(Twin1_data)):
                formid = 'twin1-%d-question' % i
                val = request.POST[formid]  # TODO Validate data input
                #qn = Question.objects.get(pk=Twin1_data[i]['qid'].pk)
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
                val = request.POST[formid]  # TODO Validate data input
                #qn = Question.objects.get(pk=Twin1_data[i]['qid'].pk)
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
                subjectcat = SubjectQuestionnaire(subject=user, questionnaire=qnaire,
                                                  session_token=token)
                subjectcat.save()
                messages = 'Congratulations, %s!  You have completed the questionnaire.' % user
            except IntegrityError:
                print("ERROR: Error saving results")
                messages.error(request, 'There was an error saving your result.')
    else:
        t1_formset = Twin1FormSet(prefix='twin1', initial=Twin1_data)
        t2_formset = Twin2FormSet(prefix='twin2', initial=Twin2_data)
    return render(request, template, {
        't1_formset': t1_formset,
        't2_formset': t2_formset,
        'qtitle': qnaire.title,
        'twin1': t1,
        'twin2': t2,
        'messages': messages,
    })

