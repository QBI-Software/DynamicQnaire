from ckeditor_uploader.fields import RichTextUploadingField
from colorfield.fields import ColorField
from django.contrib.auth.models import User, Group
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext_lazy as _

##### DEFAULT COLORS ############################
BGDEFAULT='#FFFFFF'
TCDEFAULT='#212121'
##### LISTS #############
class Category(models.Model):
    CATEGORIES = (('W1', 'Wave 1'), ('W2', 'Wave 2'), ('W3', 'Wave 3'), ('W4', 'Wave 4'))
    name = models.CharField(_("Name"), max_length=10,choices=CATEGORIES, default='W1')

    def code(self):
        return self.name[1]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


##### CLASSES ############
class Questionnaire(models.Model):

    TYPES=(('multi','Multi Page' ),('single','Single Page' ),('custom','Custom'))
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"), null=True, blank=True)
    intropage = RichTextUploadingField(_("Introduction"),null=True, blank=True)
    code = models.CharField(_("Code"), max_length=10, unique=True)
    category = models.ManyToManyField(Category, verbose_name="Visit Category")
    type = models.CharField(_("Type"), max_length=20, choices=TYPES, default='multi')
    group = models.ManyToManyField(Group)
    active = models.BooleanField(_("Active"), default=True)
    bgcolor = ColorField(_("Background Color"), default=BGDEFAULT)
    textcolor = ColorField(_("Text Color"), default=TCDEFAULT)
    order = models.IntegerField(_("Order"), default=1, null=True, blank=False)

    def categorylist(self):
        catlist = [c.get_name_display() for c in self.category.all()]
        return " ".join(catlist)

    def num_questions(self):
        return self.question_set.count()

    def getNextOrder(self):
        return self.question_set.count()+1

    def __str__(self):
        return self.code + ": " + self.title


class Question(models.Model):
    """
    Main model for question information
    Conditionals is optional but must match views.load_questionnaire [conditional_actions] and be implemented by views.QuestionnaireWizard process_step
    """
    INPUTS = ((1, 'Radio'), (2, 'Checkbox'), (3, 'Textfield'), (4, 'Dropdown'), (5,'Date'), (6,'Slider'))
    CSSCLASSES = ((1, 'default'), (2, 'coloredbox'), (3, 'coloredbox_sm'))
    CONDITIONALS = ((0,'None'),
                    (1,'Show next only if this value is <value>'),
                    (2,'Skip next <skip> qns if this value is <value>'),
                    (3,'Skip next <skip> qns if this value is more than <value>'),
                    (4,'Skip next <skip> qns if this value is less than <value>'),
                    (5,'Show checked only [values=order start at 0]'))
    qid = models.ForeignKey(Questionnaire, verbose_name="Questionnaire", null=False)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)
    conditional = models.PositiveSmallIntegerField(_("Conditional"), default=0, choices=CONDITIONALS)
    condval = models.PositiveSmallIntegerField(_("Conditional value"), default=0)
    condskip = models.PositiveSmallIntegerField(_("Conditional skip"), default=0)
    question_required = models.BooleanField(_("Required"), default=True)
    question_text = models.CharField(_("Question Text"), max_length=500)
    question_image = models.ImageField(verbose_name="Question Image", null=True, blank=True)
    question_type = models.PositiveSmallIntegerField(_("Type"), default=1, choices=INPUTS)
    group = models.ManyToManyField(Group, verbose_name="Group", blank=True)
    bgcolor = ColorField(_("Background Color"),default=BGDEFAULT)
    textcolor = ColorField(_("Text Color"),default=TCDEFAULT)
    css = models.PositiveSmallIntegerField(_("CSS class"), choices=CSSCLASSES, default=1)
    usegrid = models.BooleanField(_("Use Grid Layout"), default=False)
    gridcols = models.PositiveSmallIntegerField(_("Number Columns in Grid Layout"), default=3, null=True, blank=True,validators=[ MaxValueValidator(5),  MinValueValidator(1)])
    duplicate = models.BooleanField(_("Duplicate answers"), default=False)
    question_description = RichTextUploadingField(_("Description"), null=True, blank=True)

    def num_choices(self):
        return self.choice_set.count()

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_image = models.ImageField(verbose_name="Choice Image", null=True, blank=True)
    choice_text = models.TextField(_("Choice Text"), max_length=5000, default="")
    choice_value = models.CharField(_("Value"),default='0', max_length=20)
    show_label = models.BooleanField(_("Show label"), default=True)
    group = models.ManyToManyField(Group, verbose_name="Group", blank=True)

    def questionnaire(self):
        return self.question.qid

    def __str__(self):
       return self.choice_text


class TestResult(models.Model):
    """Stores result of each question or multiple entries for multi-select"""
    testee = models.ForeignKey(User)
    test_datetime = models.DateTimeField(verbose_name="Test Datetime", auto_now=True)
    test_questionnaire = models.ForeignKey(Questionnaire, verbose_name="Questionnaire", null=False)
    test_result_question = models.ForeignKey(Question,verbose_name="Question", null=False)
    test_result_choice = models.ForeignKey(Choice, verbose_name="Choice", null=True)
    test_result_text = models.TextField(verbose_name="FreeText", max_length=5000, null=True)
    test_result_date = models.DateField(_("Date"), null=True)
    test_token = models.CharField(_("Hiddentoken"), max_length=100)

    def __str__(self):
        return self.test_questionnaire.title


class SubjectQuestionnaire(models.Model):
    """Manage questionnaires done per user - entered once per questionnaire - synch manually with TestResult"""
    subject = models.ForeignKey(User)
    questionnaire = models.ForeignKey(Questionnaire, null=False) #stored as questionnaire to facilitate delete/update
    date_stored = models.DateTimeField(auto_now=True) #relevant to Wave
    session_token = models.CharField(_("Hidden token"), max_length=100)
    start = models.DateTimeField(verbose_name="Start time", auto_now=False, null=True)

    def duration(self):
        return self.date_stored - self.start

    def __str__(self):
        return self.subject.username + ": " + self.questionnaire.title


class SubjectVisit(models.Model):
    """One Visit for user - managed by Admin per visit"""
    subject = models.OneToOneField(User, verbose_name="Subject")
    twin = models.OneToOneField(User, verbose_name="Twin", null=True, blank=True, related_name="twin")
    parent1 = models.ForeignKey(User, verbose_name="Parent 1", null=True, blank=True, related_name="parent1")
    parent2 = models.ForeignKey(User, verbose_name="Parent 2", null=True, blank=True, related_name="parent2")
    xnatid = models.CharField(_("XNAT ID"), null=True, blank=True,max_length=20, unique=True)
    category = models.ForeignKey(Category,verbose_name="Wave",) #ie Wave number
    date_visit = models.DateTimeField(_("Date of Visit"), null=False)  # only one entry per visit
    icon = models.ImageField(_("Subject icon"), null=True, blank=True)
    gender = models.PositiveSmallIntegerField(_("Gender"), null=False, default=0, choices=((0,'Unknown'),(1, 'Male'), (2, 'Female')))
    is_parent = models.BooleanField(_("Is Parent"), default=False)

    def __str__(self):
        return self.subject.username + ": " + self.category.name

    # Only for parent user
    def get_twins(self):
        twins = None
        if self.is_parent:
            twins = SubjectVisit.objects.filter(parent1=self.subject) | SubjectVisit.objects.filter(parent2=self.subject)
        return twins

    def has_mm(self):
        genders = []
        test = [1,1]
        if self.is_parent:
            genders = [twin.gender for twin in self.get_twins()]
        return (genders == test)

    def has_ff(self):
        genders = []
        test = [2,2]
        if self.is_parent:
            genders = [twin.gender for twin in self.get_twins()]
        return (genders == test)

    def has_mf(self):
        genders = []
        test = [1, 2]
        if self.is_parent:
            genders = [twin.gender for twin in self.get_twins()]
        return (sorted(genders) == test)

