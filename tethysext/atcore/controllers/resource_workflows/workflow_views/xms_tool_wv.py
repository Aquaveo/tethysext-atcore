"""
********************************************************************************
* Name: xms_tool_wv.py
* Author: dgallup
* Created On: December, 2023
* Copyright: (c) Aquaveo 2023
********************************************************************************
"""
import logging
import re

from django import forms
from django_select2.forms import Select2Widget

from tethysext.atcore.controllers.resource_workflows.workflow_view import ResourceWorkflowView
from tethysext.atcore.models.resource_workflow_steps.xms_tool_rws import XMSToolRWS

# from bokeh.embed import server_document

log = logging.getLogger(f'tethys.{__name__}')


def _build_selector_field(info):
    return forms.ChoiceField(
        initial=info['value'],
        widget=Select2Widget,
        choices=info['choices'],
    )


xmstool_widget_map = {
    'Boolean': lambda info: forms.BooleanField(initial=info['value'], required=False),
    'String': lambda info: forms.CharField(initial=info['value']),
    'Number': lambda info: forms.FloatField(initial=info['value']),
    'Integer': lambda info: forms.IntegerField(initial=info['value']),
    'ObjectSelector': _build_selector_field,
    'StringSelector': _build_selector_field,
}


def _default_setup_args(arguments):
    """Takes the XMSToolArgument list and turns it into a dictionary of Param types.

    Args:
        arguments (List[Argument]): List of tool arguments.

    Returns:
        (Dict[str, Parameter]): List of Parameter objects.
    """
    arguments_dict = {}
    for argument in arguments:
        interface_info = argument.get_interface_info()
        if interface_info['value'] is not None:
            interface_info['value'] = argument.value
        if argument.io_direction == 2 and argument.type in ['integer', 'float', 'string']:
            continue
        arguments_dict[argument.name] = interface_info
    return arguments_dict


class XMSToolWV(ResourceWorkflowView):
    """
    Controller for XMSToolRWS.
    """
    template_name = 'atcore/resource_workflows/form_input_wv.html'
    valid_step_classes = [XMSToolRWS]

    def process_step_options(self, request, session, context, resource, current_step, previous_step, next_step):
        """
        Hook for processing step options (i.e.: modify map or context based on step options).

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            context(dict): Context object for the map view template.
            resource(Resource): the resource for this request.
            current_step(ResourceWorkflowStep): The current step to be rendered.
            previous_step(ResourceWorkflowStep): The previous step.
            next_step(ResourceWorkflowStep): The next step.
        """
        # Status style
        form_title = current_step.options.get('form_title', current_step.name) or current_step.name
        form_values = current_step.get_parameter('form-values')

        current_step.options.pop('param_class', None)
        package, p_class = current_step.options['xmstool_class'].rsplit('.', 1)
        arg_mapping = current_step.options['arg_mapping']
        mod = __import__(package, fromlist=[p_class])
        XMSToolClass = getattr(mod, p_class)

        # Get the renderer option
        renderer = current_step.options['renderer']
        context.update({'renderer': renderer})

        # Django Renderer
        if renderer == 'django':
            tool = XMSToolClass()
            form = generate_django_form_xmstool(tool, form_values, resource=resource,
                                                form_field_prefix='param-form-',
                                                read_only=self.is_read_only(request, current_step),
                                                arg_mapping=arg_mapping)()

            # Save changes to map view and layer groups
            context.update({
                'read_only': self.is_read_only(request, current_step),
                'form_title': form_title,
                'form': form,
            })

    def process_step_data(self, request, session, step, resource, current_url, previous_url, next_url):
        """
        Hook for processing user input data coming from the map view. Process form data found in request.POST and request.GET parameters and then return a redirect response to one of the given URLs. Only called if the user has an active role.

        Args:
            request(HttpRequest): The request.
            session(sqlalchemy.orm.Session): Session bound to the steps.
            step(ResourceWorkflowStep): The step to be updated.
            resource(Resource): the resource for this request.
            current_url(str): URL to step.
            previous_url(str): URL to the previous step.
            next_url(str): URL to the next step.

        Returns:
            HttpResponse: A Django response.
        """  # noqa: E501
        step.options.pop('param_class', None)
        package, p_class = step.options['xmstool_class'].rsplit('.', 1)
        arg_mapping = step.options['arg_mapping']
        mod = __import__(package, fromlist=[p_class])
        XMSToolClass = getattr(mod, p_class)
        form_values = step.get_parameter('form-values')
        if step.options['renderer'] == 'django':
            tool = XMSToolClass()
            form = generate_django_form_xmstool(tool, form_values, resource=resource,
                                                form_field_prefix='param-form-',
                                                arg_mapping=arg_mapping)(request.POST)
            form_values = {}

            if not form.is_valid():
                raise RuntimeError('form is invalid')

            # Get the form from the post
            # loop through items and set the params
            for p in request.POST:
                if p.startswith('param-form-'):
                    try:
                        param_name = p[11:]
                        form_values[param_name] = form.cleaned_data[p]
                    except ValueError as e:
                        raise RuntimeError('error setting param data: {}'.format(e))

            step.set_parameter('resource_name', step.workflow.resource.name)
            temp_values = step.get_parameter('form-values')
            temp_values['value'] = form_values
            step.set_parameter('form-values', temp_values)

        # Save parameters
        session.commit()

        # Validate the parameters
        step.validate()

        # Set the status
        step.set_status(status=step.STATUS_COMPLETE)
        session.commit()

        response = super().process_step_data(
            request=request,
            session=session,
            step=step,
            resource=resource,
            current_url=current_url,
            previous_url=previous_url,
            next_url=next_url
        )

        return response


def _build_choices_from_resource(resource, arg_atts):
    """Build (value, label) choices for a mapped argument by reading resource datasets."""
    datasets = getattr(resource, arg_atts['resource_attr'])
    if not isinstance(datasets, list):
        datasets = [datasets]

    choices = []
    for dataset in datasets:
        if getattr(dataset, arg_atts['filter_attr']) not in arg_atts['valid_values']:
            continue
        label = getattr(dataset, arg_atts['name_attr'])
        if 'name_attr_regex' in arg_atts:
            # Perform a regex on the name attribute to filter the name
            match = re.findall(arg_atts['name_attr_regex'], label)
            label = match[0] if match else label
        choices.append((str(dataset.id), label))  # (value, label)
    return choices


def generate_django_form_xmstool(xms_tool_class, form_values, resource=None, form_field_prefix=None,
                                 read_only=False, arg_mapping=None, setup_func=None):
    """
    Create a Django form from a Parameterized object.

    Args:
        xms_tool_class(class): the XMS tool class.
        form_values(dict): dict of initial values to assign
        form_field_prefix(str): A prefix to prepend to form fields
        read_only(bool): Read only flag
        arg_mapping(dict): Dictionary to map particular arguments to available resources
    Returns:
        Form: a Django form with fields matching the parameters of the given parameterized object.
    """

    tool_arguments = xms_tool_class.initial_arguments()
    input_arg_names = {a.name for a in tool_arguments if a.io_direction == 1}
    argument_params = (setup_func or _default_setup_args)(tool_arguments)

    # Create Django Form class dynamically
    class_name = '{}Form'.format(xms_tool_class.name.title()).replace(' ', '')
    form_class = type(class_name, (forms.Form,), {})

    resource_choices = {}
    if resource and arg_mapping:
        for arg_name, arg_atts in arg_mapping.items():
            if arg_name in argument_params:
                resource_choices[arg_name] = _build_choices_from_resource(resource, arg_atts)

    # Fill in form values if necessary
    if form_values:
        for values in form_values.values():
            for param_name, param_info in argument_params.items():
                if param_name in values:
                    param_info['value'] = values[param_name]

    for param_name, param_info in argument_params.items():
        # Assign any initial arguments if found from argument mapping for input arguments
        if param_name in input_arg_names and param_name in resource_choices:
            param_info['choices'] = resource_choices[param_name]

        # Prefix parameter name if prefix provided
        field_name = (form_field_prefix or '') + param_name

        # Get appropriate Django field/widget based on param type
        param_type = param_info['type']
        if param_type not in xmstool_widget_map:
            param_type = 'StringSelector'  # Default to StringSelector if type is not found
        form_class.base_fields[field_name] = xmstool_widget_map[param_type](param_info)

        # Set label with param label if set, otherwise derive from parameter name
        label = param_info['description']
        form_class.base_fields[field_name].label = field_name.replace("_", " ").title() if not label else label

        # If form is read-only, set disabled attribute
        form_class.base_fields[field_name].widget.attrs.update({'disabled': read_only})

        # Help text displayed on hover over field
        if 'doc' in param_info and param_info['doc']:
            form_class.base_fields[field_name].widget.attrs.update({'title': param_info['doc']})

    return form_class
