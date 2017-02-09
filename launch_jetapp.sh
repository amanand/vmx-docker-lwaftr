#!/bin/bash
# Copyright (c) 2016, Juniper Networks, Inc.
# All rights reserved.

echo "$0: Launching jetapp server"
while :
do
  python /jetapp/src/main.py --config /jetapp/src/config.json 
  echo "jetapp terminated. Restarting in 5 seconds ..."
  sleep 5
done
