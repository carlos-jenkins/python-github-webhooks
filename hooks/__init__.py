# -*- coding: utf-8 -*-
#
import sys
import importlib

__all__ = ['ping']
# CHECKME: import hooks here
# from . import ping
for hook in __all__:
    importlib.import_module('.%s' % hook, 'hooks')


def get_hooks():
    return [k.replace('hooks.', '') for k in list(sys.modules.keys()) if k.startswith('hooks.')]


def has_hook(hook):
    return hook in get_hooks()


def run_hook(hook, payload=None):
    mod_name = 'hooks.%s' % hook
    try:
        return getattr(sys.modules[mod_name], 'run')(payload)
    except Exception as e:
        return {'exception': e}
