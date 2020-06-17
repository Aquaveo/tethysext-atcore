{% set CONDA_HOME = salt['environ.get']('CONDA_HOME') %}
{% set CONDA_ENV_NAME = salt['environ.get']('CONDA_ENV_NAME') %}
{% set TETHYS_PUBLIC_HOST = salt['environ.get']('TETHYS_PUBLIC_HOST') %}
{% set TETHYS_PERSIST = salt['environ.get']('TETHYS_PERSIST') %}
{% set TETHYSEXT_DIR = salt['environ.get']('TETHYSEXT_DIR') %}

Edit_Tethys_Portal_Config_Settings_File_Atcore:
  cmd.run:
    - name: >
        . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} &&
        tethys settings
        --set PUBLIC_HOST {{ TETHYS_PUBLIC_HOST }}
        --set INSTALLED_APPS "[datetimewidget, django_select2, taggit]"
        --set DATA_UPLOAD_MAX_MEMORY_SIZE 104800000
    - shell: /bin/bash
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

Site_Settings_Atcore:
  cmd.run:
    - name: >
        . {{ CONDA_HOME }}/bin/activate {{ CONDA_ENV_NAME }} &&
        tethys site
        --title "Portal"
        --tab-title "Portal"
        --logo "/atcore/images/aquaveo_logo.png"
        --favicon "/atcore/images/aquaveo_favicon.ico"
        --base-css atcore/css/tethys_main.css
        --library-css atcore/css/app_library.css
        --copyright "Copyright © 2020 Aquaveo, LLC"
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/atcore_setup_complete" ];"

Flag_Complete_Setup_Atcore:
  cmd.run:
    - name: touch {{ TETHYS_PERSIST }}/atcore_setup_complete
    - shell: /bin/bash
