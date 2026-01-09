{% set ALLOWED_HOSTS = salt['environ.get']('ALLOWED_HOSTS') %}
{% set CSRF_TRUSTED_ORIGINS = salt['environ.get']('CSRF_TRUSTED_ORIGINS') %}
{% set OTHER_SETTINGS = salt['environ.get']('OTHER_SETTINGS') %}
{% set PORTAL_SUPERUSER_EMAIL = salt['environ.get']('PORTAL_SUPERUSER_EMAIL') %}
{% set PORTAL_SUPERUSER_NAME = salt['environ.get']('PORTAL_SUPERUSER_NAME') %}
{% set PORTAL_SUPERUSER_PASSWORD = salt['environ.get']('PORTAL_SUPERUSER_PASSWORD') %}
{% set POSTGRES_PASSWORD = salt['environ.get']('POSTGRES_PASSWORD') %}
{% set TETHYSAPP_DIR = salt['environ.get']('TETHYSAPP_DIR') %}
{% set TETHYSEXT_DIR = salt['environ.get']('TETHYSEXT_DIR') %}
{% set TETHYS_DB_ENGINE = salt['environ.get']('TETHYS_DB_ENGINE') %}
{% set TETHYS_DB_NAME = salt['environ.get']('TETHYS_DB_NAME') %}
{% set TETHYS_DB_USERNAME = salt['environ.get']('TETHYS_DB_USERNAME') %}
{% set TETHYS_DB_PASSWORD = salt['environ.get']('TETHYS_DB_PASSWORD') %}
{% set TETHYS_DB_HOST = salt['environ.get']('TETHYS_DB_HOST') %}
{% set TETHYS_DB_PORT = salt['environ.get']('TETHYS_DB_PORT') %}
{% set TETHYS_DB_SUPERUSER = salt['environ.get']('TETHYS_DB_SUPERUSER') %}
{% set TETHYS_DB_SUPERUSER_PASS = salt['environ.get']('TETHYS_DB_SUPERUSER_PASS') %}
{% set TETHYS_HOME = salt['environ.get']('TETHYS_HOME') %}
{% set TETHYS_PERSIST = salt['environ.get']('TETHYS_PERSIST') %}
{% set TETHYS_PUBLIC_HOST = salt['environ.get']('TETHYS_PUBLIC_HOST') %}


DC_Generate_Tethys_Settings:
  cmd.run:
    - name: >
        tethys settings
        --set ALLOWED_HOSTS {{ ALLOWED_HOSTS }}
        --set CSRF_TRUSTED_ORIGINS {{ CSRF_TRUSTED_ORIGINS }}
        {%- if TETHYS_DB_ENGINE %}
        --set DATABASES.default.ENGINE "{{ TETHYS_DB_ENGINE }}"
        {%- endif %}
        {%- if TETHYS_DB_NAME %}
        --set DATABASES.default.NAME "{{ TETHYS_DB_NAME }}"
        {%- endif %}
        {%- if TETHYS_DB_USERNAME %}
        --set DATABASES.default.USER "{{ TETHYS_DB_USERNAME }}"
        {%- endif %}
        {%- if TETHYS_DB_PASSWORD %}
        --set DATABASES.default.PASSWORD "{{ TETHYS_DB_PASSWORD }}"
        {%- endif %}          
        {%- if TETHYS_DB_HOST %}
        --set DATABASES.default.HOST "{{ TETHYS_DB_HOST }}"
        {%- endif %}
        {%- if TETHYS_DB_PORT %}
        --set DATABASES.default.PORT "{{ TETHYS_DB_PORT }}"
        {%- endif %}                   
        {{ OTHER_SETTINGS }}
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/devcontainer_setup_complete" ];"

DC_SET_ATCore_Settings:
  cmd.run:
    - name: >
        tethys settings
        --set PUBLIC_HOST {{ TETHYS_PUBLIC_HOST }}
        --set INSTALLED_APPS "[django_select2, taggit]"
        --set CHANNEL_LAYERS.default.BACKEND 'channels.layers.InMemoryChannelLayer'
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/devcontainer_setup_complete" ];"

DC_Create_Database_User_and_SuperUser:
  cmd.run:
    - name: >
        PGPASSWORD="{{ POSTGRES_PASSWORD }}" tethys db create
        -n "{{ TETHYS_DB_USERNAME }}"
        -p "{{ TETHYS_DB_PASSWORD }}"
        -N "{{ TETHYS_DB_SUPERUSER }}"
        -P "{{ TETHYS_DB_SUPERUSER_PASS }}"
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f '{{ TETHYS_PERSIST }}/devcontainer_setup_complete' ]

DC_Migrate_Database:
  cmd.run:
    - name: >
        tethys db migrate
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/devcontainer_setup_complete" ];"

DC_Create_Database_Portal_SuperUser:
  cmd.run:
    - name: >
        tethys db createsuperuser
        {%- if PORTAL_SUPERUSER_NAME and PORTAL_SUPERUSER_PASSWORD %}
        --pn "{{ PORTAL_SUPERUSER_NAME }}" --pp "{{ PORTAL_SUPERUSER_PASSWORD }}"
        {% endif %}
        {%- if PORTAL_SUPERUSER_EMAIL %}--pe "{{ PORTAL_SUPERUSER_EMAIL }}"{% endif %}
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/devcontainer_setup_complete" ];"

DC_Persist_Portal_Config:
  file.rename:
    - source: {{ TETHYS_HOME }}/portal_config.yml
    - name: {{ TETHYS_PERSIST }}/portal_config.yml
    - unless: /bin/bash -c "[ -f "${TETHYS_PERSIST}/portal_config.yml" ];"

DC_Restore_Portal_Config:
  file.symlink:
    - name: {{ TETHYS_HOME }}/portal_config.yml
    - target: {{ TETHYS_PERSIST }}/portal_config.yml
    - force: True

DC_Editable_Install_Extension:
  cmd.run:
    - name: cd {{ TETHYSEXT_DIR }}/tethysext-atcore && pip install -e .
    - shell: /bin/bash

DC_Portal_Settings:
  cmd.run:
    - name: >
        tethys site
        --brand-text "Portal"
        --site-title "Aquaveo Portal"
        --brand-image "/atcore/images/aquaveo_logo.png"
        --favicon "/atcore/images/aquaveo_favicon.ico"
        --portal-base-css atcore/css/tethys_main.css
        --apps-library-css atcore/css/app_library.css
        --copyright "Copyright © 2022 Aquaveo, LLC"
    - shell: /bin/bash
    - unless: /bin/bash -c "[ -f "{{ TETHYS_PERSIST }}/devcontainer_setup_complete" ];"

DC_Flag_Complete_Setup:
  cmd.run:
    - name: touch {{ TETHYS_PERSIST }}/devcontainer_setup_complete
    - shell: /bin/bash
