from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from formtools.wizard.views import SessionWizardView
from formtools_addons import WizardAPIView
from django.forms.formsets import formset_factory
import datetime
from .models import Questionnaire, Question, Choice, TestResult
from .forms import BaseQuestionFormSet, MultipageQuestionForm


class IndexView(generic.ListView):
    template_name = 'questionnaires/index.html'
    context_object_name = 'questionnaire_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Questionnaire.objects.order_by('title')


class DetailView(generic.DetailView):
    model = Questionnaire
    template_name = 'questionnaires/detail.html'


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'questionnaires/results.html'

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'questionnaires/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('questionnaires:results', args=(question.id,)))

class QuestionnaireWizard(generic.FormView):
    #model = Questionnaire
    template_name = 'contact.html'
    form_class = MultipageQuestionForm
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
                flist[step] = MultipageQuestionForm(prefix='q_info', initial={'qid':q.id,'qtext':q.question_text, 'qchoices': q.choice_set.all()})
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
    LinkFormSet = formset_factory(MultipageQuestionForm, formset=BaseQuestionFormSet, validate_max=True)
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