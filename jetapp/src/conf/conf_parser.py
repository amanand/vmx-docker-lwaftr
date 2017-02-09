
import os
from jinja2 import Environment, FileSystemLoader
from common.mylogging import LOG
from conf_action import ConfAction
from conf_globals import *
import filecmp
from collections import OrderedDict
from ftplib import FTP
import re


class ParseNotification:

    def __init__(self, device):
        self.binding_changed = False
        self.old_cfg = None
        self.old_conf = None
        self.old_binding_filename = None
        self._dev = device
        # All the instances will be added to this list
        self.instances = {}

    @staticmethod
    def myget(dictitem,key):
        for keys in dictitem.keys():
            if keys.split(':')[-1] == key:
                value = dictitem.get(keys)
                LOG.info("Found key %s, value = %s" %(key,value))
                return value
        LOG.info('Key %s not present' % str(key))
        return None


    def get_binding_file(self, remote_filename, local_filename):
        try:
            localfd = open(local_filename, 'w+')
            ftp = FTP(self._dev._host)
            ftp.login(user=self._dev._auth_user, passwd=self._dev._auth_pwd)
            LOG.info("FTP get the file %s" % remote_filename)
            ftp.retrbinary('RETR %s' % remote_filename, localfd.write)
        except Exception as e:
            LOG.critical(
                'Failed to connect to the device: exception: %s' % e.message)
            return False
        LOG.info('Successfully copied the file %s' % remote_filename)
        return True

    def dictdiff(self, old_dict, new_dict):
        if old_dict is None:
            return True
        if new_dict is None:
            return True

        for key in old_dict.keys():
            if (not new_dict.has_key(key)):
                return True
            elif (old_dict[key] != new_dict[key]):
                return True
        for key in new_dict.keys():
            if (not old_dict.has_key(key)):
                return True
        return False

    def write_file(self, filename, templatename, dictitems):
        PATH = os.path.dirname(os.path.abspath(__file__))
        TEMPLATE_ENVIRONMENT = Environment(
            autoescape=True,
            loader=FileSystemLoader(os.path.join(PATH, 'template')),
            trim_blocks=True,
            lstrip_blocks=False)
        try:
            with open(filename, 'w') as f:
                btext = TEMPLATE_ENVIRONMENT.get_template(
                    templatename).render(context=dictitems)
                f.write(btext)
                LOG.info("Successfully written %s" % str(filename))
            return True
        except Exception as e:
            LOG.critical("Failed to write the file %s, exception: %s" %
                         (str(filename), e.message))
            return False

    def write_snabb_conf_file(self, config_dict, instance_id):
        SNABB_CONF_FILE = SNABB_FILENAME + str(instance_id) + '.conf'
        return self.write_file(SNABB_CONF_FILE, SNABB_CONF_TEMPLATE, config_dict)

    def write_snabb_cfg_file(self, cfg_dict, instance_id):
        SNABB_CFG_FILE = SNABB_FILENAME + str(instance_id) + '.cfg'
        return self.write_file(SNABB_CFG_FILE, SNABB_CFG_TEMPLATE, cfg_dict)

    def parse_for_binding(self, config_dict, action_handler):
        br_addresses = OrderedDict()
        br_address_idx = -1
        softwires = []
        addresses = {}
        remote_binding_table_filename = self.myget(config_dict['binding']['br'],'binding-table-file')
        # This section will take care of the binding files and binding table entries
        # Fetch this binding file from the device
        if remote_binding_table_filename is not "None":
            # New binding table is provided by the user
            new_binding_file = r'/tmp/snabbvmx.binding.new'
            # touch the new file
            open(new_binding_file, 'w+').close()
            if self.get_binding_file(remote_binding_table_filename, new_binding_file):
                # Copy the remote file to new_binding_file and create the softwires, psid and br_address tables
                # Then add to these tables the new entries from the configuration
                # At the end compare the new binding file with the old one to see if binding entries have changed
                with open(new_binding_file, 'r') as f:
                    # Walk over the file to create the binding entries
                    regex_br_address = r"softwires_([\w:]+)"
                    regex_br_entries = r"([\w:]+)+\s+(\d+.\d+.\d+.\d+),(\d+),(\d+),(\d+)"
                    for lines in f.readlines():
                        if re.search(regex_br_address, lines):
                            match = re.search(regex_br_address, lines)
                            br_addresses[match.group(0).split(
                                '_')[1]] = br_address_idx + 1
                            br_address_idx += 1
                        elif re.search(regex_br_entries, lines):
                            match = re.search(regex_br_entries, lines)
                            shift = 16 - int(match.group(4)) - \
                                int(match.group(5))
                            softwires.append('{ ipv4=%s, psid=%s, b4=%s, aftr=%s }' %
                                             (match.group(2),match.group(3),
                                              match.group(1),br_address_idx))
                            if shift > 0:
                                addresses[str(match.group(2))] = "{psid_length=%s, shift=%d}" % (match.group(4),
                                                                                                 shift)
                            else:
                                addresses[
                                    str(match.group(2))] = "{psid_length=%s}" % match.group(4)

                        else:
                            LOG.info("Ignoring this line: %s" % lines)
                os.remove(new_binding_file)
            else:
                LOG.critical(
                    'Failed to copy remote binding file onto the local disk')
        else:
            LOG.info("No binding table info found in the config")

        # Now parse the snabb config to see if there is any binding table entry
        new_instance_list = config_dict['binding']['br']['br-instances']['br-instance']
        for instances in new_instance_list:
            bt = self.myget(instances,'binding-table')
            if bt is not None:
                bte = self.myget(bt,'binding-entry')
                if bte is not None:
                    for items in bte:
                        binding_ipv6_info = self.myget(items,"binding-ipv6info")
                        ipv4 = self.myget(items,"binding-ipv4-addr")
                        b4_address = self.myget(items,"br-ipv6-addr")
                        portset = self.myget(items,'port-set')
                        psid = self.myget(portset,"psid")
                        psid_len = self.myget(portset,"psid-len")
                        offset = self.myget(portset,"psid-offset")
                        shift = 16-psid_len-offset
                        if binding_ipv6_info is not None and ipv4 is not None and b4_address is not None:
                            if shift > 0:
                                addresses[ipv4] = "{psid_length=%s, shift=%d}" % (psid_len, shift)
                            else:
                                addresses[ipv4] = "{psid_length=%s}" %psid_len
                            if b4_address in br_addresses.keys():
                                aftr = br_addresses[b4_address]
                            else:
                                aftr = len(br_addresses)
                                br_addresses[b4_address] = aftr

                            softwires.append('{ ipv4=%s, psid=%s, b4=%s, aftr=%s }' % (
                                ipv4,psid,binding_ipv6_info,aftr))
                        else:
                            LOG.info("Incomplete binding table entry in the configuration %s" %str(items))
                else:
                    LOG.info("Empty binding table entry in the configuration")
            else:
                LOG.info("No binding table configuration present")

        # Write it into a file
        with open(SNABB_BINDING_FILENAME_TMP, 'w+') as nf:
            nf.write('psid_map {\n')
            for items in sorted(addresses.iterkeys()):
                nf.write("\t" + items + " " + addresses[items] + '\n')
            nf.write("}\nbr_addresses {\n")
            for items in br_addresses.keys():
                nf.write("\t" + items + ",\n")
            nf.write("}\nsoftwires {\n")
            for items in softwires:
                nf.write("\t" + items + "\n")
            nf.write("}")

        # Determine if this binding file is different from existing
        # file
        if self.old_binding_filename is None:
            self.old_binding_filename = SNABB_BINDING_FILENAME
            os.rename(SNABB_BINDING_FILENAME_TMP, self.old_binding_filename)
            self.binding_changed = True
            LOG.info("Old binding file not present, so creating a new binding file")
        elif not filecmp.cmp(self.old_binding_filename, SNABB_BINDING_FILENAME_TMP):
            os.rename(SNABB_BINDING_FILENAME_TMP, self.old_binding_filename)
            self.binding_changed = True
            LOG.info("Binding Table has changed")
        else:
            LOG.info("Binding Table has not changed")

        if (self.binding_changed):
            self.binding_changed = False
            # Send a sighup to all the snabb instances
            # LOG.info('Binding entries have changed')
            rc = action_handler.bindAction(self.old_binding_filename)
            # if not rc:
            #     LOG.critical("Failed to send SIGHUP to the Snabb instances")
            # else:
            #     LOG.info("Successfully sent SIGHUP to the Snabb instances")
        return


    def parse_snabb_config(self, config_dict):
        if config_dict.get('purge', None) is not None:
            # Call the confAction to kill all the Snabb applications after
            # deleting the cfg/conf/binding files
            self.old_cfg = None
            self.old_conf = None
            self.old_binding_filename = None
            self.instances = {}
            ca = ConfAction()
            ca.deleteAction()
            return

        # At first lets clear the present flag in all the instances
        for keys in self.instances:
            self.instances[keys] = 0

        # Action handler to commit actions for conf/cfg/binding changes
        action_handler = ConfAction()

        # First the binding entry changes
        self.parse_for_binding(config_dict, action_handler)

        # description is same for all the instances in the YANG schema
        cfg_dict = {}
        conf_dict = {}
        # Parse the config and cfg changes
        descr = self.myget(config_dict,'description')
        new_instance_list = config_dict['binding']['br']['br-instances']['br-instance']
        for instances in new_instance_list:
            # TODO try except loop has to be implemented
            instance_id = self.myget(instances,'id')
            # Verify that the old config contains this instance, if not then we
            # need to delete this instance
            self.instances[instance_id] = 1
            cfg_dict['id'] = instance_id
            cfg_dict['cnf_file_name'] = SNABB_FILENAME.split('/')[-1] + str(instance_id) + '.conf'

            cfg_dict['ipv4_address'] = self.myget(instances,'ipv4_address')
            cfg_dict['ipv4_desc'] = descr
            cfg_dict['ipv4_cache_rate'] = self.myget(instances,'cache_refresh_interval')
            cfg_dict['ipv4_ingress_filter'] = self.myget(instances, 'ipv4_ingress_filter')
            cfg_dict['ipv4_egress_filter'] = self.myget(instances, 'ipv4_egress_filter')
            cfg_dict['fragmentation'] = self.myget(instances, 'fragmentation')


            cfg_dict['ipv6_address'] = self.myget(instances,'ipv6_address')
            cfg_dict['ipv6_desc'] = descr
            cfg_dict['ipv6_cache_rate'] = self.myget(instances,'cache_refresh_interval')
            cfg_dict['ipv6_ingress_filter'] = self.myget(instances, 'ipv6_ingress_filter')
            cfg_dict['ipv6_egress_filter'] = self.myget(instances, 'ipv6_egress_filter')
            cfg_dict['fragmentation'] = self.myget(instances, 'fragmentation')

            cfg_dict['ingress_drop_interval'] = self.myget(instances,'ingress_drop_interval')
            cfg_dict['ingress_drop_monitor'] = self.myget(instances,'ingress_drop_monitor')
            cfg_dict['ingress_drop_threshold'] = self.myget(instances, 'ingress_drop_threshold')
            cfg_dict['ingress_drop_wait'] = self.myget(instances,'ingress_drop_wait')
            cfg_dict['ring_buffer_size'] = None

            # Parse the conf file attributes
            conf_dict['id'] = instance_id
            if self.old_binding_filename is not None:
                conf_dict['binding_table'] = str(self.old_binding_filename).split('/')[-1]
            else:
                conf_dict['binding_table'] = None

            mac_path = SNABB_MAC_PATH + str(instance_id)
            # Read the files
            mac_id = "00:00:00:00:00:00"
            try:
                with open(mac_path) as f:
                    mac_id = f.read().strip()
            except Exception as e:
                LOG.info('Failed to read the file %s due to exception: %s' %
                         (mac_path, e.message))

            conf_dict['v4_vlan_tag'] = self.myget(instances,'v4_vlan_tag')
            conf_dict['v6_vlan_tag'] = self.myget(instances, 'v6_vlan_tag')
            if self.myget(instances,'v4_vlan_tag') is not None or self.myget(instances, 'v6_vlan_tag') is not None:
                conf_dict['vlan_tagging'] = 'true'
            else:
                conf_dict['vlan_tagging'] = 'false'

            conf_dict['policy_icmpv4_incoming'] = self.myget(instances, 'policy_icmpv4_incoming')
            conf_dict['policy_icmpv4_outgoing'] = self.myget(instances, 'policy_icmpv4_outgoing')
            conf_dict['policy_icmpv6_incoming'] = self.myget(instances,'policy_icmpv6_incoming')
            conf_dict['policy_icmpv6_outgoing'] = self.myget(instances, 'policy_icmpv6_outgoing')
            conf_dict['max_fragments_per_reassembly_packet'] = self.myget(instances, 'max_fragments_per_reassembly_packet')
            conf_dict['max_ipv4_reassembly_packets'] = self.myget(instances, 'max_ipv4_reassembly_packets')
            conf_dict['max_ipv6_reassembly_packets'] = self.myget(instances, 'max_ipv6_reassembly_packets')
            conf_dict['icmpv6_rate_limiter_n_packets'] = self.myget(instances, 'icmpv6_rate_limiter_n_packets')
            conf_dict['icmpv6_rate_limiter_n_seconds'] = self.myget(instances, 'icmpv6_rate_limiter_n_seconds')
            conf_dict['ipv4_address'] = self.myget(instances, 'ipv4_address')
            conf_dict['ipv6_mtu'] = self.myget(instances,"tunnel-path-mru")
            conf_dict['ipv4_mtu'] = self.myget(instances,"tunnel-payload-mtu")
            conf_dict['hairpinning'] = self.myget(instances,"hairpinning")

            #TODO Why are the following values hardcoded
            conf_dict['ipv6_address'] = '2001:db8::1'
            conf_dict['inet_mac'] = '02:02:02:02:02:02'
            conf_dict['next_hop6_mac'] = '02:02:02:02:02:02'

            # TODO these parameters are not defined
            conf_dict['aftr_mac_inet_side'] = mac_id
            conf_dict['aftr_mac_b4_side'] = mac_id

            # Take action based on whether the cfg or conf files have changed
            # or not
            ret_cfg, ret_conf = False, False
            new_cfg_id_present = False
            new_conf_id_present = False
            cnt = 0
            cfg_changed = False
            LOG.debug('New cfg dict = %s' % str(cfg_dict))
            if self.old_cfg is None:
                ret_cfg = self.write_snabb_cfg_file(cfg_dict, instance_id)
                if not ret_cfg:
                    LOG.critical("Failed to write the cfg file")
                    return
            else:
                # Add the new cfg to the old_cfg dictionary
                cnt = 0
                for cfg_instance in self.old_cfg:
                    if cfg_instance['id'] == cfg_dict['id']:
                        # Check if the configuration has changed for this new instance
                        if cmp(cfg_instance, cfg_dict) != 0:
                            cfg_changed = True
                            self.old_cfg[cnt] = cfg_dict
                            new_cfg_id_present = True
                            LOG.info("Cfg dictionary has changed")
                            break
                        else:
                            new_cfg_id_present = True
                            cfg_changed = False
                            LOG.info("Cfg dictionary has not changed")
                            break
                    cnt += 1
                # New cfg is not in the existing dict, add it
                if not new_cfg_id_present:
                    self.old_cfg.append(cfg_dict)
                    cfg_changed = True
                if (cfg_changed):
                    ret_cfg = self.write_snabb_cfg_file(cfg_dict, instance_id)
                    if not ret_cfg:
                        LOG.critical("Failed to write the cfg file")
                        return

            if self.old_conf is None:
                ret_conf = self.write_snabb_conf_file(conf_dict, instance_id)
                if not ret_conf:
                    LOG.critical("Failed to write the conf file")
                    return
            else:
                cnt = 0
                conf_changed = False
                new_conf_id_present = False
                for conf_instance in self.old_conf:
                    if (conf_instance['id'] == conf_dict['id']):
                        if cmp(conf_instance, conf_dict) != 0:
                            conf_changed = True
                            self.old_conf[cnt] = conf_dict
                            new_conf_id_present = True
                            LOG.info("Conf dictionary has changed")
                            break
                        else:
                            new_conf_id_present = True
                            conf_changed = False
                            LOG.info("Conf dictionary has not changed")
                    cnt = + 1
                if not new_conf_id_present:
                    self.old_conf.append(conf_dict)
                    conf_changed = True
                if (conf_changed):
                    ret_conf = self.write_snabb_conf_file(
                        conf_dict, instance_id)
                    if not ret_conf:
                        LOG.critical("Failed to write the conf file")
                        return

            if ret_conf or ret_cfg:
                # Assume that the instances list is populated here
                if not new_cfg_id_present and not new_conf_id_present:
                    # It is a new instance, so start it
                    ret = action_handler.start_snabb_instance(instance_id)
                else:
                    ret = action_handler.cfgAction(instance_id)
                    if not ret:
                        LOG.critical("Failed to restart the Snabb instance")
            else:
                LOG.info("No config change hence did not restart Snabb instance %d id" %str(instance_id))

        # Few of the instances might have been deleted, we need to kill those
        # instances
        for keys in self.instances:
            if self.instances[keys] == 0:
                # Remove the old_cfg item which is for this id
                cnt = 0
                for cfg_instance in self.old_cfg:
                    if cfg_instance['id'] == keys:
                        del self.old_cfg[cnt]
                        break
                    cnt += 1

                cnt = 0
                for conf_instance in self.old_conf:
                    if conf_instance['id'] == keys:
                        del self.old_conf[cnt]
                        break
                    cnt += 1
                # Kill this instance
                LOG.info(
                    "Instance id %d is not present, need to kill it" % int(keys))
                ret = action_handler.cfgAction(keys, False)
                if not ret:
                    LOG.critical(
                        "Failed to kill the Snabb instance %d" % int(keys))

        return

    def __call__(self):
        LOG.info("Entered ParseNotification")
        global dispQ
        while True:
            # process the notification message
            config_dict = dispQ.get()
            dispQ.task_done()
            LOG.info("dequeued %s" % str(config_dict))
            self.parse_snabb_config(config_dict)
