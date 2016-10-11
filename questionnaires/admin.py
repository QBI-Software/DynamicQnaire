from django.contrib import admin
from .models import Questionnaire, Question, Choice, Category


## Bulk Admin Actions

#TODO: Results: List of results per questionnaire and with percentage total and paginate
#TODO: Results: Export raw results as csv

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
               'create_5number',
               'create_7number']



    def create_radiobuttons(self,request,queryset,labels):
        for obj in queryset:
            print(obj)
            num = obj.choice_set.count() + 1
            for label in labels:
                ch = Choice(question=obj, choice_text=label, choice_value=num)
                ch.save()
                num += 1

    def create_true(self, request, queryset):
        labels = ["Not True", "Somewhat True", "True"]
        self.create_radiobuttons(request,queryset,labels)

    def create_yesnosometimes(self, request, queryset):
        labels = ["Yes", "No", "Sometimes","Don't know"]
        self.create_radiobuttons(request, queryset, labels)

    def create_never_always(self, request, queryset):
        labels = ["Never", "Sometimes", "Often","Always"]
        self.create_radiobuttons(request, queryset, labels)

    def create_5number(self, request, queryset):
        labels = ["1", "2", "3", "4", "5","NA"]
        self.create_radiobuttons(request, queryset, labels)

    def create_7number(self, request, queryset):
        labels = ["1", "2", "3", "4", "5","6","7"]
        self.create_radiobuttons(request, queryset, labels)

    create_true.short_description = "Create 'True' Options"
    create_yesnosometimes.short_description = "Create 'Yes/No/Sometimes/Don\'t know' Options"
    create_never_always.short_description = "Create 'Never - Always' Options"
    create_5number.short_description ="Create range '1 to 5' options"
    create_7number.short_description = "Create range '1 to 7' options"

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3

#TODO: Use CKeditor for intropage field
class QuestionnaireAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title','description', 'intropage','group','code','category', 'type']}),
    ]
    inlines = [QuestionInline]
    list_display = ('title','description','code','category', 'type','num_questions')
    list_filter = ['category','type']
    search_fields = ['title']
    actions=['sequence_questions']

    def sequence_questions(self,request,queryset):
        """ Generate order sequences for questions in set of questionnaires - will reset existing """
        for obj in queryset:
            qnlist = obj.question_set.order_by('pk').order_by('order')
            #total = qnlist.count()
            num = 1
            for q in qnlist:
                q.order=num
                q.save()
                num += 1
            print('AdminBulkMethod:Updated ',num, 'questions in ',obj)

    sequence_questions.short_description = 'Generate order sequences for questions'
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "car":
    #         kwargs["queryset"] = Question.objects.filter(owner=request.user)
    #     return super(QuestionnaireAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Category)