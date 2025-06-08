#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimales Logging Setup
"""

import logging
import os
from datetime import datetime


def setup_logger(name='RFIDScanner', log_level='INFO'):
    """Minimales Logger Setup"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))

    # Console Handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler (optional)
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(console_format)
    logger.addHandler(file_handler)

    return logger


def get_logger(name='RFIDScanner'):
    """Logger abrufen"""
    return logging.getLogger(name)