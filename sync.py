#!/usr/bin/env python

#tooltool is a lookaside cache implemented in Python
#Copyright (C) 2013 Mozilla Foundation
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation version 2
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import logging
import logging.config
import json
import os

LOG_FILENAME = 'tooltool_sync.log'
DEFAULT_LOG_LEVEL=logging.DEBUG
logging.basicConfig(filename=LOG_FILENAME,
                        level=DEFAULT_LOG_LEVEL,
                        format='%(asctime)s - %(levelname)s - %(message)s'
                        )


CONFIG_FILENAME = 'config.json'
LOG_LEVELS={"DEBUG":logging.DEBUG, "INFO":logging.INFO, "WARNING":logging.WARNING, "ERROR":logging.ERROR, "CRITICAL":logging.CRITICAL}

def validate_config(config):

    matching={}
    log_level=DEFAULT_LOG_LEVEL
    root=""
    
    if config['root'] and os.path.exists(config['root']) and os.path.isdir(config['root']) :
        root=config['root']
    else:
        logging.CRITICAL("The configuration file does not contain a valid root folder")
        exit(1)
    
    if config['matching'] and type(config['matching']) is dict:
        matching=config['matching']
    else:
        logging.CRITICAL("The configuration file does not contain a matching section (a dictionary)")
        exit(1)
        
    
    if "log_level" in config:
        if config["log_level"].upper()  in LOG_LEVELS:
            log_level=LOG_LEVELS[config["log_level"].upper()]
        else:
            logging.WARNING("The configuration file does not contain a log_level.")


    return root, matching, log_level

def load_config():
    config={}
    try:
        f= open(CONFIG_FILENAME, 'r')
        config = json.load(f)
        f.close()
    except IOError as e:
        logging.critical("Impossible to read configuration file %s; I/O error(%s): %s" % (CONFIG_FILENAME,e.errno, e.strerror))
        exit(1)
    return validate_config(config)
    

def main():

    root, matching, log_level=load_config()
    logging.basicConfig(filename=LOG_FILENAME,
                        level=log_level,
                        )
    logging.info("test")


        





if __name__ == "__main__":
    main()
