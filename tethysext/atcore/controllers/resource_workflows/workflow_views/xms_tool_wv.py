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


xmstool_widget_map = {
    # param.Foldername:
    #     lambda po, p, name: forms.FilePathField(
    #         initial=po.param.inspect_value(name) or p.default,
    #         path=p.search_paths,
    #     ),
    'Boolean':
        lambda po, interface_info, name: forms.BooleanField(
            initial=interface_info['value'],
            required=False,
        ),
    # param.Filename:
    #     lambda po, p, name: forms.FileField(
    #         initial=po.param.inspect_value(name) or p.default,
    #     ),
    'String':
        lambda po, interface_info, name: forms.CharField(
            initial=interface_info['value'],
        ),
    'ObjectSelector':
        lambda po, d, name: forms.ChoiceField(
            initial=d['value'],
            widget=Select2Widget,
            choices=list(enumerate(d['objects'])),
        ),
    'StringSelector':
        lambda po, d, name: forms.ChoiceField(
            initial=d['value'],
            widget=Select2Widget,
            choices=list(enumerate(d['choices'])),
        ),
    'Number':
        lambda po, interface_info, name: forms.FloatField(
            initial=interface_info['value'],
        ),
    # param.FileSelector:
    #     lambda po, p, name: forms.ChoiceField(
    #         initial=po.param.inspect_value(name) or p.default,
    #     ),
    'Integer':
        lambda po, interface_info, name: forms.IntegerField(
            initial=interface_info['value'],
        ),
}


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
    def _setup_parameterized_args(arguments):
        """Takes the XMSToolArgument list and turns it into a dictionary of Param types.

        Args:
            arguments (List[Argument]): List of tool arguments.

        Returns:
            (Dict[str, Parameter]): List of Parameter objects.
        """
        arguments_dict = {}
        argument_precedence = {}
        precedence = 100
        for argument in arguments:
            interface_info = argument.get_interface_info()
            if interface_info['value'] is not None:
                interface_info['value'] = argument.value
            displayed = True
            if argument.io_direction == 2 and argument.type in ['integer', 'float', 'string']:
                displayed = False
            if displayed:
                argument_precedence[argument.name] = precedence
                arguments_dict[argument.name] = interface_info
                precedence += 1
        return arguments_dict

    if not setup_func:
        setup_func = _setup_parameterized_args
    tool_arguments = xms_tool_class.initial_arguments()
    argument_params = setup_func(tool_arguments)

    # Create Django Form class dynamically
    class_name = '{}Form'.format(xms_tool_class.name.title()).replace(' ', '')
    form_class = type(class_name, (forms.Form,), dict(forms.Form.__dict__))

    # Sort parameters based on precedence
    sorted_params = argument_params.items()

    initial_options = {}
    if resource and arg_mapping:
        for arg_name, arg_atts in arg_mapping.items():
            for cur_p in sorted_params:
                if cur_p[0] == arg_name:
                    available_options = []

                    # Use the resource attribute to read the possible resource data sources
                    datasets = getattr(resource, arg_atts['resource_attr'])
                    datasets = datasets if type(datasets) is list else [datasets]
                    for dataset in datasets:
                        filter_attr_value = getattr(dataset, arg_atts['filter_attr'])
                        if filter_attr_value in arg_atts['valid_values']:
                            name_attr = getattr(dataset, arg_atts['name_attr'])
                            if 'name_attr_regex' in arg_atts:
                                # Perform a regex on the name attribute to filter the name
                                name_attr_regex = re.findall(arg_atts['name_attr_regex'], name_attr)
                                name_attr = name_attr_regex[0] if name_attr_regex else name_attr
                            available_options.append(name_attr)

                    # Store any initial options if found
                    if available_options:
                        initial_options[arg_name] = available_options

    # Fill in form values if necessary
    if form_values:
        for form_value in form_values.items():
            for param in sorted_params:
                if param[0] in form_value[1]:
                    param[1]._value = form_value[1][param[0]]

    for cur_p in sorted_params:
        p_name = cur_p[0]

        # Assign any initial arguments if found from argument mapping for input arguments
        for xms_arg in tool_arguments:
            if xms_arg.name == p_name and xms_arg.io_direction == 1 and p_name in initial_options:
                cur_p[1]['choices'] = initial_options[p_name]

        # Prefix parameter name if prefix provided
        if form_field_prefix is not None:
            p_name = form_field_prefix + p_name

        # Get appropriate Django field/widget based on param type
        form_class.base_fields[p_name] = xmstool_widget_map[cur_p[1]['type']](argument_params, cur_p[1], cur_p[0])

        # Set label with param label if set, otherwise derive from parameter name
        label = cur_p[1]['description']
        form_class.base_fields[p_name].label = cur_p[0].replace("_", " ").title() if not label else label

        # If form is read-only, set disabled attribute
        form_class.base_fields[p_name].widget.attrs.update({'disabled': read_only})

        # Help text displayed on hover over field
        if 'doc' in cur_p[1] and cur_p[1]['doc']:
            form_class.base_fields[p_name].widget.attrs.update({'title': cur_p[1]['doc']})

        # Set required state from allow_None
        # form_class.base_fields[p_name].required = cur_p.allow_None

    return form_class
