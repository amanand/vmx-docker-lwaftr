#!/bin/bash
INT1=$1
INT2=$2
CPUS=$3

if [ -z "$CPUS" ]; then
  echo "Usage: $0 emX emY cpus"
  exit 1
fi

while :
do
  # check if there is a snabb binary available in the mounted directory.
  # use that one if yes
  SNABB=/usr/local/bin/snabb
  if [ -f /u/snabb ]; then
    cp /u/snabb /tmp/ 2>/dev/null
    SNABB=/tmp/snabb
  fi
  echo "launch snabbvmx for $INT1 and $INT2 ..."
  $SNABB gc # removing stale runtime files created by Snabb
  CMD="taskset -c $CPUS $SNABB snabbvmx lwaftr --conf snabbvmx-lwaftr-${INT1}-${INT2}.cfg --v1id $INT1 --v1pci `cat pci_$INT1` --v1mac `cat mac_$INT1` --v2id $INT2 --v2pci `cat pci_$INT2` --v2mac `cat mac_$INT2` --sock %s.socket"
  echo $CMD
  $CMD
  sleep 5
done
