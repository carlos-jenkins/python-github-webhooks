# -*- coding: utf-8 -*-
"""Application configuration."""
import os
from datetime import timedelta


class Config(object):
    """Base configuration."""
    GITHUB_OWNER = 'adeo'
    PIPELINES_DEFAULT_VERSION = 'latest'
    PIPELINES_VERSION = os.getenv("PIPELINES_VERSION", 'latest')
    PIPELINES_REPO = 'cloud-build-pipelines'
    LMESCI_FILENAME = '.lmes-ci.yaml'



