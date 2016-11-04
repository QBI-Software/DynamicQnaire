from __future__ import unicode_literals

from django import forms
from django.shortcuts import render_to_response

from formtools_addons import SessionMultipleFormWizardView

from .formscustom import ParentForm1, ParentForm2, ParentForm3


class ParentQuestionnaireWizard(SessionMultipleFormWizardView):
    form_list = [
        ("demographics", ParentForm1),
        ("education", (
            ('account', ParentForm2),
            ('address', ParentForm3)
        ))
    ]

    templates = {
        "start": 'demo/wizard-start.html',
        "user_info": 'demo/wizard-user_info.html'
    }

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def done(self, form_dict, **kwargs):
        result = {}

        for key in form_dict:
            form_collection = form_dict[key]
            if isinstance(form_collection, forms.Form):
                result[key] = form_collection.cleaned_data
            elif isinstance(form_collection, dict):
                result[key] = {}
                for subkey in form_collection:
                    result[key][subkey] = form_collection[subkey].cleaned_data

        return render_to_response('demo/wizard-end.html', {
            'form_data': result,
        })

############################################################################################

form = Wizard.as_view(form_list, instance_dict={
    'start': user,  # User model instance
    'user_info': {
        'account': Account.objects.get(user=user),
        'address': Address.objects.get(user=user),
    },
})