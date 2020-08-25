#!/usr/local/bin/python3
#vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
'''
------------------------------------------------------------------------------------------------------------

 Description:

    Automation demo for SEs

 Requirements:
   Python3 with re, ipaddress, requests and sqlite3 modules

 Author: Chris Marrison

 Date Last Updated: 20200825

 Todo:
    [ ] Too much to list

 Copyright (c) 2020 Chris Marrison / Infoblox

 Redistribution and use in source and binary forms,
 with or without modification, are permitted provided
 that the following conditions are met:

 1. Redistributions of source code must retain the above copyright
 notice, this list of conditions and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright
 notice, this list of conditions and the following disclaimer in the
 documentation and/or other materials provided with the distribution.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 POSSIBILITY OF SUCH DAMAGE.

------------------------------------------------------------------------------------------------------------
'''
__version__ = '0.1.1'
__author__ = 'Chris Marrison'
__author_email__ = 'chris@infoblox.com'

import logging
import os
import sys
import json
import bloxone
import argparse
import configparser
import datetime
import ipaddress


# Global Variables
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
# console_handler = logging.StreamHandler(sys.stdout)
# log.addHandler(console_handler)

def parseargs():
    '''
    Parse Arguments Using argparse

    Parameters:
        None

    Returns:
        Returns parsed arguments
    '''
    parse = argparse.ArgumentParser(description='SE Automation Demo - Create Demo')
    parse.add_argument('-o', '--output', action='store_true', 
                        help="Ouput CSV and log to files <username>.csv and .log") 
    parse.add_argument('-c', '--config', type=str, default='demo.ini',
                        help="Overide Config file")
    parse.add_argument('-d', '--debug', action='store_true', 
                        help="Enable debug messages")
    parse.add_argument('-r', '--remove', action='store_true', 
                        help="Clean-up demo data")

    return parse.parse_args()


def setup_logging(level, usefile=False):
    '''
     Set up logging

     Parameters:
        advanced (bool): True or False.

     Returns:
        None.

    '''

    # Set advanced level
    # if level == "advanced":
     #    logging.addLevelName(15, "advanced")
      #   logging.basicConfig(level=advanced,
       #                      format='%(asctime)s %(levelname)s: %(message)s')
    if level == "debug":
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s')
    else:
        if usefile:
            # Full log format
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s %(levelname)s: %(message)s')
        else:
            # Simple log format
            logging.basicConfig(level=logging.INFO,
                                format='%(levelname)s: %(message)s')

    return


def open_file(filename):
    '''
    Attempt to open output file

    Parameters:
        filename (str): desired filename

    Returns file handler
        handler (file): File handler object
    '''
    if os.path.isfile(filename):
        backup = filename+".bak"
        try:
            shutil.move(filename, backup)
            log.info("Outfile exists moved to {}".format(backup))
            try:
                handler = open(filename, mode='w')
                log.info("Successfully opened output file {}.".format(filename))
            except IOError as err:
                log.error("{}".format(err))
                handler = False
        except:
            logging.warning("Could not back up existing file {}, exiting.".format(filename))
            handler = False
    else:
        try:
            handler = open(filename, mode='w')
            log.info("Opened file {} for invalid lines.".format(filename))
        except IOError as err:
            log.error("{}".format(err))
            handler = False

    return handler



def read_demo_ini(ini_filename):
    '''
    Open and parse ini file

    Parameters:
        ini_filename (str): name of inifile

    Returns:
        config (dict): Dictionary of BloxOne configuration elements

    '''
    # Local Variables
    cfg = configparser.ConfigParser()
    config = {}
    ini_keys = [ 'owner', 'customer', 'postfix', 'tld', 'dns_view', 
                'dns_domain', 'no_of_records', 'ip_space', 'base_net', 
                'no_of_networks', 'no_of_ips', 'container_cidr', 'cidr' ]

    # Attempt to read api_key from ini file
    try:
        cfg.read(ini_filename)
    except configparser.Error as err:
        logging.error(err)

    # Look for demo section
    if 'B1DDI_Demo' in cfg:
        for key in ini_keys:
            # Check for key in BloxOne section
            if key in cfg['B1DDI_Demo']:
                config[key] = cfg['B1DDI_Demo'][key].strip("'\"")
                logging.debug('Key {} found in {}: {}'.format(key, ini_filename, config[key]))
            else:
                logging.warning('Key {} not found in B1DDI_demo section.'.format(key))
                config[key] = ''
    else:
        logging.warning('No B1DDI_demo Section in config file: {}'.format(ini_filename))

    return config


def create_tag_body(owner, **params):
    '''
    Add Owner tag and any others defined in **params

    Parameters:
        owner (str): Typically username
        params (dict): Tag key/value pairs
    
    Returns:
        tags (str): JSON string to append to body
    '''
    now = datetime.datetime.now()  
    datestamp = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    if params:
        tags = params
        tags.update({"Owner": owner})
        tags.update({"Created": datestamp})
        tag_body = '"tags":' + str(tags) 
    else:
        tag_body = ( '"tags": { "Owner" : "' + owner + 
                    '", "Created": "' +  datestamp + '" }' )
    
    log.debug("Tag body: {}".format(tag_body))

    return tag_body


def ip_space(b1ddi, config):
    '''
    Create IP Space

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False

    # Check for existence
    if not b1ddi.get_id('/ipam/ip_space', key="name", value=config['ip_space']):
        log.info("---- Create IP Space ----")
        tag_body = create_tag_body(config['owner'])
        body = '{ "name": "' + config['ip_space'] + '",' + tag_body +' }'
        log.debug("Body:{}".format(body))

        log.info("Creating IP_Space {}".format(config['ip_space']))
        response = b1ddi.create('/ipam/ip_space', body=body)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("IP_Space {} Created".format(config['ip_space']))
            status = True
        else:
            log.warning("IP Space {} not created".format(config['ip_space']))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
    else:
        log.warning("IP Space {} already exists".format(config['ip_space']))
    
    return status


def create_networks(b1ddi, config):
    '''
    Create Subnets

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False

    # Get id of ip_space
    log.info("---- Create Address Block and subnets ----")
    space = b1ddi.get_id('/ipam/ip_space', key="name", 
                        value=config['ip_space'], include_path=True)
    if space:
        log.info("IP Space id found: {}".format(space))

        tag_body = create_tag_body(config['owner'])
        base_net = config['base_net']

        # Create subnets
        cidr = config['container_cidr']
        body = ( '{ "address": "' + base_net + '", '
                + '"cidr": "' + cidr + '", '
                + '"space": "' + space + '", '
                + tag_body + ' }' )
        log.debug("Body:{}".format(body))
        log.info("~~~~ Creating Addresses block {}/{}~~~~ "
                .format(base_net, cidr))
        response = b1ddi.create('/ipam/address_block', body=body)

        if response.status_code in b1ddi.return_codes_ok:
            log.info("+++ Address block {}/{} created".format(base_net, cidr))

            # Create subnets
            network = ipaddress.ip_network(base_net + '/' + cidr)
            # Reset cidr for subnets
            cidr = config['cidr']
            subnet_list = list(network.subnets(new_prefix=int(cidr)))
            if len(subnet_list) < int(config['no_of_networks']):
                nets = len(subnet_list)
                log.warn("Address block only supports {} subnets".format(nets))
            else:
                nets = int(config['no_of_networks'])
            log.info("~~~~ Creating {} subnets ~~~~".format(nets))
            for n in range(nets):
                address = str(subnet_list[n].network_address)
                body = ( '{ "address": "' + address + '", '
                        + '"cidr": "' + cidr + '", '
                        + '"space": "' + space + '", '
                        + tag_body + ' }' )
                log.debug("Body:{}".format(body))
                log.info("Creating Subnet {}/{}".format(address, cidr))
                response = b1ddi.create('/ipam/subnet', body=body)

                if response.status_code in b1ddi.return_codes_ok:
                    log.info("+++ Subnet {}/{} successfully created".format(address, cidr))
                    if populate_network(b1ddi, config, space, subnet_list[n]):
                        log.info("+++ Networks populated.")
                        status = True
                    else:
                        log.warning("Issues populating networks")
                else:
                    log.warning("--- Subnet {}/{} not created".format(network, cidr))
                    log.debug("Return code: {}".format(response.status_code))
                    log.debug("Return body: {}".format(response.text))

        else:
            log.warning("--- Address Block {}/{} not created".format(base_net, cidr))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
    else:
        log.warning("IP Space {} does not exist".format(config['ip_space']))

    return status


def populate_network(b1ddi, config, space, network):
    '''
    Create DHCP Range and IPs

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
        network (str): Network base address
    
    Returns:
        status (bool): True if successful
    '''
    status = False

    log.info("~~~~ Creating Range ~~~~")
    tag_body = create_tag_body(config['owner'])

    net_size = network.num_addresses
    range_size = int(net_size / 2)
    broadcast = network.broadcast_address
    start_ip = str(broadcast - (range_size + 1))
    end_ip = str(broadcast - 1)

    body = ( '{ "start": "' + start_ip + '", "end": "' + end_ip +
            '", "space": "' + space + '", '  + tag_body + ' }' )
    log.debug("Body:{}".format(body))

    log.info("Creating Range start: {}, end: {}".format(start_ip, end_ip))
    response = b1ddi.create('/ipam/range', body=body)
    if response.status_code in b1ddi.return_codes_ok:
        log.info("+++ Range created in network {}".format(str(network)))
        status = True
    else:
        log.warning("--- Range for network {} not created".format(str(network)))
        log.debug("Return code: {}".format(response.status_code))
        log.debug("Return body: {}".format(response.text))

    # Add reservations

    no_of_ips = int(range_size / 2)
    # If number requested is lt than caluculated use configured
    if int(config['no_of_ips']) < no_of_ips:
        no_of_ips = int(config['no_of_ips'])
    log.info("~~~~ Creating {} IPs ~~~~".format(no_of_ips))
    ips = list(network.hosts())
    for ip in range(1, no_of_ips):
        address = str(ips[ip])
        body = ( '{ "address": "' + address + '", "space": "' 
                + space + '", '  + tag_body + ' }' )
        log.debug("Body:{}".format(body))

        log.info("Creating IP Reservation: {}".format(address))
        response = b1ddi.create('/ipam/address', body=body)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("+++ IP {} created".format(address))
            status = True
        else:
            log.warning("--- IP {} not created".format(address))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
            status = False

    return status


def create_ips(b1ddi, config, space, network):
    '''
    Create Fixed Addrs

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
        network (str): Network base address
    
    Returns:
        status (bool): True if successful
    '''
    status = False

    return



def create_hosts(b1ddi, config):
    '''
    Create DNS View

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False
    return


def create_zones(b1ddi, config):
    '''
    Create DNS Zones

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False
    return


def create_dnsview(b1ddi, config):
    '''
    Create DNS Hosts

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False
    return


def create_other(b1ddi, config):
    '''
    Create Other

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False
    return


def create_demo(b1ddi, config):
    '''
    Create the demo data

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful

    '''
    exitcode = 0

    if ip_space(b1ddi, config):
        if create_networks(b1ddi, config):
            log.info("+++ Successfully Populated IP Space")
        else:
            log.error("--- Failed to create networks in {}"
                    .format(config['ip_space']))
            exitcode = 1
    else:
        exitcode = 1
    
    return exitcode


def clean_up(b1ddi, config):
    '''
    Clean Up Demo Data

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    exitcode = 0

    # Check for existence
    id = b1ddi.get_id('/ipam/ip_space', key="name", value=config['ip_space'])
    if id:
        log.info("Deleting IP_Space {}".format(config['ip_space']))
        response = b1ddi.delete('/ipam/ip_space', id=id)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("IP_Space {} deleted".format(config['ip_space']))
        else:
            log.warning("IP Space {} not deleted due to error".format(config['ip_space']))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
            exitcode = 1
    else:
        log.warning("IP Space {} not fonud.".format(config['ip_space']))
        exitcode = 1
    
    return exitcode


def check_config(config):
    '''
    Perform some basic network checks on config

    Parameters:
        config (dict): Config Dictionary
    
    Returns:
        config_ok (bool): True if all good
    '''
    config_ok = True
    container = int(config['container_cidr'])
    subnet = int(config['cidr'])

    if not bloxone.utils.validate_ip(config['base_net']):
        log.error("Base network not valid: {}".format(config['base_net']))
        config_ok = False
    elif container < 8 or container > 28:
        log.error("Container CIDR should be between 8 and 28: {}"
                  .format(container))
        config_ok = False
    elif container >= subnet:
        log.error("Container prefix does not contain subnet prefix: {} vs {}"
                  .format(container, subnet))
        config_ok = False
    elif subnet > 29:
        log.error("Subnet CIDR should be /29 or shorter: {}".format(subnet))
        config_ok = False

    return config_ok

def main():
    '''
    Core Logic
    '''
    exitcode = 0
    reports = {}
    reportfile = None
    usefile = False

    args = parseargs()
    inifile = args.config
    debug = args.debug

    # Read inifile
    config = read_demo_ini(inifile)

    if len(config) > 0:
        # Check for file output
        if args.output:
            outputprefix = config['username']
            usefile = True

        if usefile:
            outfn = outputprefix + ".csv"
            logfn = outputprefix + ".log"
            reportfile = open_file(outfn)
            hdlr = logging.FileHandler(logfn)
            log.addHandler(hdlr)

        if debug:
            setup_logging("debug", usefile=usefile)
        else:
            setup_logging("normal", usefile=usefile)

        log.info("====== B1DDI Automation Demo Version {} ======"
                .format(__version__))
        b1ddi = bloxone.b1ddi(inifile)

        if not args.remove:
            log.info("Checking config...")
            if check_config(config):
                log.info("Config checked out proceeding...")
                log.info("------ Creating Demo Data ------")
                exitcode = create_demo(b1ddi, config)
            else:
                log.error("Config {} contains errors".format(inifile))
                exitcode = 3
        elif args.remove:
            log.info("------ Cleaning Up Demo Data ------")
            exitcode = clean_up(b1ddi, config)
        else:
            log.error("Script Error - something seriously wrong")
            exitcode = 99

    else:
        logging.error("No config found in {}".format(inifile))
        exitcode = 2

    return exitcode

### Main ###
if __name__ == '__main__':
    exitcode = main()
    exit(exitcode)
## End Main ###