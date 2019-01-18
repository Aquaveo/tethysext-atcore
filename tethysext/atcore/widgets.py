"""
********************************************************************************
* Name: widgets.py
* Author: nswain
* Created On: January 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import param
from django import forms
from tethys_sdk.gizmos import SelectInput
from datetimewidget.widgets import DateWidget
from django_select2.forms import Select2Widget
from taggit.forms import TagField


class ConditionalSelectWidget(forms.widgets.Select):
    template_name = 'conditional_input.html'

    def __init__(self, forms, **kwargs):
        self.forms = forms
        super(ConditionalSelectWidget, self).__init__(**kwargs)

    def get_context(self, name, value, attrs):
        context = super(ConditionalSelectWidget, self).get_context(name, value, attrs)

        select_options = SelectInput(
            name=name,
            display_text='select',
            options=[(option, option) for option in self.forms.keys()],
        )

        context['select_options'] = select_options
        context['forms'] = self.forms

        return context


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
            widget=DateWidget(options={
                'startDate': p.bounds[0].strftime('%Y-%m-%d') if p.bounds else '0000-01-01',  # start of supported time
                'endDate': p.bounds[1].strftime('%Y-%m-%d') if p.bounds else '9999-12-31',  # the end of supported time
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
        )
}


def widgets(paramitarized_obj, set_options):
    class_name = '{}Form'.format(paramitarized_obj.name.title())
    form_class = type(class_name, (forms.Form,), dict(forms.Form.__dict__))

    params = list(filter(lambda x: (x.precedence is None or x.precedence >= 0) and not x.constant,
                         paramitarized_obj.params().values()))

    for p in sorted(params, key=lambda p: p.precedence or 9999):
        form_class.base_fields[p._attrib_name] = widget_map[type(p)](p, set_options.get(p._attrib_name))
        form_class.base_fields[p._attrib_name].widget.attrs.update({'class': 'form-control'})

    return form_class


# WIP: attempt at handling conditional widgets
def widgets_form(paramitarized_obj_dict, set_options):

    form_classes = {}

    for name, paramitarized_obj in paramitarized_obj_dict.items():
        form_class = widgets(paramitarized_obj, set_options)
        form_classes[name] = form_class

    if len(form_classes) > 1:
        class_name = '{}Form'.format('Conditional')
        form_class = type(class_name, (forms.Form,), dict(forms.Form.__dict__))
        choices = [(p, p) for p in form_classes.keys()]
        form_class.base_fields['condition'] = forms.ChoiceField(
                                                choices=choices,
                                                widget=ConditionalSelectWidget(
                                                    forms=form_classes,
                                                    attrs={'class': 'form-control'})
                                              )
        # form_class.media = lambda: [f.media for f in form_classes.values()]

    return form_class
