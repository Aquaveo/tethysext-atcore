{% set CONDA_HOME = salt['environ.get']('CONDA_HOME') %}
{% set TETHYS_HOME = salt['environ.get']('TETHYS_HOME') %}
{% set CONDA_ENV_NAME = salt['environ.get']('CONDA_ENV_NAME') %}
{% set TETHYS_BIN_DIR = salt['environ.get']('TETHYS_BIN_DIR') %}

Edit_Tethys_Settings_File_(INSTALLED_APPS)_Atcore:
  file.replace:
    - name: {{ TETHYS_HOME }}/src/tethys_portal/settings.py
    - pattern: "'rest_framework.authtoken',"
    - repl: "'rest_framework.authtoken',\n'datetimewidget',\n'django_select2',\n'taggit',"
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/setup_complete" ];"

Migrate_Database_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && {{ TETHYS_BIN_DIR }}/tethys manage syncdb
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/setup_complete" ];"

Sync_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys manage sync
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/atcore_setup_complete" ];"

Collect_Static_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys manage collectstatic --noinput
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/atcore_setup_complete" ];"

Flag_Complete_Setup_Atcore:
  cmd.run:
    - name: touch /usr/lib/tethys/atcore_setup_complete
    - shell: /bin/bash
