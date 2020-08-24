#!/usr/local/bin/python3
#vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
'''
------------------------------------------------------------------------------------------------------------

 Description:

    Automation demo for SEs

 Requirements:
   Python3 with re, ipaddress, requests and sqlite3 modules

 Author: Chris Marrison

 Date Last Updated: 20200822

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
__version__ = '0.0.5'
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
    ini_keys = ['owner', 'customer', 'postfix', 'tld', 'dns_view', 
                'dns_domain', 'no_of_records', 'ip_space', 'no_of_networks', 
                'container_cidr', 'cidr' ]

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


"""
def create_range(b1ddi, config, space, network):
    '''
    Create DHCP Range

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
    body = '{ "name": "' + config['ip_space'] + '",' + tag_body +' }'
    log.debug("Body:{}".format(body))

    log.info("Creating Range {}".format(config['ip_space']))
        response = b1ddi.create('/ipam/ip_space', body=body)
        if response.status_code in b1ddi.return_codes_ok:
            log.info("IP_Space {} Created".format(config['ip_space']))
            status = True
        else:
            log.warning("IP Space {} not created".format(config['ip_space']))
            log.debug("Return code: {}".format(response.status_code))
            log.debug("Return body: {}".format(response.text))
    else: 

    return status
"""

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


def create_networks(b1ddi, config, base_net="192.168"):
    '''
    Create Subnets

    Parameters:
        b1ddi (obj): bloxone.b1ddi object
        config (obj): ini config object
    
    Returns:
        status (bool): True if successful
    '''
    status = False
    create_block = True

    # Get id of ip_space
    log.info("---- Create Address Block and subnets ----")
    space = b1ddi.get_id('/ipam/ip_space', key="name", 
                        value=config['ip_space'], include_path=True)
    if space:
        log.info("IP Space id found: {}".format(space))

        tag_body = create_tag_body(config['owner'])

        for n in (range(int(config['no_of_networks']))):
            network = base_net + "." + str(n) + ".0"
            if create_block:
                cidr = config['container_cidr']
                body = ( '{ "address": "' + network + '", '
                        + '"cidr": "' + cidr + '", '
                        + '"space": "' + space + '", '
                        + tag_body + ' }' )
                log.debug("Body:{}".format(body))
                log.info("Creating Addresses block {}/{}".format(network, cidr))
                response = b1ddi.create('/ipam/address_block', body=body)
            else:
                cidr = config['cidr']
                body = ( '{ "address": "' + network + '", '
                        + '"cidr": "' + cidr + '", '
                        + '"space": "' + space + '", '
                        + tag_body + ' }' )
                log.debug("Body:{}".format(body))
                log.info("Creating Subnet {}/{}".format(network, cidr))
                response = b1ddi.create('/ipam/subnet', body=body)

            if response.status_code in b1ddi.return_codes_ok:
                if create_block:
                    log.info("+++ Address block {}/{} created".format(network, cidr))
                    create_block = False
                else:
                    log.info("+++ Subnet {}/{} successfully created".format(network, cidr))
                    # create_range(b1ddi, config, space, network)
                    # create_ips(b1ddi, config, network)

                status = True
            else:
                log.warning("--- Subnet {}/{} not created".format(network, cidr))
                log.debug("Return code: {}".format(response.status_code))
                log.debug("Return body: {}".format(response.text))
    else:
        log.warning("IP Space {} does not exist".format(config['ip_space']))

    return status


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
            log.info("------ Creating Demo Data ------")
            exitcode = create_demo(b1ddi, config)
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