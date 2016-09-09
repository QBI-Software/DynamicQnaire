from django.db import models
from django.core import urlresolvers
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
class Questionnaire(models.Model):
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), null=True, blank=True)
    code = models.CharField(_("Code"), max_length=10, unique=True)
    category = models.ForeignKey(Category, verbose_name="Category")

    def __str__(self):
        return self.code + ": " + self.title

class Question(models.Model):
    qid = models.ForeignKey(Questionnaire, verbose_name="Questionnaire", null=False)
    question_text = models.CharField(_("Question Text"), max_length=200)
    question_image = models.ImageField(verbose_name="Question Image", null=True, blank=True)
    order = models.IntegerField(_("Sequence Order"), default=0)

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(_("Choice Text"), max_length=200)
    choice_value = models.IntegerField(_("Value"),default=0)

    def __str__(self):
        return self.choice_text


