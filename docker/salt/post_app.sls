{% set TETHYS_HOME = salt['environ.get']('TETHYS_HOME') %}
{% set TETHYS_PERSIST = salt['environ.get']('TETHYS_PERSIST') %}

Persist_Settings_Post_App:
  file.rename:
    - source: {{ TETHYS_HOME }}/tethys/tethys_portal/settings.py
    - name: {{ TETHYS_PERSIST }}/settings.py
    - unless: /bin/bash -c "[ -f "${TETHYS_PERSIST}/settings.py" ];"

Restore_Settings_Post_App:
  file.copy:
    - name: {{ TETHYS_HOME }}/tethys/tethys_portal/settings.py
    - source: {{ TETHYS_PERSIST }}/settings.py
    - force: True

Chown_Settings_Post_App:
  cmd.run:
    - name: chown www:www {{ TETHYS_HOME }}/tethys/tethys_portal/settings.py
    - shell: /bin/bash

Persist_NGINX_Config_Post_App:
  file.rename:
    - source: {{ TETHYS_HOME }}/tethys/tethys_portal/tethys_nginx.conf
    - name: {{ TETHYS_PERSIST }}/tethys_nginx.conf
    - unless: /bin/bash -c "[ -f "${TETHYS_PERSIST}/tethys_nginx.conf" ];"

Link_NGINX_Config_Post_App:
  file.symlink:
    - name: /etc/nginx/sites-enabled/tethys_nginx.conf
    - target: {{ TETHYS_PERSIST }}/tethys_nginx.conf
    - force: True

Persist_NGINX_Supervisor_Post_App:
  file.rename:
    - source: {{ TETHYS_HOME }}/tethys/tethys_portal/nginx_supervisord.conf
    - name: {{ TETHYS_PERSIST }}/nginx_supervisord.conf
    - unless: /bin/bash -c "[ -f "${TETHYS_PERSIST}/nginx_supervisord.conf" ];"

Link_NGINX_Supervisor_Post_App:
  file.symlink:
    - name: /etc/supervisor/conf.d/nginx_supervisord.conf
    - target: {{ TETHYS_PERSIST }}/nginx_supervisord.conf
    - force: True

Persist_ASGI_Supervisor_Post_App:
  file.rename:
    - source: {{ TETHYS_HOME }}/tethys/tethys_portal/asgi_supervisord.conf
    - name: {{ TETHYS_PERSIST }}/asgi_supervisord.conf
    - unless: /bin/bash -c "[ -f "${TETHYS_PERSIST}/asgi_supervisord.conf" ];"

Link_ASGI_Supervisor_Post_App:
  file.symlink:
    - name: /etc/supervisor/conf.d/asgi_supervisord.conf
    - target: {{ TETHYS_PERSIST }}/asgi_supervisord.conf
    - force: True
