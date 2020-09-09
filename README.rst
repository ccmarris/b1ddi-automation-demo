=====================
B1DDI Demo Automation
=====================

Version: 0.1.0
Author: Chris Marrison
Email: chris@infoblox.com

Description
-----------

These -set of- scripts are designed to simplify and standardise the use of the Bloxone
Infoblox SE organisations for the purposes of customer demos and of automation
using the BloxOne DDI app.

This includes the creation of a 'demo' set of data and the clean up (removal) of
this environment once you have finished wth the data.

The scripts utilise a customisable ini file for this automation.

Prerequisites
-------------

Python 3.6 or above

Non-standard modules:

    - bloxone 0.5.6+

The latest version of the bloxone module is available on PyPI and can simply be
installed using::

    pip3 install bloxone --user

To upgrade to the latest version::

    pip3 install bloxone --user --upgrade

Complete list of modules::

    import bloxone
    import os
    import json
    import argparse
    import logging


Basic Configuration
-------------------

The scripts and the bloxone module use an ini file for configuration. For
simplicity the configuration for both the scripts and module is shared within 
single ini file. 

A sample is provided called demo.ini. Unless an alternative is specified on the
command line, the script will automatically use the demo.ini from the current 
working directory if available. 

The format of the ini file is::

    [BloxOne]
    url = 'https://csp.infoblox.com'
    api_version = 'v1'
    api_key = '<Your Region API Key Here>'

    [B1DDI_Demo]
    owner = <username>
    customer = <customer name>
    postfix = %(customer)s
    tld = com
    dns_view = %(owner)s-%(postfix)s-demo
    dns_domain = %(customer)s.%(tld)s
    no_of_records = 20
    ip_space = %(owner)s-%(postfix)s-demo
    base_net = 192.168.0.0
    no_of_networks = 10
    no_of_ips = 5
    container_cidr = 16
    cidr = 24
    
    
Once your API key is configured, your username and customer name are set
you are ready to run the scripts with the remaining defaults or tweak as
you need!

As can be seen the ini file is used to form the naming conventions and Owner
tagging to both ensure that it is easy to identify who the demo data belongs
to and ensure this is identified by automated clean-up scripts.

You can customise the number of networks, subnet masks, and the first base 
network for the auto created demo data, as well as, the number of ips and 
hosts to be created.

.. note::

Basic checks of of the base network and CIDR prefix lengths is performed by
the script. 

Usage
-----

The two core scripts are *create_demo.py* and *delete_demo.py*.

Both support -h or --help on the command line to access the options available::

    $ ./b1ddi-demo-automation.py --help
    usage: b1ddi-demo-automation.py [-h] [-c CONFIG] [-d] [-r]

    SE Automation Demo - Create Demo

    optional arguments:
    -h, --help            show this help message and exit
    -c CONFIG, --config CONFIG
                            Overide Config file
    -d, --debug           Enable debug messages
    -r, --remove          Clean-up demo data
    
With all the configuration and customisation performed within the ini file the script
becomes very simple to run with effectively two modes:

    1. Create mode
    2. Clean up mode

To run in create mode, simply point the script at the appropriate ini fle as required.
For example::

    % ./b1ddi-demo-automation.py
    % ./b1ddi-demo-automation.py -c <path to inifile>
    % ./b1ddi-demo-automation.py -c ~/configs/customer.ini
    
To run in clean-up mode simply add *--remove* or *-r* to the command line::

    % ./b1ddi-demo-automation.py --remove
    % ./b1ddi-demo-automation.py -c <path to inifile> --remove
    % ./b1ddi-demo-automation.py -c ~/configs/customer.ini --remove


The details
-----------

In create mode the script creates an IP Space with an address block, subnets are then 
created wth ranges and IP reservations. These are based on the following elements in 
the ini file::

    ip_space = %(owner)s-%(postfix)s-demo
    base_net = 192.168.0.0
    no_of_networks = 10
    no_of_ips = 5
    container_cidr = 16
    cidr = 24

The ranges will effectively take up the top 50% of the subnet, whilst the number
of IP reservations is ether be the *no_of_ips* or 25% of the subnet, which ever
is the smaller number.

Configuration checking is performed to confirm that *base_net* is a valid IPv4
address and both *container_cidr* and *cidr* are suitable and larger than a 
/28 and /29 respectively.

A DNS View is then also created with an authoritative zone and reverse zone 
for the *base_net* (adjusted for byte boundaries) and a set of A records wth
corresponding PTRs.

These are controlled by the following keys in the ini file::

    tld = com
    dns_view = %(owner)s-%(postfix)s-demo
    dns_domain = %(customer)s.%(tld)s
    no_of_records = 20

Output
------

Section headers are represented using::

     ============ Section Heading ============

Subsections are represented using::

    ------------ Subsection ------------

Although the majority of messages are general information, certain
message use the convention of "+++ message" for positive messages about
the configuration, whilst negative messages use "--- message". For example::

    INFO: +++ Range created in network 192.168.0.0/24
    INFO: --- :

Prior to the report the raw summaries from each of the checking functions is 
output. Again this can be useful to determine why something did not pass, 
before looking at the specific log messages or in the BloxOne DDI GUI.

The second type of output is the summary report itself in tabular format. The 
table is best viewed on a wide screen with a terminal set to 180 characters
wide.

Example output can be found in the files *example1.txt* and *example2.txt*.

In addition to the output to console the :option:`-o` or :option:`--out`
can be used to create a <username>.log and <username>.csv output file.

Limitations
-----------

There are several limitations to the automation: 

    - No API for Join Tokens

    - Subnets and Ranges are not checked for tags

    - Other Misc objects not specific to the training are not checked

    - The value of the location tags are not verified due to international 
    differences
    
    - API bugs, although there is a workaround implemented for one of these

    - Owner and Location tags are combined due to summarisation of multiple 
    objects of the same type - details, however, can be found in the logging 
    messages.


Some of these are due to current limitation within the API or current lack 
of formally documented calls and very occasionally API bugs.

It is therefore important that, especially in the instance of a False being
indicated in the summary report that this is confirmed in the GUI. Of course
limitation also mean that you may also wish to check tags on additional items,
rather than just the key ones checked during the automation.


License
-------

This project, and the bloxone module are licensed under the 2-Cluse BSD License
- please see LICENSE file for details.

Aknowledgements
---------------

Thanks to Geoff for his input to the bloxone module, and for letting me
undertake this project. Thanks John Steele for his help in testing, prior to
'publishing' to the team.

Finally, that to the whole team for all the extra work helping with this
training.