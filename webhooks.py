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

import semantic_version
import hmac
import yaml
import base64
import os
from hashlib import sha1
from json import loads, dumps
from subprocess import Popen, PIPE
from tempfile import mkstemp
from os import access, X_OK, remove, fdopen
from os.path import isfile, abspath, normpath, dirname, join, basename
import sys
import json
import re

import json

import requests
from ipaddress import ip_address, ip_network
from flask import Flask, request, abort

import google_utils

application = Flask(__name__)

def runShell(script, tmpfile, event, version, language):
    proc = Popen(
        [script, tmpfile, event, version, language],
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

def runFunction(scripts, tmpfile, event, version, language):
    ran = {}
    for s in scripts:
        ran[basename(s)] = runShell(s, tmpfile, event, version, language)
    # Remove temporal file
    remove(tmpfile)
    return ran

def getVersion(payload, branch, is_tag, event, commit_id):
    if is_tag and event == "release":
        return payload['release']['tag_name'].replace('v', '')
    elif is_tag and event == "push":
        return branch.replace('v', '')
    elif branch == "develop" or branch == "master":
        # Navigate through the registry and find the latest image
        organization = payload['organization']['login']
        repo_name = payload['repository']['name']
        project_id = getProjectId()
        version = None
        for repo in getTagList(project_id, organization, repo_name, commit_id):
            application.logger.info("Processing tag: " +  repo)
            try:
                extracted_version = re.match(r'v*(\d\.\d\.\d)$', repo)
                if extracted_version is not None:
                    tmpVersion = semantic_version.Version(extracted_version.groups()[0])
                    if version is None:
                        version = tmpVersion
                        application.logger.info("- Setting as highest version: " +  str(version))
                    elif tmpVersion > version:
                        version = tmpVersion
                        application.logger.info("- Setting as highest version: " +  str(version))
            except ValueError:
                application.logger.info("- Not a version!: " +  repo)
        if version is None:
            if (branch == "develop"):
                return os.getenv("START_VERSION", "1.0.0") + "-SNAPSHOT." + commit_id[0:7]
            else:
                return os.getenv("START_VERSION", "1.0.0") + "-RC." + commit_id[0:7]
        else:
            if (branch == "develop"):
                return str(version.next_minor()) + "-SNAPSHOT." + commit_id[0:7]
            else:
                return str(version.next_minor()) + "-RC." + commit_id[0:7]
    else:
        return commit_id[0:7]

    #DOC: https://firebase.google.com/docs/database/rest/auth
def getGoogleAccessToken(service_account_info):
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
    credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=scopes)
    AuthorizedSession(credentials)
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

def getTagList(project_id, organization, repo_name, commit_id):
    registry_url="https://" + os.getenv("DOCKER_REGISTRY", "eu.gcr.io") + "/v2/" + project_id + "/github.com/" + organization + "/" + repo_name +"/tags/list"
    if commit_id is not None:
        # See if the repo has a cloudbuild.yaml to get image names from there, if not, get the image name from a composition of vars
        content = requests.get(url="https://api.github.com/repos/" + organization + "/" + repo_name + "/contents/cloudbuild.yaml?ref="+commit_id, auth=(os.getenv("GITHUB_USER"), os.getenv("GITHUB_TOKEN")))
        if content.status_code == 200:
            substitutions = {"$PROJECT_ID":project_id, "$_ORG_NAME":organization, "eu.gcr.io":"eu.gcr.io/v2"}
            # Get only one image as the rest are going to have the same tags (monorepo)
            #application.logger.info(yaml.load(base64.b64decode(content.json()["content"])))
            image_dict = yaml.load(base64.b64decode(content.json()["content"]), Loader=yaml.FullLoader)
            if image_dict["images"] and image_dict["images"][0]:
            # Now replace substitution vars
                for sub in substitutions.keys():
                    image = image.replace(sub, substitutions.get(sub))
                registry_url= "https://" + image.split(":")[0] + "/tags/list"
    try:
        application.logger.info("Registry url: " + registry_url)
        access_token = google_utils.getGoogleAccessToken(json.loads(os.environ['GCP_KEY']))
        r = requests.get(url = registry_url, headers = {"Authorization": "Bearer " + access_token})
        if r.status_code == 200:
            return r.json()["tags"]
        else:
            application.logger.info("Error loading tag list")
            return []
    except Exception as e:
        application.logger.error(e, exc_info=True)
        return []
        
def getProjectId():
    try:
        r = requests.get(url = "http://metadata.google.internal/computeMetadata/v1/project/project-id", headers = {"Metadata-Flavor": "Google"})
        if r.status_code == 200:
            return r.text
        else:
            # Get env var
            return os.getenv('PROJECT_ID')
    except Exception:
        return os.getenv('PROJECT_ID')
      

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
    is_tag = False
    commit_id = None
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
            commit_id = payload["pull_request"]["head"]["sha"]

        elif event in ['push']:
            # Push events provide a full Git ref in 'ref' and not a 'ref_type'.
            branch = payload['ref'].split('/', 2)[2]
            commit_id = payload["head_commit"]["id"]
            if payload['ref'].split('/', 2)[1] == "tags":
                is_tag = True

        elif event in ['release']:
            # Release events provide branch name in 'target_commitish'.
            branch = payload['release']['target_commitish']
            if payload['release']['tag_name'] is not None:
                is_tag = True

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

    # Calculate version
    version = getVersion(payload, branch, is_tag, event, commit_id)
    if payload["repository"]["language"]:
        language=payload["repository"]["language"]
    else:
        language="unknown"
    # Run scripts
    ran = runFunction(scripts, tmpfile, event, version, language)

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
    #with open(sys.argv[1]) as json_file:
    #    data = json.load(json_file)
    #    print getVersion(data, sys.argv[2], False, sys.argv[3], data["commits"][0]["id"])
    application.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
    
