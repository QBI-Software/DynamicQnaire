from django.contrib import admin
from .models import Questionnaire, Question, Choice, Category

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3

class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['question_text']}),
    ]
    inlines = [ChoiceInline]
    search_fields = ['question_text']

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3




class QuestionnaireAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['title','description', 'code','category']}),
    ]
    inlines = [QuestionInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "car":
            kwargs["queryset"] = Question.objects.filter(owner=request.user)
        return super(QuestionnaireAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Questionnaire, QuestionnaireAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Category)