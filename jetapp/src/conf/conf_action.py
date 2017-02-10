__author__ = "Amish Anand"
__copyright__ = "Copyright (c) 2015 Juniper Networks, Inc."

import subprocess
import signal
from common.mylogging import LOG
import os
from string import Template
from conf_globals import *

SNABB_PROCESS_SEARCH_STRING = 'snabbvmx-lwaftr-xe'
SNABB_INSTANCE_LAUNCH_TEMPLATE = Template(
    '/usr/local/bin/snabb snabbvmx lwaftr --conf $cfg --id xe$id --pci $pci --mac $mac')


class ConfAction(object):

    def start_snabb_instance(self, instance_id):
        s = SNABB_INSTANCE_LAUNCH_TEMPLATE
        config_file_name = SNABB_FILENAME + str(instance_id) + '.cfg'
        pci_path = SNABB_PCI_PATH + str(instance_id)
        mac_path = SNABB_MAC_PATH + str(instance_id)
        # Read the files
        mac_id = ''
        pci_id = ''
        try:
            with open(pci_path) as f:
                pci_id = f.read().strip().split('/')[0]
        except Exception as e:
            LOG.info('Failed to read the file %s due to exception: %s' %
                     (pci_path, e.message))
            return False
        try:
            with open(mac_path) as f:
                mac_id = f.read().strip()
        except Exception as e:
            LOG.info('Failed to read the file %s due to exception: %s' %
                     (mac_path, e.message))
            return False

        cmd = s.substitute(cfg=config_file_name, id=instance_id,
                     pci=pci_id, mac=mac_id)
        # TODO launch the process if required
	output = 0
	try:
            output = subprocess.check_output(cmd, shell=True)
            LOG.info('Tried to restart the snabb instance id %s, returned %s' %
                 (str(instance_id), str(output)))
	except Exception as e:
	    LOG.info("Failed to start the snabb instance, exception %s" %e.message)

        return output


    def bindAction(self, binding_file):
        # Compile the binding file
        signal_sent = False
        # Find the snabb instances and send sighup to all the instances
        p = subprocess.Popen(['ps', '-axw'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        snabb_search_string = SNABB_PROCESS_SEARCH_STRING
        for lines in out.splitlines():
            if snabb_search_string in lines:
                pid = int(lines.split(None, 1)[0])
                cmd = r"/usr/local/bin/snabb lwaftr control " + str(pid)+" reload"
                try:
                    output = subprocess.check_output(cmd, shell=True)
                    LOG.info('Sent SIGHUP to instance %d' %pid)
                except Exception as e:
                    LOG.info("Failed to send SIGHUP to instance %d" %pid)
                signal_sent = True
                LOG.info("Successfully sent SIGHUP to the snabb instance")
                break
        return signal_sent

    def cfgAction(self, instance_id=None, restart_action=True):
        # Find the specific snabb instance or all depending on instance_id argument
        # Kill the relevant instances
        signal_sent = False
        if instance_id is not None and restart_action is False:
            cfg_file_name = SNABB_FILENAME + str(instance_id) + '.cfg'
            conf_file_name = SNABB_FILENAME + str(instance_id) + '.conf'
	    try:
                os.remove(cfg_file_name)
                os.remove(conf_file_name)
	    except OSError:
		pass
            LOG.info("Removed the file %s and %s as the instance %d was deleted" % (
                cfg_file_name, conf_file_name, int(instance_id)))

        p = subprocess.Popen(['ps', '-axw'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        if instance_id is not None:
            snabb_search_string = SNABB_PROCESS_SEARCH_STRING + \
                str(instance_id)
        else:
            snabb_search_string = SNABB_PROCESS_SEARCH_STRING
        for lines in out.splitlines():
            if snabb_search_string in lines:
                pid = int(lines.split(None, 1)[0])
                os.kill(pid, signal.SIGTERM)
                LOG.info("Successfully sent SIGTERM to the snabb instance %s" % str(
                    lines.split(None, 1)[1]))
                signal_sent = True

        return signal_sent

    def deleteAction(self):
        # Delete the cfg files
        snabb_search_string = SNABB_PROCESS_SEARCH_STRING
        for f in os.listdir('/tmp'):
            if snabb_search_string in f:
                LOG.info('Deleting the file %s' % str(f))
		try:
                    os.remove(os.path.join('/tmp/', f))
		except OSError:
		    pass
        signal_sent = False
        p = subprocess.Popen(['ps', '-axw'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        for lines in out.splitlines():
            if snabb_search_string in lines:
                pid = int(lines.split(None, 1)[0])
                os.kill(pid, signal.SIGTERM)
                LOG.info("Successfully sent SIGTERM to the snabb instance %s" % str(
                    lines.split(None, 1)[1]))
                signal_sent = True
        return signal_sent
