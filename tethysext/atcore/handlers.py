"""
********************************************************************************
* Name: handlers
* Author: msouffront
* Created On: Nov 12, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethys_sdk.base import with_request
from tethys_apps.utilities import get_active_app
import panel as pn
from tethysext.atcore.models.app_users import ResourceWorkflowStep


@with_request
def panel_rws_handler(document):
    app = get_active_app(document.request, get_class=True)
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()

    current_step_id = document.request.url_route['kwargs']['step_id']
    current_step = session.query(ResourceWorkflowStep).get(current_step_id)

    package, p_class = current_step.options['param_class'].rsplit('.', 1)
    mod = __import__(package, fromlist=[p_class])
    ParamClass = getattr(mod, p_class)

    param_class = ParamClass(request=document.request, session=session)

    form_values = current_step.get_parameter('form-values').items()
    for k, v in form_values:
        if k != 'name':
            param_class.set_param(k, v)

    panel = pn.Row(param_class.param)

    panel.server_doc(document)
