from django.db import models
from django.core import urlresolvers
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

##### LISTS #############
class Category(models.Model):
    name = models.CharField(_("Name"), max_length=60)
    code = models.CharField(_("Code"), max_length=5, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


##### CLASSES ############
TYPES=(('single','Single Page' ),('multi','Multi Page' ))
class Questionnaire(models.Model):
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), null=True, blank=True)
    intropage = models.TextField(_("Introduction"),null=True,blank=True)
    code = models.CharField(_("Code"), max_length=10, unique=True)
    category = models.ForeignKey(Category, verbose_name="Category")
    type = models.CharField(_("Type"), max_length=20, choices=TYPES, default='single')
    group = models.ManyToManyField(Group)

    def __str__(self):
        return self.code + ": " + self.title

class Question(models.Model):
    qid = models.ForeignKey(Questionnaire, verbose_name="Questionnaire", null=False)
    question_text = models.CharField(_("Question Text"), max_length=200)
    question_image = models.ImageField(verbose_name="Question Image", null=True, blank=True)
    order = models.IntegerField(_("Sequence Order"), default=0)
    group = models.ManyToManyField(Group, verbose_name="Group", blank=True)

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_image = models.ImageField(verbose_name="Choice Image", null=True, blank=True)
    choice_text = models.CharField(_("Choice Text"), max_length=200)
    choice_value = models.IntegerField(_("Value"),default=0)
    group = models.ManyToManyField(Group, verbose_name="Group", blank=True)

    def __str__(self):
       return self.choice_text

class TestResult(models.Model):
    testee = models.ForeignKey(User)
    test_datetime = models.DateTimeField(verbose_name="Test Datetime", auto_now=True)
    test_questionnaire = models.ForeignKey(Questionnaire, verbose_name="Questionnaire", null=False)
    test_result_question=models.ForeignKey(Question,verbose_name="Question", null=False)
    test_result_choice=models.ForeignKey(Choice, verbose_name="Choice", null=False)
    test_token = models.CharField(_("Hiddentoken"), max_length=100)

    def __str__(self):
        return self.test_questionnaire.title