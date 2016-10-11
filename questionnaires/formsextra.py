from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.datastructures import MultiValueDict

CommaSep = ','


class SelectCommaWidget(CheckboxSelectMultiple):
    def value_from_datadict(self, data, name):
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        retval = data.get(name)
        if isinstance(retval, type('')):
            retval = retval.split(CommaSep)
        return retval


class MultipleChoiceCommaField(forms.MultipleChoiceField):
    """
    MultipleChoiceCommaField will return the value sequence as a
    single string, comma-separated.  This could easily generalized
    to a use a specified delimiter other than the comma.

    # >>> Choices = (('1','almonds'), ('2','pecans'), ('3','cashews'), ('4','walnuts'), ('5','peanuts'))
    # >>> class NutForm(forms.Form):
    # ...     nuts = MultipleChoiceCommaField(required=False, choices=Choices)
    # ...
    #
    # >>> print NutForm({})
    # <tr><th><label for="id_nuts_0">Nuts:</label></th><td><ul>
    # <li><label><input type="checkbox" name="nuts" value="1" id="id_nuts_0" /> almonds</label></li>
    # <li><label><input type="checkbox" name="nuts" value="2" id="id_nuts_1" /> pecans</label></li>
    # <li><label><input type="checkbox" name="nuts" value="3" id="id_nuts_2" /> cashews</label></li>
    # <li><label><input type="checkbox" name="nuts" value="4" id="id_nuts_3" /> walnuts</label></li>
    # <li><label><input type="checkbox" name="nuts" value="5" id="id_nuts_4" /> peanuts</label></li>
    # </ul></td></tr>
    #
    # >>> print NutForm({'nuts':'3'})
    # <tr><th><label for="id_nuts_0">Nuts:</label></th><td><ul>
    # <li><label><input type="checkbox" name="nuts" value="1" id="id_nuts_0" /> almonds</label></li>
    # <li><label><input type="checkbox" name="nuts" value="2" id="id_nuts_1" /> pecans</label></li>
    # <li><label><input checked="checked" type="checkbox" name="nuts" value="3" id="id_nuts_2" /> cashews</label></li>
    # <li><label><input type="checkbox" name="nuts" value="4" id="id_nuts_3" /> walnuts</label></li>
    # <li><label><input type="checkbox" name="nuts" value="5" id="id_nuts_4" /> peanuts</label></li>
    # </ul></td></tr>
    #
    # >>> print NutForm({'nuts':'2,4'})
    # <tr><th><label for="id_nuts_0">Nuts:</label></th><td><ul>
    # <li><label><input type="checkbox" name="nuts" value="1" id="id_nuts_0" /> almonds</label></li>
    # <li><label><input checked="checked" type="checkbox" name="nuts" value="2" id="id_nuts_1" /> pecans</label></li>
    # <li><label><input type="checkbox" name="nuts" value="3" id="id_nuts_2" /> cashews</label></li>
    # <li><label><input checked="checked" type="checkbox" name="nuts" value="4" id="id_nuts_3" /> walnuts</label></li>
    # <li><label><input type="checkbox" name="nuts" value="5" id="id_nuts_4" /> peanuts</label></li>
    # </ul></td></tr>
    # >>>
    """

    def __init__(self, **kwargs):
        if not 'widget' in kwargs:
            kwargs['widget'] = SelectCommaWidget
        super(forms.MultipleChoiceField, self).__init__(**kwargs)

    def clean(self, value):
        # The following lines are here to work around ticket #3482.  When the
        # ticket is fixed uncomment the next line and remove the remainder.
        # return CommaSep.join(super(MultipleChoiceCommaField, self).clean(value))
        v = super(MultipleChoiceCommaField, self).clean(value)
        if v == ['']:
            return []
        else:
            return CommaSep.join(v)


if __name__ == '__main__':
    import doctest

    doctest.testmod()