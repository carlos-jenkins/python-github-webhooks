# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, 2015, 2016 Carlos Jenkins <carlos@jenkins.co.cr>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
from sys import stdout, hexversion


import hmac
import base64
import os
from hashlib import sha1
from json import loads, dumps
from subprocess import Popen, PIPE
from tempfile import mkstemp
from os import access, X_OK, remove, fdopen
from os.path import isfile, abspath, normpath, dirname, join, basename

import requests
from ipaddress import ip_address, ip_network
from flask import Flask, request, abort

application = Flask(__name__)

def runShell(script, tmpfile, event):
    proc = Popen(
        [script, tmpfile, event],
        stdout=PIPE, stderr=PIPE
    )
    stdout, stderr = proc.communicate()

    # Log errors if a hook failed
    if proc.returncode != 0:
        application.logger.error('{} : {} \nSTDOUT: {}\nSTDERR: {}'.format(
            script, proc.returncode, stdout, stderr
        ))

    return {
        'returncode': proc.returncode,
        'stdout': stdout.decode('utf-8'),
        'stderr': stderr.decode('utf-8'),
    }

def runFunction(scripts, tmpfile, event):
    ran = {}
    for s in scripts:
        ran[basename(s)] = runShell(s, tmpfile, event)
    # Remove temporal file
    remove(tmpfile)
    return ran

@application.route('/', methods=['GET', 'POST'])
def index():
    """
    Main WSGI application entry.
    """
    path = normpath(abspath(dirname(__file__)))

    # Only POST is implemented
    if request.method != 'POST':
        abort(501)

    # # Load config
    config = loads(os.getenv('CONFIG'))
    hooks = config.get('hooks_path', join(path, 'hooks'))


    # Gather data
    try:
        payload = loads(base64.b64decode(request.get_json()['message']['data']))
        event = request.get_json()['message']['attributes']['event']
    except Exception as e:
        application.logger.error(e, exc_info=True)
        abort(400)

    # Determining the branch is tricky, as it only appears for certain event
    # types an at different levels
    branch = None
    try:
        # Case 1: a ref_type indicates the type of ref.
        # This true for create and delete events.
        if 'ref_type' in payload:
            if payload['ref_type'] == 'branch':
                branch = payload['ref']

        # Case 2: a pull_request object is involved. This is pull_request and
        # pull_request_review_comment events.
        elif 'pull_request' in payload:
            # This is the TARGET branch for the pull-request, not the source
            # branch
            branch = payload['pull_request']['base']['ref']

        elif event in ['push']:
            # Push events provide a full Git ref in 'ref' and not a 'ref_type'.
            branch = payload['ref'].split('/', 2)[2]

        elif event in ['release']:
            # Release events provide branch name in 'target_commitish'.
            branch = payload['release']['target_commitish']

    except KeyError:
        # If the payload structure isn't what we expect, we'll live without
        # the branch name
        pass

    # All current events have a repository, but some legacy events do not,
    # so let's be safe
    name = payload['repository']['name'] if 'repository' in payload else None

    meta = {
        'name': name,
        'branch': branch,
        'event': event
    }
    application.logger.info('Event received: {}'.format(dumps(meta)))

    # Skip push-delete
    if event == 'push' and payload['deleted']:
        application.logger.info('Skipping push-delete event for {}'.format(dumps(meta)))
        return dumps({'status': 'skipped'})
    # Skip release different from published
    elif event == 'release' and payload['action'] != 'published':
        application.logger.info('Skipping release-notpublished event for {}'.format(dumps(meta)))
        return dumps({'status': 'skipped'})

    # Possible hooks
    scripts = []
    if branch and name:
        scripts.append(join(hooks, '{event}-{name}-{branch}'.format(**meta)))
    if name:
        scripts.append(join(hooks, '{event}-{name}'.format(**meta)))
    scripts.append(join(hooks, '{event}'.format(**meta)))
    scripts.append(join(hooks, 'all'))

    application.logger.debug("scripts before: {}".format(scripts))
    # Check file
    scripts = [s for s in scripts if isfile(s) and access(s, X_OK)]
    application.logger.debug("scripts after: {}".format(scripts))
    #Give permissions
    # for s in scripts: 
    #     if not :
    #         os.chmod(s, 777)

    if not scripts:
        return dumps({'status': 'nop'})

    # Save payload to temporal file
    osfd, tmpfile = mkstemp()
    with fdopen(osfd, 'w') as pf:
        pf.write(dumps(payload))

    # Run scripts
    ran = runFunction(scripts, tmpfile, event)

    info = config.get('return_scripts_info', False)
    if not info:
        return dumps({'status': 'done'})

    output = dumps(ran, sort_keys=True, indent=4)
    application.logger.info(output)
    return output


if __name__ == '__main__':
    logging.basicConfig(level = os.getenv('LOG_LEVEL', logging.INFO))
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
    handler = logging.StreamHandler(stdout)
    handler.setFormatter(formatter)
    handler.setLevel(os.getenv('LOG_LEVEL', logging.INFO))
    application.logger.addHandler(handler)
    logging.root.handlers = [handler]
    application.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
    
