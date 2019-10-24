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
        lambda po, p, name: forms.FilePathField(
            initial=po.inspect_value(name) or p.default,
            path=p.search_paths,
        ),
    param.Boolean:
        lambda po, p, name: forms.BooleanField(
            initial=po.inspect_value(name) or p.default, required=False
        ),
    # param.Array: ,
    # param.Dynamic: ,
    param.Filename:
        lambda po, p, name: forms.FileField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.Dict:
        lambda po, p, name: forms.CharField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.XYCoordinates:
        lambda po, p, name: forms.MultiValueField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.Selector:
        lambda po, p, name: forms.ChoiceField(
            initial=po.inspect_value(name) or p.default,
        ),
    # param.HookList,
    # param.Action: ,
    param.parameterized.String:
        lambda po, p, name: forms.CharField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.Magnitude:
        lambda po, p, name: forms.FloatField(
            initial=po.inspect_value(name) or p.default,
        ),
    # param.Composite,
    param.Color:
        lambda po, p, name: forms.CharField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.ObjectSelector:
        lambda po, p, name: forms.ChoiceField(
            initial=po.inspect_value(name) or p.default,
            widget=Select2Widget,
            choices=p.get_range().items(),
        ),
    param.Number:
        lambda po, p, name: forms.FloatField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.Range:
        lambda po, p, name: forms.MultiValueField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.NumericTuple:
        lambda po, p, name: forms.MultiValueField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.Date:
        lambda po, p, name: forms.DateTimeField(
            initial=po.inspect_value(name) or p.default,
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
        lambda po, p, name: TagField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.Path:
        lambda po, p, name: forms.FilePathField(
            initial=po.inspect_value(name) or p.default,
            path=p.search_paths,
        ),
    param.MultiFileSelector:
        lambda po, p, name: forms.MultipleChoiceField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.ClassSelector:
        lambda po, p, name: forms.ChoiceField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.FileSelector:
        lambda po, p, name: forms.ChoiceField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.ListSelector:
        lambda po, p, name: forms.MultipleChoiceField(
            initial=po.inspect_value(name) or p.default,
        ),
    # param.Callable,
    param.Tuple:
        lambda po, p, name: forms.MultiValueField(
            initial=po.inspect_value(name) or p.default,
        ),
    param.Integer:
        lambda po, p, name: forms.IntegerField(
            initial=po.inspect_value(name) or p.default,
        ),
    # TODO: Implement DataFrameField someday...
    # param.DataFrame:
    #     lambda po, p, name: DataFrameField(
    #         initial=po.inspect_value(name) is not None or p.default is not None
    #     )
}

widget_converter = {

}


def generate_django_form(parameterized_obj, set_options=None, form_field_prefix=None):
    """
    Create a Django form from a Parameterized object.

    Args:
        parameterized_obj(Parameterized): the parameterized object.
        set_options(dict<attrib_name, initial_value>): Dictionary of initial value for one or more fields.
        form_field_prefix(str): A prefix to prepend to form fields
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
        p_name = p.name
        if form_field_prefix is not None:
            p_name = form_field_prefix + p_name
        form_class.base_fields[p_name] = widget_map[type(p)](parameterized_obj, p, p.name)
        form_class.base_fields[p_name].label = p.name.capitalize()
        form_class.base_fields[p_name].widget.attrs.update({'class': 'form-control'})

    return form_class
