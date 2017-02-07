# Copyright (c) 2016, Juniper Networks, Inc.
# All rights reserved.

FROM ubuntu:14.04
MAINTAINER Marcel Wiget

# install tools required in the running container
RUN apt-get -o Acquire::ForceIPv4=true update \
  && apt-get -o Acquire::ForceIPv4=true install -y --no-install-recommends \
  net-tools iproute2 dosfstools tcpdump bridge-utils numactl genisoimage \
  libaio1 libspice-server1 libncurses5 openssh-client libjson-xs-perl \
  python-twisted mosquitto-clients python-setuptools

# fix usr/sbin/tcpdump by moving it into /sbin: 
#  error while loading shared libraries: libcrypto.so.1.0.0: 
#  cannot open shared object file: Permission denied
RUN mv /usr/sbin/tcpdump /sbin/

# dumb-init
COPY dumb-init/dumb-init /usr/bin/

COPY qemu-v2.4.1-snabb.tgz /
RUN tar zxf /qemu-v*-snabb.tgz -C /usr/local/

# python-tools
COPY python-tools.tgz /
RUN tar zxf python-tools.tgz && rm python-tools.tgz 

# Snabb
COPY snabb/src/snabb /usr/local/bin/

RUN mkdir /yang /jetapp /jetapp/src /utils /op /snmp /jet \
  /jetapp/src/common /jetapp/src/conf /jetapp/src/notification /jetapp/src/conf/template /jetapp/src/conf/protos 

COPY yang/ietf-inet-types.yang yang/ietf-yang-types.yang \
  yang/ietf-softwire.yang \
  jetapp/yang/op/junos-extension.yang jetapp/yang/op/junos-extension-odl.yang \
  jetapp/yang/op/rpc-get-lwaftr.yang jetapp/yang/op/rpc-get-lwaftr-statistics.yang \
  jetapp/yang/op/rpc-monitor-lwaftr.yang \
  yang/jnx-aug-softwire.yang yang/jnx-softwire-dev.yang yang/

COPY /jetapp/COPYRIGHT /jetapp/COPYRIGHT
COPY /jetapp/LICENSE /jetapp/LICENSE
COPY /jetapp/MANIFEST.in /jetapp/MANIFEST.in
COPY /jetapp/README.txt /jetapp/README.txt
COPY /jetapp/requirements.txt /jetapp/requirements.txt
COPY /jetapp/setup.py /jetapp/setup.py
COPY /jetapp/src/__init__.py /jetapp/src/__init__.py
COPY /jetapp/src/main.py /jetapp/src/main.py
COPY /jetapp/src/requirements.txt /jetapp/src/requirements.txt
COPY /jetapp/src/version.py /jetapp/src/version.py
COPY /jetapp/src/common/__init__.py /jetapp/src/common/__init__.py
COPY /jetapp/src/common/app_globals.py /jetapp/src/common/app_globals.py
COPY /jetapp/src/common/device.py /jetapp/src/common/device.py
COPY /jetapp/src/common/mylogging.py /jetapp/src/common/mylogging.py
COPY /jetapp/src/common/sanity.py /jetapp/src/common/sanity.py
COPY /jetapp/src/common/snabb_startup_checks.py /jetapp/src/common/snabb_startup_checks.py
COPY /jetapp/src/conf/__init__.py /jetapp/src/conf/__init__.py
COPY /jetapp/src/conf/callback.py /jetapp/src/conf/callback.py
COPY /jetapp/src/conf/conf_action.py /jetapp/src/conf/conf_action.py
COPY /jetapp/src/conf/conf_globals.py /jetapp/src/conf/conf_globals.py
COPY /jetapp/src/conf/conf_parser.py /jetapp/src/conf/conf_parser.py
COPY /jetapp/src/conf/protos/__init__.py /jetapp/src/conf/protos/__init__.py
COPY /jetapp/src/conf/protos/authentication_service.proto /jetapp/src/conf/protos/authentication_service.proto
COPY /jetapp/src/conf/protos/authentication_service_pb2.py /jetapp/src/conf/protos/authentication_service_pb2.py
COPY /jetapp/src/conf/protos/mgd_service.proto /jetapp/src/conf/protos/mgd_service.proto
COPY /jetapp/src/conf/protos/mgd_service_pb2.py /jetapp/src/conf/protos/mgd_service_pb2.py
COPY /jetapp/src/conf/protos/openconfig_service.proto /jetapp/src/conf/protos/openconfig_service.proto
COPY /jetapp/src/conf/protos/openconfig_service_pb2.py /jetapp/src/conf/protos/openconfig_service_pb2.py
COPY /jetapp/src/conf/template/snabbvmx-binding.template /jetapp/src/conf/template/snabbvmx-binding.template
COPY /jetapp/src/conf/template/snabbvmx-cfg.template /jetapp/src/conf/template/snabbvmx-cfg.template
COPY /jetapp/src/conf/template/snabbvmx-conf.template /jetapp/src/conf/template/snabbvmx-conf.template
COPY /jetapp/src/conf/template/snabbvmx-top.template /jetapp/src/conf/template/snabbvmx-top.template
COPY /jetapp/src/notification/__init__.py /jetapp/src/notification/__init__.py
COPY /jetapp/src/notification/notification.py /jetapp/src/notification/notification.py
COPY /jetapp/src/notification/notification_handler.py /jetapp/src/notification/notification_handler.py
COPY /jetapp/src/notification/notification_topic.py /jetapp/src/notification/notification_topic.py
COPY /jetapp/src/op/__init__.py /jetapp/src/op/__init__.py
COPY /jetapp/src/op/opglobals.py /jetapp/src/op/opglobals.py
COPY /jetapp/src/op/opserver.py /jetapp/src/op/opserver.py
COPY /jetapp/tests/test_rpc_get_lwaftr_state.py /jetapp/tests/test_rpc_get_lwaftr_state.py
COPY /jetapp/tests/test_rpc_get_lwaftr_statistics.py /jetapp/tests/test_rpc_get_lwaftr_statistics.py
COPY /jetapp/yang/op/junos-extension-odl.yang /jetapp/yang/op/junos-extension-odl.yang
COPY /jetapp/yang/op/junos-extension.yang /jetapp/yang/op/junos-extension.yang
COPY /jetapp/yang/op/rpc-get-lwaftr-statistics.yang /jetapp/yang/op/rpc-get-lwaftr-statistics.yang
COPY /jetapp/yang/op/rpc-get-lwaftr.yang /jetapp/yang/op/rpc-get-lwaftr.yang
COPY /jetapp/yang/op/rpc-jet.py /jetapp/yang/op/rpc-jet.py
COPY /jetapp/yang/op/rpc-monitor-lwaftr.yang /jetapp/yang/op/rpc-monitor-lwaftr.yang
COPY /jetapp/yang/op/rpc_get_lwaftr_state.py /jetapp/yang/op/rpc_get_lwaftr_state.py
COPY /jetapp/yang/op/rpc_get_lwaftr_statistics.py /jetapp/yang/op/rpc_get_lwaftr_statistics.py
COPY /jetapp/yang/op/rpc_monitor_lwaftr.py /jetapp/yang/op/rpc_monitor_lwaftr.py


COPY slax/lwaftr.slax \
  jetapp/yang/op/rpc_get_lwaftr_state.py \
  jetapp/yang/op/rpc_monitor_lwaftr.py \
  jetapp/yang/op/rpc_get_lwaftr_statistics.py op/

COPY jetapp/yang/op/rpc-jet.py jet/

COPY snmp/snmp_lwaftr.slax snmp/lw4over6.py snmp/

COPY launch.sh launch_snabb.sh top.sh topl.sh README.md VERSION \
  launch_jetapp.sh \
  show_affinity.sh \
  monitor.sh add_bindings.sh launch_snabb_query.sh /

RUN date >> /VERSION

EXPOSE 8700 

ENTRYPOINT ["/usr/bin/dumb-init", "/launch.sh"]
CMD ["-h"]
