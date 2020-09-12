FROM alpine:3.12.0

ARG TZ='Europe/Brussels'

ENV TZ ${TZ}
ENV LD_LIBRARY_PATH=/lib:/lib/oracle/11.2/client64/lib
ENV ORACLE_HOME=/lib/oracle/11.2/client64

RUN apk update

RUN apk add --no-cache bash python3 python3-dev py3-pip py3-virtualenv tzdata procps lapack libstdc++ g++ gcc gfortran musl-dev lapack-dev libaio libnsl libc6-compat

# create an alias for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Create the findhost-inventory folder
RUN mkdir -p /opt/findhost-inventory
RUN chmod -R 755 /opt/findhost-inventory

# Add files
ADD . /opt/findhost-inventory
ADD functions/entrypoint.sh /entrypoint.sh

# Oracle instaclient 11.2 lib files
RUN unzip /opt/findhost-inventory/functions/oracle.zip -d /lib/
RUN rm -rf /opt/findhost-inventory/functions/oracle.zip

# link the oracle client
RUN ln -s /lib/oracle/11.2/client64/lib/libclntsh.so.11.1 /lib/oracle/11.2/client64/lib/libclntsh.so
RUN ln -s /usr/lib/libnsl.so.2.0.0 /lib/libnsl.so.1

# install python requirements
RUN pip install -r /opt/findhost-inventory/requirements.txt

RUN chmod -R 755 /entrypoint.sh
RUN chmod -R 755 /opt/findhost-inventory/findhost-populate.sh
RUN chmod -R 755 /opt/findhost-inventory/consolidator/findhost-consolidator.sh
RUN chmod -R 755 /opt/findhost-inventory/collector/findhost-collector.sh
RUN chmod -R 755 /opt/findhost-inventory/collector/frontix/findhost-collector-frontix.sh

WORKDIR /opt/findhost-inventory

ENTRYPOINT /entrypoint.sh

