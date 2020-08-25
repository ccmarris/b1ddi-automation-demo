=====================
B1DDI Demo Automation
=====================

Version: 0.0.4
Author: Chris Marrison
Email: chris@infoblox.com

Description
-----------

These set of scripts are designed to simply and standardise the use of the Bloxone
Infoblox SE organisations for the purposes of customer demos and of automation
with the BloxOne DDI app.

This includes the creation of a 'demo' set of data and the clean up (deletion) of
this environment.

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


Configuration
-------------

The scripts and the bloxone module use an ini file for configuration. For
simplicity the configuration for the scripts and module is shared within single
ini file. A sample is provided called demo.ini. The script will automatically use
the demo.ini from the current working directory. Alternate ini files can be specified
on the command line.

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
    no_of_records = 50
    ip_space = %(owner)s-%(postfix)s-demo
    base_net = 192.168
    no_of_networks = 10
    container_cidr = 16
    cidr = 24
    
    
Once your API key is configured, your username and customer name are set
you are ready to run the scripts with the remaining defaults or tweak as
you need!

As can be seen the ini file is used to form the naming conventions and Owner
tagging to both ensure that it is easy to identify who the demo data belongs
to and ensure this is identified by automated clean-up scripts.

You can customise the number of networks, subnet masks, and the first two octets
of the base network for the auto created demo data, as well as, the number of 
hosts to be created.

.. note::
   
    Although there is provision for custom cidrs for the container and subnets there
    is currently no checking of these parameters.


Usage
-----

The two core scripts are *create_demo.py* and *delete_demo.py*.

Both support -h or --help on the command line to access the options available.

    
Examples::

    % python3 create_demo.py -c demo.ini
    
    % ./create_demo.py -c demo.ini
    

create_demo.py
~~~~~~~~~~~~~~

This script creates an IP Space, named appropriately based on the ini file. An
address block based on the the *base_net* and *container_cidr* and then sequencially
creates a series of subnets, with ranges and hosts.

A DNS View is then also created with an appropriate authoritative zone and reverse
zones






Section headers are represented using::

     ============ Section Heading ============

Subsections are represented using::

    ------------ Subsection ------------

Although the majority of messages are general information, certain
message use the convention of "+++ message" for positive messages about
the configuration, whilst negative messages use "--- message". For example::

    INFO: +++ Owner tag correctly set.
    INFO: --- Location tag not set

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