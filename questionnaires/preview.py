from formtools.preview import FormPreview
from .models import Questionnaire, Question, Choice
from django.http import HttpResponse, HttpResponseRedirect

class QuestionnaireFormPreview(FormPreview):

    def done(self, request, cleaned_data):
        # Do something with the cleaned_data, then redirect
        # to a "success" page.
        return HttpResponseRedirect('/form/success')
