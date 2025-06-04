# Use our Tethyscore base docker image as a parent image
FROM tethysplatform/tethys-core:dev-py3.12-dj5.2

#####################
# Default Variables #
#####################
ENV TETHYSAPP_DIR=/var/www/tethys/apps
ENV TETHYSEXT_DIR=/var/www/tethys/exts
ENV TETHYS_PUBLIC_HOST='localhost'
ENV JOBS_TABLE_REFRESH_INTERVAL=30000

#########
# SETUP #
#########
RUN mkdir -p "${TETHYSAPP_DIR}" \
  ; mkdir -p "${TETHYSEXT_DIR}" \
  ; mkdir -p "${TETHYS_HOME}/keys"

# Speed up APT installs and Install APT packages
RUN echo "force-unsafe-io" > /etc/dpkg/dpkg.cfg.d/02apt-speedup \
  ; echo "Acquire::http {No-Cache=True;};" > /etc/apt/apt.conf.d/no-cache \
  ; echo "Acquire::Check-Valid-Until false;" > /etc/apt/apt.conf.d/no-check-valid \
  ; rm -rf /var/lib/apt/lists/* && apt-get update && apt-get -y install gcc libgdal-dev g++ libhdf5-dev && rm -rf /var/lib/apt/lists/*

###########
# INSTALL #
###########
ADD tethysext ${TETHYSEXT_DIR}/tethysext-atcore/tethysext
ADD *.ini ${TETHYSEXT_DIR}/tethysext-atcore/
ADD pyproject.toml ${TETHYSEXT_DIR}/tethysext-atcore/
ADD *.sh ${TETHYSEXT_DIR}/tethysext-atcore/
ADD install.yml ${TETHYSEXT_DIR}/tethysext-atcore/
ARG MAMBA_DOCKERFILE_ACTIVATE=1
RUN /bin/bash -c "micromamba run -n ${ENV_NAME} python --version; which python"
RUN /bin/bash -c "cd ${TETHYSEXT_DIR}/tethysext-atcore ; micromamba run -n ${ENV_NAME} tethys install -N -q"

#########
# CHOWN #
#########
RUN export NGINX_USER=$(grep 'user .*;' /etc/nginx/nginx.conf | awk '{print $2}' | awk -F';' '{print $1}') \
  ; find ${TETHYSAPP_DIR} ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find ${TETHYSEXT_DIR} ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find ${TETHYS_PERSIST} ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find ${TETHYS_HOME}/keys ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {}

#########################
# CONFIGURE ENVIRONMENT #
#########################
EXPOSE 80

################
# COPY IN SALT #
################
ADD docker/salt/ /srv/salt/

RUN bash ${TETHYS_HOME}/build-checks.sh

#######
# RUN #
#######
CMD bash run.sh
