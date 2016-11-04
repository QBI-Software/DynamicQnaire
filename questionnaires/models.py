from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.translation import ugettext_lazy as _
from colorfield.fields import ColorField

##### LISTS #############
class Category(models.Model):
    CATEGORIES = (('W1', 'Wave 1'), ('W2', 'Wave 2'), ('W3', 'Wave 3'))
    name = models.CharField(_("Name"), max_length=10,choices=CATEGORIES, default='W1')
    #code = models.CharField(_("Code"), max_length=5, unique=True)

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

    def categorylist(self):
        catlist = [c.get_name_display() for c in self.category.all()]
        print('DEBUG: Catlist=', catlist)
        return ", ".join(catlist)

    def num_questions(self):
        return self.question_set.count()

    def getNextOrder(self):
        return self.question_set.count()+1

    def __str__(self):
        return self.code + ": " + self.title


class Question(models.Model):
    INPUTS = ((1, 'Radio'), (2, 'Checkbox'), (3, 'Textfield'), (4, 'Dropdown'))
    CSSCLASSES = ((1, 'default'), (2, 'radiobox'))
    qid = models.ForeignKey(Questionnaire, verbose_name="Questionnaire", null=False)
    order = models.PositiveSmallIntegerField(_("Number"), default=0)
    question_required = models.BooleanField(_("Required"), default=True)
    question_text = models.CharField(_("Question Text"), max_length=200)
    question_image = models.ImageField(verbose_name="Question Image", null=True, blank=True)
    question_type = models.PositiveSmallIntegerField(_("Type"), default=1, choices=INPUTS)
    group = models.ManyToManyField(Group, verbose_name="Group", blank=True)
    skip_value = models.CharField(_("Conditional value"), max_length=20, blank=True, null=True)
    #skip_goto = models.PositiveSmallIntegerField(_("Skip to question"), blank=True, null=True)
    bgcolor = ColorField(_("Background Color"),default='#FFFFFF')
    textcolor = ColorField(_("Text Color"),default='#666666')
    css = models.PositiveSmallIntegerField(_("CSS class"), choices=CSSCLASSES, default=1)
    usegrid = models.BooleanField(_("Use Grid Layout"), default=False)

    def num_choices(self):
        return self.choice_set.count()

    def __str__(self):
        return self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_image = models.ImageField(verbose_name="Choice Image", null=True, blank=True)
    choice_text = models.CharField(_("Choice Text"), max_length=200, default="")
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
    test_result_text = models.CharField(verbose_name="FreeText", max_length=200, null=True)
    test_token = models.CharField(_("Hiddentoken"), max_length=100)

    def __str__(self):
        return self.test_questionnaire.title


class SubjectQuestionnaire(models.Model):
    """Manage questionnaires done per user - entered once per questionnaire - synch manually with TestResult"""
    subject = models.ForeignKey(User)
    questionnaire = models.ForeignKey(Questionnaire, null=False) #stored as questionnaire to facilitate delete/update
    date_stored = models.DateTimeField(auto_now=True) #relevant to Wave
    session_token = models.CharField(_("Hidden token"), max_length=100)

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
    date_visit = models.DateTimeField(verbose_name="Date of Visit", null=False)  # only one entry per visit
    icon = models.ImageField(verbose_name="Subject icon", null=True, blank=True)

    def __str__(self):
        return self.subject.username + ": " + self.category.name

############## Custom Classes ##############
class Demographic(models.Model):
    """ Capture demographic information for Parents and Twins """
    SUBJECTTYPES = ((1,'Parent'), (2,'Child'))
    MARITAL = ((1, 'Single (and have never been married)'),
               (2, 'Married or living with partner'),
               (3, 'In a relationship but not living with partner'),
               (4, 'Separated (but still legally married)'),
               (5, 'Divorced'),
               (6, 'Widowed'))
    PARENTAL = ((1, 'Biological parent'), (2, 'Non-biological parent'),
                (3, 'Other biological relative'), (4, 'Other'))
    GENDER = ((1, 'Male'), (2, 'Female'))
    AGERANGES = ((0,'Don’t know'),(1,'<20'),(2,'20-24'),(3,'25-29'),(4,'30-34'),(5,'35-39'),(6,'40-44'),(7,'45-49'),
                 (8,'50-54'),(9,'55-59'),(10,'≥60'))
    ABORIGINAL = ((1,"No"), (2,"Yes, Aboriginal"),(3,"Yes, Torres Strait Islander"),
                  (4,"Yes, both Aboriginal and Torres Strait Islander"),
                  (5,"Don't know"))
    LANGUAGES = ((0,"English"),(1,"Afrikaans"),(2,"Arabic"),(3,"Cantonese"),(4,"Croatian"),(5,"French"),(6,"German"),(7,"Greek"),
                 (8,"Hindi"),(9,"Italian"),(10,"Japanese"),(11,"Malaysian"),(12,"Mandarin"),(13,"Macedonian"),(14,"Polish"),
                 (15,"Serbian"),(16,"Spanish"),(17,"Tagalog/ Filipino"),(18,"Turkish"),(19,"Vietnamese"),(20,"Other (specify)"),(21,"Don’t know"))
    subject = models.OneToOneField(User, verbose_name="Subject")
    subjecttype = models.PositiveSmallIntegerField(_("Type"), choices=SUBJECTTYPES)
    dob = models.DateField(_("Date of Birth"), null=True)
    maiden = models.CharField(_("Maiden Name"), max_length=200, null=True)
    gender = models.PositiveSmallIntegerField(_("Gender"), choices=GENDER)
    marital_status  = models.PositiveSmallIntegerField(_("Marital status"), choices=MARITAL)
    parental_status = models.PositiveSmallIntegerField(_("Parental status"), choices=PARENTAL)
    parental_status_other = models.CharField(_("Parent status - Other"), max_length=200, null=True)
    agerange_twinborn = models.CharField(_("Age when twins born"), max_length=200, null=True, choices=AGERANGES)
    country_birth = models.CharField(_("Country of birth"), max_length=200, null=True)
    aboriginal = models.PositiveSmallIntegerField(_("Aboriginal or Torres Strait Islander"), null=True, choices=ABORIGINAL)
    language = models.PositiveSmallIntegerField(_("Language"), choices=LANGUAGES, default=0)
    language_other = models.CharField(_("Other Language"), max_length=200, null=True)
