# Use our Tethyscore base docker image as a parent image
ARG PYTHON_VERSION=3.12
ARG DJANGO_VERSION=3.2
ARG TETHYS_VERSION=4.3.7
ARG BASE_IMAGE_TAG="${TETHYS_VERSION}-py${PYTHON_VERSION}-dj${DJANGO_VERSION}"
ARG BASE_IMAGE="tethysplatform/tethys-core"

# Use our Tethys Core base docker image as a parent image
FROM ${BASE_IMAGE}:${BASE_IMAGE_TAG}

# This is necessary for the ARG variables to be available in the rest of the Dockerfile
ARG PYTHON_VERSION
ARG DJANGO_VERSION
ARG TETHYS_VERSION

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
RUN echo "Django version set to ${DJANGO_VERSION}" \
  ; echo "Tethys version set to ${TETHYS_VERSION}" \
  ; echo "Python version set to ${PYTHON_VERSION}"
RUN /bin/bash -c "micromamba run -n ${ENV_NAME} python --version; which python"
RUN echo "DJANGO_VERSION is: ${DJANGO_VERSION}" \
  ; cd ${TETHYSEXT_DIR}/tethysext-atcore \
  ; sed -i "s|^[[:space:]]*- django[^-].*|    - django=${DJANGO_VERSION}|" install.yml \
  ; cat install.yml \
  ; micromamba run -n ${ENV_NAME} tethys install -N -q

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
