API
===

This is the API documentation for ATCore.

Resource Model
--------------

.. autoclass:: tethysext.atcore.models.app_users.resource.Resource
   :members:


Model Database
--------------

.. code-block:: python
    :linenos:
    :emphasize-lines: 3

    from tethysext.atcore.services.model_database import ModelDatabase

    md = ModelDatabase('agwa', '14')

.. autoclass:: tethysext.atcore.services.model_database.ModelDatabase
   :members:
