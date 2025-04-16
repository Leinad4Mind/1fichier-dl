#!/usr/bin/env python3
import os
import sys
import logging
from core.gui import gui

log_level = logging.DEBUG
if getattr(sys, 'frozen', False):
    # If the script is running as a bundled executable (e.g., PyInstaller)
    log_dir = os.path.join(os.path.dirname(sys.executable), 'app')
    log_level = logging.INFO
else:
    # If the script is running in a development environment
    log_dir = os.path.join(os.path.dirname(__file__), 'app')

if __name__ == '__main__':
    try:
        # Check if the log directory exists, and if not, create it
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(log_dir, 'logs.txt')

        logging.basicConfig(filename=log_file,
                            level=log_level, filemode='w')
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        logger = logging.getLogger(__name__)
        gui.Gui()
    except Exception as e:
        # Call handle_exit() when an exception occurs
        gui.Gui().actions.handle_exit()
        logger = logging.getLogger(__name__)  # Move logger definition here
        logger.debug(__name__+' Exception')
        logger.exception(e)
