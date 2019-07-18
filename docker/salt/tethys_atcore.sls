{% set CONDA_HOME = salt['environ.get']('CONDA_HOME') %}
{% set TETHYS_HOME = salt['environ.get']('TETHYS_HOME') %}
{% set TETHYSEXT_DIR = salt['environ.get']('TETHYSEXT_DIR') %}
{% set CONDA_ENV_NAME = salt['environ.get']('CONDA_ENV_NAME') %}
{% set TETHYS_BIN_DIR = salt['environ.get']('TETHYS_BIN_DIR') %}
{% set TETHYS_DB_HOST = salt['environ.get']('TETHYS_DB_HOST') %}
{% set TETHYS_DB_PASSWORD = salt['environ.get']('TETHYS_DB_PASSWORD') %}
{% set TETHYS_DB_PORT = salt['environ.get']('TETHYS_DB_PORT') %}
{% set TETHYS_DB_USERNAME = salt['environ.get']('TETHYS_DB_USERNAME') %}

Edit_Tethys_Settings_File_(INSTALLED_APPS)_Atcore:
  file.replace:
    - name: {{ TETHYS_HOME }}/src/tethys_portal/settings.py
    - pattern: "'rest_framework.authtoken',"
    - repl: "'rest_framework.authtoken',\n'datetimewidget',\n'django_select2',\n'taggit',"
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/setup_complete" ];"

Migrate_Database_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys manage syncdb
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

Site_Settings_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && PGPASSWORD={{ TETHYS_DB_PASSWORD }} psql -U {{ TETHYS_DB_USERNAME }} -h {{ TETHYS_DB_HOST }} -p {{ TETHYS_DB_PORT }} -d {{ TETHYS_DB_USERNAME }} -f {{ TETHYSEXT_DIR }}/tethysext-atcore/tethysext/atcore/resources/tethys_site_settings.sql
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/atcore_setup_complete" ];"

Flag_Complete_Setup_Atcore:
  cmd.run:
    - name: touch /usr/lib/tethys/atcore_setup_complete
    - shell: /bin/bash
