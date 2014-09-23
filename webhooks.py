# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Carlos Jenkins <carlos@jenkins.co.cr>
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
from sys import stderr
logging.basicConfig(stream=stderr)

import hmac
from hashlib import sha1
from json import loads, dumps
from shlex import split as shsplit
from subprocess import Popen, PIPE
from os import access, X_OK
from os.path import isfile, abspath, normpath, dirname, join

import requests
from ipaddress import ip_address, ip_network
from flask import Flask, request, abort


application = Flask(__name__)


@application.route('/', methods=['GET', 'POST'])
def index():
    """
    """
    hooks = join(normpath(abspath(dirname(__file__))), 'hooks')

    whitelist = requests.get('https://api.github.com/meta').json()['hooks']

    # Only POST is implemented
    if request.method != 'POST':
        abort(501)

    # Load config
    with open('config.json', 'r') as cfg:
        config = loads(cfg.read())

    # Allow Github IPs only
    if config.get('github_ips_only', True):
        src_ip = ip_address(request.remote_addr)
        for valid_ip in whitelist:
            if src_ip in ip_network(valid_ip):
                break
        else:
            abort(403)

    # Enforce secret
    secret = config.get('enforce_secret', '')
    if secret:
        # Only SHA1 is supported
        sha_name, signature = request.headers.get('X-Hub-Signature').split('=')
        if sha_name != 'sha1':
            abort(501)

        # HMAC requires its key to be bytes, but data is strings.
        mac = hmac.new(secret, msg=data, digestmod=sha1)
        if not hmac.compare_digest(mac.hexdigest(), signature):
            abort(403)

    # Implement ping
    event = request.headers.get('X-GitHub-Event', None)
    if event == 'ping':
        return dumps({'msg': 'pong'})

    # Gather data
    try:
        payload = loads(request.data)
        meta = {
            'name': payload['repository']['name'],
            'branch': payload['ref'].split('/')[2],
            'event': event
        }
    except:
        abort(400)

    # Possible hooks
    scripts = [
        join(hooks, '{event}-{name}-{branch}'.format(**meta)),
        join(hooks, '{event}-{name}'.format(**meta)),
        join(hooks, '{event}'.format(**meta)),
        join(hooks, 'all')
    ]

    # Run scripts
    ran = {}
    for s in scripts:
        if isfile(s) and access(s, X_OK):
            cmd = Popen(
                shsplit("{} '{}'".format(s, dumps(payload))),
                shell=True,
                stdout=PIPE, stderr=PIPE
            )
            stdout, stderr = cmd.communicate()
            ran[basename(s)] = {
                'returncode': returncode,
                'stdout': stdout,
                'stderr': stderr,
            }

    return ran


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0')
