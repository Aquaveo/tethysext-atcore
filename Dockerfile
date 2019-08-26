# Use our Tethyscore base docker image as a parent image
FROM docker.aquaveo.com/tethys/aqua-tethys:v3.0.0b-r22

#####################
# Default Variables #
#####################
ENV TETHYSAPP_DIR /var/www/tethys/apps
ENV TETHYSEXT_DIR /var/www/tethys/exts
ENV TETHYS_PUBLIC_HOST 'localhost'

#########
# SETUP #
#########
RUN mkdir -p "${TETHYSAPP_DIR}" \
  ; mkdir -p "${TETHYSEXT_DIR}"

# Speed up APT installs and Install APT packages
RUN echo "force-unsafe-io" > /etc/dpkg/dpkg.cfg.d/02apt-speedup \
  ; echo "Acquire::http {No-Cache=True;};" > /etc/apt/apt.conf.d/no-cache \
  ; echo "Acquire::Check-Valid-Until false;" > /etc/apt/apt.conf.d/no-check-valid \
  ; apt-get update && apt-get -y install gcc libgdal-dev g++ libhdf5-dev

###########
# INSTALL #
###########
ADD tethysext ${TETHYSEXT_DIR}/tethysext-atcore/tethysext
ADD *.ini ${TETHYSEXT_DIR}/tethysext-atcore/
ADD *.py ${TETHYSEXT_DIR}/tethysext-atcore/
ADD install.yml ${TETHYSEXT_DIR}/tethysext-atcore/
# Generate temporary settings.py to be able to install the extension, then remove it.
RUN /bin/bash -c ". ${CONDA_HOME}/bin/activate tethys \
  ; tethys gen settings --overwrite \
  ; cd ${TETHYSEXT_DIR}/tethysext-atcore \
  ; tethys install --quiet --only-dependencies \
  ; rm $(tethys list -s)"

#########
# CHOWN #
#########
RUN export NGINX_USER=$(grep 'user .*;' /etc/nginx/nginx.conf | awk '{print $2}' | awk -F';' '{print $1}') \
  ; find ${TETHYSAPP_DIR} ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find ${TETHYSEXT_DIR} ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find /usr/lib/tethys/workspaces ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find /usr/lib/tethys/static ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find /usr/lib/tethys/keys ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {} \
  ; find /usr/lib/tethys/src ! -user ${NGINX_USER} -print0 | xargs -0 -I{} chown ${NGINX_USER}: {}

#########################
# CONFIGURE ENVIRONMENT #
#########################
EXPOSE 80

################
# COPY IN SALT #
################
ADD docker/salt/ /srv/salt/
ADD docker/test-docker.sh ${TETHYS_HOME}/

#######
# RUN #
#######
CMD bash run.sh
