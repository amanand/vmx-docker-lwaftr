
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER
#
# Copyright (c) 2015 Juniper Networks, Inc.
# All rights reserved.
#
# Use is subject to license terms.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Please make sure to run this file as a root user

#!/usr/bin/env python
__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2017 Juniper Networks, Inc."

import argparse
import sys
import os
import json
from common.device import Device
from threading import Thread
from conf.conf_parser import ParseNotification
from op.opserver import OpServer
from twisted.internet import reactor
from twisted.web import server
from common.mylogging import LOG
from common.app_globals import *


def Main():
    parser = argparse.ArgumentParser(prog=os.path.basename(
        __file__), description='Snabb VMX integration JET app')
    parser.add_argument("--host",  help="Host address of the JSD server",
                        type=str, default=DEFAULT_RPC_HOST)
    parser.add_argument("--user",  help="Username for authentication by JET server (default:%(default)s)",
                        type=str, default=DEFAULT_USER_NAME)
    parser.add_argument("--password",  help="Password for authentication by JET server (default:%(default)s",
                        type=str, default=DEFAULT_PASSWORD)
    parser.add_argument("--rpc_port", nargs='?', help="Port number of the JSD gRPC server. default: %(default)s",
                        type=int, default=DEFAULT_RPC_PORT)
    parser.add_argument("--notification_port", nargs='?', help="Port number of the JSD notification server. default: %(default)s",
                        type=int, default=DEFAULT_NOTIFICATION_PORT)
    parser.add_argument("--config", nargs='?', help="JSON config file", type=str,default=None)

    args = parser.parse_args()
    if args.config is not None:
	try:
	    json_cfg = {}
	    with open(args.config) as json_cfg_file:
                json_cfg = json.load(json_cfg_file)
            device = Device(json_cfg['host'], json_cfg['user'], json_cfg['password'],
                                json_cfg['rpc_port'], json_cfg['notification_port'])
	except Exception as e:
	     LOG.error("exception :%s" %str(e.message))
	     sys.exit(0)	    
    else:
        try:
            device = Device(args.host, args.user, args.password,
                    args.rpc_port, args.notification_port)
        except Exception as e:
            LOG.error("Exception:%s" % e.message)
            sys.exit(0)
    dispatchFunction = ParseNotification(device)
    dispatchThread = Thread(target=dispatchFunction)
    dispatchThread.setDaemon(True)
    dispatchThread.start()
    try:
        device.initialize()
        # log device initialized successfully
        print "Device initialized for the configuration updates"
        opw = OpServer()
        reactor.listenTCP(9191, server.Site(opw))
        LOG.info("Starting the reactor")
        reactor.run()

    except Exception as e:
        # log device initialization failed
        LOG.critical("JET app exiting due to exception: %s" % str(e.message))
        sys.exit(0)
    return

if __name__ == '__main__':
    Main()
