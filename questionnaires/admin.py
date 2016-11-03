from django.contrib import admin
#from suit.widgets import HTML5Input
from .models import Questionnaire, Question, Choice, SubjectVisit, Category


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('questionnaire','question','choice_text','choice_image','choice_value')
    #list_filter =['choice_type']

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3



class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['question_text']}),
    ]
    inlines = [ChoiceInline]
    list_display = ('qid','question_text', 'question_image','order','num_choices','question_type')
    list_filter = ['group','question_type']
    search_fields = ['question_text']
    actions = ['create_true',
               'create_yesnosometimes',
               'create_never_always',
               'create_never_often',
               'create_5number',
               'create_7number',
               'create_9number']


    def create_radiobuttons(self,request,queryset,labels):
        for obj in queryset:
            #Clear previous choices
            print(obj)
            for c in obj.choice_set.all():
                c.delete()
            num = 1
            for label in labels:
                ch = Choice(question=obj, choice_text=label, choice_value=num)
                ch.save()
                num += 1
        msg = 'Questions have been CREATED for selected questionnaires'
        self.message_user(request, msg)

    def create_true(self, request, queryset):
        labels = ["Not True", "Somewhat True", "True"]
        self.create_radiobuttons(request,queryset,labels)

    def create_yesnosometimes(self, request, queryset):
        labels = ["Yes", "No", "Sometimes","Don't know"]
        self.create_radiobuttons(request, queryset, labels)

    def create_never_always(self, request, queryset):
        labels = ["Never", "Sometimes", "Often","Always"]
        self.create_radiobuttons(request, queryset, labels)

    def create_never_often(self, request, queryset):
        labels = ["Never", "Rarely", "Occasionally","Often","Very Often","Not Applicable"]
        self.create_radiobuttons(request, queryset, labels)

    def create_5number(self, request, queryset):
        labels = ["1", "2", "3", "4", "5","NA"]
        self.create_radiobuttons(request, queryset, labels)

    def create_7number(self, request, queryset):
        labels = ["1", "2", "3", "4", "5","6","7"]
        self.create_radiobuttons(request, queryset, labels)

    def create_9number(self, request, queryset):
        labels = ["1", "2", "3", "4", "5", "6", "7","8","9"]
        self.create_radiobuttons(request, queryset, labels)

    create_true.short_description = "Create 'True' Options"
    create_yesnosometimes.short_description = "Create 'Yes/No/Sometimes/Don\'t know' Options"
    create_never_always.short_description = "Create 'Never - Always' Options"
    create_never_often.short_description = "Create 'Never - Often' Options"
    create_5number.short_description ="Create range '1 to 5' with NA options"
    create_7number.short_description = "Create range '1 to 7' options"
    create_9number.short_description = "Create range '1 to 9' options"

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3



class QuestionnaireAdmin(admin.ModelAdmin):

    fieldsets = [
        (None, {'fields': ['title','active','description', 'intropage','code','type','category','group']}),
    ]
    inlines = [QuestionInline]
    list_display = ('title','description','code','type','active','categorylist','num_questions')
    list_filter = ['type','active']
    search_fields = ['title']
    actions=['sequence_questions','remove_questionnaire_results']

    def sequence_questions(self,request,queryset):
        """ Generate order sequences for questions in set of questionnaires - will reset existing """

        for obj in queryset:
            qnlist = obj.question_set.order_by('pk')
            #total = qnlist.count()
            num = 1
            for q in qnlist:
                q.order=num
                q.save()
                num += 1
        msg = 'Questions have been ordered for selected questionnaires'
        self.message_user(request, msg)

    def remove_questionnaire_results(self, request,queryset):
        """ Delete all result sets for selected questionnaires """
        n = 0
        for obj in queryset:
            print("DEBUG: Questionnaire ", obj, " results to delete=", obj.testresult_set.count())
            n0 = obj.testresult_set.delete()
            obj.subjectquestionnaire_set.delete()
            n = n+ n0
        msg = "%d result sets successfully REMOVED from selected questionnaires." % n
        self.message_user(request, msg)


    sequence_questions.short_description = 'Number all questions'
    remove_questionnaire_results.short_description = 'Remove questionnaire results'

class SubjectVisitAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['date_visit', 'subject', 'category', 'xnatid','parent1','parent2','twin','icon']}),
    ]
    list_display = ( 'subject','category', 'date_visit', 'xnatid','parent1','parent2','twin','icon')
    list_filter = ['category']
    search_fields = ['subject__username']

admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(SubjectVisit,SubjectVisitAdmin)
#admin.site.register(Category)