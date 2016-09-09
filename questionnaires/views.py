from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from formtools.wizard.views import SessionWizardView

from .models import Questionnaire, Question, Choice
from .forms import QuestionForm

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

class QuestionnaireWizard(SessionWizardView):
    model = Questionnaire

    def get_form_initial(self, step):
        print('DEBUG: initial=', step)
        return self.initial_dict.get(step, {})

    def get_form_instance(self, step):
        print('DEBUG: instance=', step)
        return self.instance_dict.get(step, None)

    def get_context_data(self, form, **kwargs):
        context = super(QuestionnaireWizard, self).get_context_data(form=form, **kwargs)

        print('DEBUG: context=', context)
        qid = self.kwargs.get('pk')
        print("DEBUG: Qid=", qid)
        #get forms from Questions
        qnaire = Questionnaire.objects.get(pk=qid)
        flist=[0] * qnaire.question_set.count() #initialize
        num = 1
        for q in qnaire.question_set.all():
            print("DEBUG: Q=", q.question_text)
            flist[q.order-1] = QuestionForm(prefix='q_info', initial={'qid':q.id,'qtext':q.question_text, 'qchoices': q.choice_set.all()})

        context.update({'form_dict': flist})
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
