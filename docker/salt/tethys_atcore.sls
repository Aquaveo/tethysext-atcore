{% set ALLOWED_HOST = salt['environ.get']('ALLOWED_HOST') %} 
{% set CONDA_HOME = salt['environ.get']('CONDA_HOME') %} 
{% set CONDA_ENV_NAME = salt['environ.get']('CONDA_ENV_NAME') %} 
{% set TETHYSAPP_DIR = salt['environ.get']('TETHYSAPP_DIR') %}
{% set TETHYSEXT_DIR = salt['environ.get']('TETHYSEXT_DIR') %}


Sync_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys manage sync
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/atcore_setup_complete" ];"

Collect_Static:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys manage collectstatic --noinput
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/atcore_setup_complete" ];"

Flag_Complete_Setup:
  cmd.run:
    - name: touch /usr/lib/tethys/atcore_setup_complete
    - shell: /bin/bash
