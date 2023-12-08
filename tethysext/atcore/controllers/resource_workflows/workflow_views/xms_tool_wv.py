"""
********************************************************************************
* Name: xms_tool_wv.py
* Author: mmlebaron, glarsen
* Created On: October 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging

from django import forms
from django_select2.forms import Select2Widget

from xms.tool_core import ParameterizedArgs  # noqa I100,I201

from tethysext.atcore.controllers.resource_workflows.workflow_views import FormInputWV
from tethysext.atcore.models.resource_workflow_steps.xms_tool_rws import XMSToolRWS
from tethysext.atcore.forms.widgets.param_widgets import generate_django_form

# from bokeh.embed import server_document

log = logging.getLogger(f'tethys.{__name__}')


xmstool_widget_map = {
    # param.Foldername:
    #     lambda po, p, name: forms.FilePathField(
    #         initial=po.param.inspect_value(name) or p.default,
    #         path=p.search_paths,
    #     ),
    'Boolean':
        lambda po, p, name: forms.BooleanField(
            # initial=po.param.inspect_value(name) or p.default, required=False
            initial=p.value or p.default,
            required=False,
        ),
    # param.Filename:
    #     lambda po, p, name: forms.FileField(
    #         initial=po.param.inspect_value(name) or p.default,
    #     ),
    'String':
        lambda po, p, name: forms.CharField(
            # initial=po.param.inspect_value(name) or p.default,
            initial=p.value or p.default,
        ),
    'ObjectSelector':
        lambda po, p, name: forms.ChoiceField(
            # initial=po.param.inspect_value(name) or p.default,
            initial=p.value or p.default,
            widget=Select2Widget,
            # choices=p.get_range().items(),
            choices=p.objects,
        ),
    'Number':
        lambda po, p, name: forms.FloatField(
            # initial=po.param.inspect_value(name) or p.default,
            initial=p.value or p.default,
        ),
    # param.FileSelector:
    #     lambda po, p, name: forms.ChoiceField(
    #         initial=po.param.inspect_value(name) or p.default,
    #     ),
    'Integer':
        lambda po, p, name: forms.IntegerField(
            # initial=po.param.inspect_value(name) or p.default,
            initial=p.value or p.default,
        ),
}


class XMSToolWV(FormInputWV):
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

        package, p_class = current_step.options['xmstool_class'].rsplit('.', 1)
        mod = __import__(package, fromlist=[p_class])
        XMSToolClass = getattr(mod, p_class)

        # Get the renderer option
        renderer = current_step.options['renderer']
        context.update({'renderer': renderer})

        # Django Renderer
        if renderer == 'django':
            tool = XMSToolClass()
            # if hasattr(tool, 'update_precedence'):
            #     tool.update_precedence()
            # for k, v in current_step.get_parameter('form-values').items():
            #     tool.set_param(k, v)

            # tool_arguments = tool.initial_arguments()
            # parameterized_args = ParameterizedArgs(tool_arguments)
            # parameterized_args.setup_parameterized_args()
            # argument_params = parameterized_args.arguments_as_params

            form = generate_django_form_xmstool(tool, form_field_prefix='param-form-',
                                                read_only=self.is_read_only(request, current_step))()

            # Save changes to map view and layer groups
            context.update({
                'read_only': self.is_read_only(request, current_step),
                'form_title': form_title,
                'form': form,
            })

        # # Bokeh Renderer
        # elif renderer == 'bokeh':
        #     script = server_document(request.build_absolute_uri())
        #     context.update({
        #         'read_only': self.is_read_only(request, current_step),
        #         'form_title': form_title,
        #         'script': script
        #     })

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
        breakpoint()
        package, p_class = step.options['param_class'].rsplit('.', 1)
        mod = __import__(package, fromlist=[p_class])
        ParamClass = getattr(mod, p_class)
        if step.options['renderer'] == 'django':
            param_class_for_form = ParamClass(request=request, session=session, resource=resource)
            form = generate_django_form(param_class_for_form, form_field_prefix='param-form-')(request.POST)
            params = {}

            if not form.is_valid():
                raise RuntimeError('form is invalid')

            # Get the form from the post
            # loop through items and set the params
            for p in request.POST:
                if p.startswith('param-form-'):
                    try:
                        param_name = p[11:]
                        params[param_name] = form.cleaned_data[p]
                    except ValueError as e:
                        raise RuntimeError('error setting param data: {}'.format(e))

            # Get the param class and save the data from the form
            # for the next time the form is loaded
            param_class = ParamClass(request=request, session=session, resource=resource)
            param_values = dict(param_class.param.get_param_values())
            for k, v in params.items():
                try:
                    params[k] = type(param_values[k])(v)
                except ValueError as e:
                    raise ValueError('Invalid input to form: {}'.format(e))

            step.set_parameter('resource_name', step.workflow.resource.name)
            step.set_parameter('form-values', params)

        # elif step.options['renderer'] == 'bokeh':
        #     # get document from the request here...
        #     params = {}

        #     for p in request.POST:
        #         if p.startswith('param-form-'):
        #             try:
        #                 param_name = p[11:]
        #                 params[param_name] = request.POST.get(p, None)
        #             except ValueError as e:
        #                 raise RuntimeError('error setting param data: {}'.format(e))

        #     param_class = ParamClass(request=request, session=session, resource=resource)
        #     param_values = dict(param_class.get_param_values())
        #     for k, v in params.items():
        #         try:
        #             params[k] = type(param_values[k])(v)
        #         except ValueError as e:
        #             raise ValueError('Invalid input to form: {}'.format(e))

        #     step.set_parameter('resource_name', step.workflow.resource.name)
        #     step.set_parameter('form-values', params)

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


def generate_django_form_xmstool(xms_tool_class, form_field_prefix=None, read_only=False):
    """
    Create a Django form from a Parameterized object.

    Args:
        xms_tool_class(class): the XMS tool class.
        form_field_prefix(str): A prefix to prepend to form fields
    Returns:
        Form: a Django form with fields matching the parameters of the given parameterized object.
    """
    tool_arguments = xms_tool_class.initial_arguments()
    parameterized_args = ParameterizedArgs(tool_arguments)
    parameterized_args.setup_parameterized_args()
    argument_params = parameterized_args.arguments_as_params

    # Create Django Form class dynamically
    class_name = '{}Form'.format(xms_tool_class.name.title()).replace(' ', '')
    form_class = type(class_name, (forms.Form,), dict(forms.Form.__dict__))

    # # Filter params based on precedence and constant state
    # params = list(
    #     filter(
    #         lambda x: (x.precedence is None or x.precedence >= 0) and not x.constant,
    #         parameterized_obj.param.params().values()
    #     )
    # )

    # Sort parameters based on precedence
    # sorted_params = sorted(argument_params, key=lambda p: p.precedence or 9999)
    # sorted_params = sorted(argument_params.values(), key=operator.attrgetter('precedence') or 9999)
    sorted_params = sorted(argument_params.items(), key=lambda p: p[1].precedence or 9999)

    for cur_p in sorted_params:
        # TODO: Pass p.__dict__ as second argument instead of arbitrary
        # p_name = p.name
        p_name = cur_p[0]

        # Prefix parameter name if prefix provided
        if form_field_prefix is not None:
            p_name = form_field_prefix + p_name

        # Get appropriate Django field/widget based on param type
        # form_class.base_fields[p_name] = widget_map[type(p)](parameterized_obj, p, p.name)
        form_class.base_fields[p_name] = xmstool_widget_map[cur_p[1].type](argument_params, cur_p[1], cur_p[0])

        # Set label with param label if set, otherwise derive from parameter name
        label = cur_p[1].label
        form_class.base_fields[p_name].label = cur_p[0].replace("_", " ").title() if not label else label

        # If form is read-only, set disabled attribute
        form_class.base_fields[p_name].widget.attrs.update({'disabled': read_only})

        # Help text displayed on hover over field
        if cur_p[1].doc:
            form_class.base_fields[p_name].widget.attrs.update({'title': cur_p[1].doc})

        # Set required state from allow_None
        # form_class.base_fields[p_name].required = cur_p.allow_None

    return form_class
