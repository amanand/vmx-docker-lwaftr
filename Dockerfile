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

RUN mkdir /yang /jetapp /jetapp/op /utils /op /snmp /jet \
  /jetapp/common /jetapp/conf /jetapp/notification /jetapp/conf/template /jetapp/conf/protos 

COPY yang/ietf-inet-types.yang yang/ietf-yang-types.yang \
  yang/ietf-softwire.yang \
  jetapp/yang/op/junos-extension.yang jetapp/yang/op/junos-extension-odl.yang \
  jetapp/yang/op/rpc-get-lwaftr.yang jetapp/yang/op/rpc-get-lwaftr-statistics.yang \
  jetapp/yang/op/rpc-monitor-lwaftr.yang \
  yang/jnx-aug-softwire.yang yang/jnx-softwire-dev.yang yang/


COPY   /jetapp/src/main.py /jetapp/src/requirements.txt   \
   /jetapp/src/version.py /jetapp/common/__init__.py   \
   /jetapp/common/app_globals.py /jetapp/common/device.py   \
   /jetapp/common/mylogging.py /jetapp/common/sanity.py   \
   /jetapp/common/snabb_startup_checks.py /jetapp/conf/__init__.py   \
   /jetapp/conf/callback.py /jetapp/conf/conf_action.py   \
   /jetapp/conf/conf_globals.py /jetapp/conf/conf_parser.py   \
   /jetapp/protos/__init__.py /jetapp/protos/authentication_service.proto   \
   /jetapp/protos/authentication_service_pb2.py /jetapp/protos/mgd_service.proto   \
   /jetapp/protos/mgd_service_pb2.py /jetapp/protos/openconfig_service.proto   \
   /jetapp/protos/openconfig_service_pb2.py /jetapp/template/snabbvmx-binding.template   \
   /jetapp/template/snabbvmx-cfg.template /jetapp/template/snabbvmx-conf.template   \
   /jetapp/template/snabbvmx-top.template /jetapp/notification/__init__.py   \
   /jetapp/notification/notification.py /jetapp/notification/notification_handler.py   \
   /jetapp/notification/notification_topic.py /jetapp/op/__init__.py   \
   /jetapp/op/opglobals.py /jetapp/op/opserver.py   \
   /jetapp/tests/test_rpc_get_lwaftr_state.py /jetapp/tests/test_rpc_get_lwaftr_statistics.py   \
   /jetapp/op/junos-extension-odl.yang /jetapp/op/junos-extension.yang   \
   /jetapp/op/rpc-get-lwaftr-statistics.yang /jetapp/op/rpc-get-lwaftr.yang   \
   /jetapp/op/rpc-jet.py /jetapp/op/rpc-monitor-lwaftr.yang   \
   /jetapp/op/rpc_get_lwaftr_state.py /jetapp/op/rpc_get_lwaftr_statistics.py   \
   /jetapp/op/rpc_monitor_lwaftr.py   /jetapp/

COPY slax/lwaftr.slax \
  jetapp/yang/op/rpc_get_lwaftr_state.py \
  jetapp/yang/op/rpc_monitor_lwaftr.py \
  jetapp/yang/op/rpc_get_lwaftr_statistics.py op/

COPY jetapp/yang/op/rpc-jet.py jet/

COPY snmp/snmp_lwaftr.slax snmp/lw4over6.py snmp/

COPY launch.sh launch_snabb.sh top.sh topl.sh README.md VERSION \
  launch_jetapp.sh launch_opserver.sh \
  launch_snabbvmx_manager.sh snabbvmx_manager.pl show_affinity.sh \
  monitor.sh add_bindings.sh launch_snabb_query.sh /

RUN date >> /VERSION

EXPOSE 8700 

ENTRYPOINT ["/usr/bin/dumb-init", "/launch.sh"]
CMD ["-h"]
