{% set CONDA_HOME = salt['environ.get']('CONDA_HOME') %}
{% set CONDA_ENV_NAME = salt['environ.get']('CONDA_ENV_NAME') %}
{% set TETHYS_HOME = salt['environ.get']('TETHYS_HOME') %}
{% set TETHYSEXT_DIR = salt['environ.get']('TETHYSEXT_DIR') %}
{% set TETHYS_BIN_DIR = salt['environ.get']('TETHYS_BIN_DIR') %}
{% set TETHYS_DB_HOST = salt['environ.get']('TETHYS_DB_HOST') %}
{% set TETHYS_DB_PASSWORD = salt['environ.get']('TETHYS_DB_PASSWORD') %}
{% set TETHYS_DB_PORT = salt['environ.get']('TETHYS_DB_PORT') %}
{% set TETHYS_DB_USERNAME = salt['environ.get']('TETHYS_DB_USERNAME') %}
{% set TETHYS_PUBLIC_HOST = salt['environ.get']('PUBLIC_HOST') %}
{% set STATIC_ROOT = salt['environ.get']('STATIC_ROOT') %}
{% set TETHYS_PERSIST = salt['environ.get']('TETHYS_PERSIST') %}

Edit_Tethys_Settings_File_(INSTALLED_APPS)_Atcore:
  file.replace:
    - name: {{ TETHYS_HOME }}/tethys/tethys_portal/settings.py
    - pattern: "'rest_framework.authtoken',"
    - repl: "'rest_framework.authtoken',\n'datetimewidget',\n'django_select2',\n'taggit',"
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Edit_Tethys_Settings_File_(PUBLIC_HOST)_Atcore:
  file.append:
    - name: {{ TETHYS_HOME }}/tethys/tethys_portal/settings.py
    - text: "PUBLIC_HOST = \"{{ TETHYS_PUBLIC_HOST }}\""
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Edit_Tethys_Settings_File_(DATA_UPLOAD_MAX_MEMORY_SIZE)_Atcore:
  file.append:
    - name: {{ TETHYS_HOME }}/tethys/tethys_portal/settings.py
    - text: "DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1048000  # 100 MB"
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Install_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && cd {{ TETHYSEXT_DIR }}/tethysext-atcore && tethys install --quiet --without-dependencies
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Migrate_Database_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys db migrate
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Collect_Static_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys manage collectstatic --noinput
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Overwrite_Tethys_Main_CSS_Atcore:
  cmd.run:
    - name: rm {{ STATIC_ROOT }}/tethys_portal/css/tethys_main.css && cp {{ TETHYSEXT_DIR }}/tethysext-atcore/tethysext/atcore/public/css/tethys_main.css {{ STATIC_ROOT }}/tethys_portal/css/tethys_main.css
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Overwrite_App_Library_CSS_Atcore:
  cmd.run:
    - name: rm {{ STATIC_ROOT }}/tethys_apps/css/app_library.css && cp {{ TETHYSEXT_DIR }}/tethysext-atcore/tethysext/atcore/public/css/app_library.css {{ STATIC_ROOT }}/tethys_apps/css/app_library.css
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Site_Settings_Atcore:
  cmd.run:
    - name: . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} && tethys site --title "Portal" --tab-title "Portal" --logo "/atcore/images/aquaveo_logo.png"  --favicon "/atcore/images/aquaveo_favicon.ico" --copyright "Copyright © 2018 Aquaveo, LLC"
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Flag_Complete_Setup_Atcore:
  cmd.run:
    - name: touch {{ TETHYS_PERSIST }}/atcore_setup_complete
    - shell: /bin/bash
