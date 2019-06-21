"""
********************************************************************************
* Name: param_widgets.py
* Author: Scott Christensen and Nathan Swain
* Created On: January 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import param
from django import forms
from datetimewidget.widgets import DateWidget
from django_select2.forms import Select2Widget
from taggit.forms import TagField
# from dataframewidget.forms.fields import DataFrameField


widget_map = {
    param.Foldername:
        lambda p, initial: forms.FilePathField(
            initial=initial or p.default,
        ),
    param.Boolean:
        lambda p, initial: forms.BooleanField(
            initial=initial or p.default,
        ),
    # param.Array: ,
    # param.Dynamic: ,
    param.Filename:
        lambda p, initial: forms.FileField(
            initial=initial or p.default,
        ),
    param.Dict:
        lambda p, initial: forms.CharField(
            initial=initial or p.default,
        ),
    param.XYCoordinates:
        lambda p, initial: forms.MultiValueField(
            initial=initial or p.default,
        ),
    param.Selector:
        lambda p, initial: forms.ChoiceField(
            initial=initial or p.default,
        ),
    # param.HookList,
    # param.Action: ,
    param.parameterized.String:
        lambda p, initial: forms.CharField(
            initial=initial or p.default,
        ),
    param.Magnitude:
        lambda p, initial: forms.FloatField(
            initial=initial or p.default,
        ),
    # param.Composite,
    param.Color:
        lambda p, initial: forms.CharField(
            initial=initial or p.default,
        ),
    param.ObjectSelector:
        lambda p, initial: forms.ChoiceField(
            initial=initial or p.default,
            widget=Select2Widget,
            choices=p.get_range().items(),
        ),
    param.Number:
        lambda p, initial: forms.FloatField(
            initial=initial or p.default,
        ),
    param.Range:
        lambda p, initial: forms.MultiValueField(
            initial=initial or p.default,
        ),
    param.NumericTuple:
        lambda p, initial: forms.MultiValueField(
            initial=initial or p.default,
        ),
    param.Date:
        lambda p, initial: forms.DateTimeField(
            initial=initial or p.default,
            widget=DateWidget(
                options={
                    'startDate': p.bounds[0].strftime(
                        '%Y-%m-%d') if p.bounds else '0000-01-01',  # start of supported time
                    'endDate': p.bounds[1].strftime(
                        '%Y-%m-%d') if p.bounds else '9999-12-31',  # end of supported time
                    'format': 'mm/dd/yyyy',
                    'autoclose': True,
                    # 'showMeridian': False,
                    'minView': 2,  # month view
                    'maxView': 4,  # 10-year overview
                    'todayBtn': 'true',
                    'clearBtn': True,
                    'todayHighlight': True,
                    'minuteStep': 5,
                    'pickerPosition': 'bottom-left',
                    'forceParse': 'true',
                    'keyboardNavigation': 'true',
                },
                bootstrap_version=3
            ),
        ),
    param.List:
        lambda p, initial: TagField(
            initial=initial or p.default,
        ),
    param.Path:
        lambda p, initial: forms.FilePathField(
            initial=initial or p.default,
        ),
    param.MultiFileSelector:
        lambda p, initial: forms.MultipleChoiceField(
            initial=initial or p.default,
        ),
    param.ClassSelector:
        lambda p, initial: forms.ChoiceField(
            initial=initial or p.default,
        ),
    param.FileSelector:
        lambda p, initial: forms.ChoiceField(
            initial=initial or p.default,
        ),
    param.ListSelector:
        lambda p, initial: forms.MultipleChoiceField(
            initial=initial or p.default,
        ),
    # param.Callable,
    param.Tuple:
        lambda p, initial: forms.MultiValueField(
            initial=initial or p.default,
        ),
    param.Integer:
        lambda p, initial: forms.IntegerField(
            initial=initial or p.default,
        ),
    # TODO: Implement DataFrameField someday...
    # param.DataFrame:
    #     lambda p, initial: DataFrameField(
    #         initial=initial is not None or p.default is not None
    #     )
}


def generate_django_form(parameterized_obj, set_options=None):
    """
    Create a Django form from a Parameterized object.

    Args:
        parameterized_obj(Parameterized): the parameterized object.
        set_options(dict<attrib_name, initial_value>): Dictionary of initial value for one or more fields.

    Returns:
        Form: a Django form with fields matching the parameters of the given parameterized object.
    """
    set_options = set_options or dict()
    class_name = '{}Form'.format(parameterized_obj.name.title())
    form_class = type(class_name, (forms.Form,), dict(forms.Form.__dict__))

    params = list(filter(lambda x: (x.precedence is None or x.precedence >= 0) and not x.constant,
                         parameterized_obj.params().values()))

    for p in sorted(params, key=lambda p: p.precedence or 9999):
        # TODO: Pass p.__dict__ as second argument instead of arbitrary
        form_class.base_fields[p._attrib_name] = widget_map[type(p)](p, set_options.get(p._attrib_name))
        form_class.base_fields[p._attrib_name].widget.attrs.update({'class': 'form-control'})

    return form_class
