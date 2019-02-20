# Use our Tethyscore base docker image as a parent image
FROM docker.aquaveo.com/tethys/aqua-tethys/tethyscore:v3.0.0b-r3

#####################
# Default Variables #
#####################
ENV TETHYSAPP_DIR /var/www/tethys/apps
ENV TETHYSEXT_DIR /var/www/tethys/exts
ENV CONDA_HOME /usr/lib/tethys/miniconda

#########
# SETUP #
#########
RUN mkdir -p "${TETHYSAPP_DIR}"
RUN mkdir -p "${TETHYSEXT_DIR}"

# Speed up APT installs
RUN echo "force-unsafe-io" > /etc/dpkg/dpkg.cfg.d/02apt-speedup
RUN echo "Acquire::http {No-Cache=True;};" > /etc/apt/apt.conf.d/no-cache
# Install APT Package
RUN apt-get update && apt-get -y install gcc libgdal-dev g++ libhdf5-dev

###########
# INSTALL #
###########
RUN /bin/bash -c ". ${CONDA_HOME}/bin/activate tethys \
  ; pip install django sqlalchemy==1.0.19 filelock"

ADD tethysext ${TETHYSEXT_DIR}/tethysext-atcore/tethysext
ADD *.ini ${TETHYSEXT_DIR}/tethysext-atcore/
ADD *.py ${TETHYSEXT_DIR}/tethysext-atcore/
 RUN /bin/bash -c ". ${CONDA_HOME}/bin/activate tethys \
   ; cd ${TETHYSEXT_DIR}/tethysext-atcore \
   ; python setup.py install"

# Overwrite default Tethys Stylesheet
ADD tethysext/atcore/public/css/tethys_main.css ${TETHYS_HOME}/src/static/tethys_portal/css/tethys_main.css

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

#######
# RUN #
#######
CMD bash run.sh
