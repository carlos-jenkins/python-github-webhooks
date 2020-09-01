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
from tempfile import mkstemp, mkdtemp
from os import access, X_OK, remove, fdopen
from os.path import isfile, abspath, normpath, dirname, join, basename
import sys
import json
import re
import zipfile, io
import shutil

import requests
from ipaddress import ip_address, ip_network
from flask import Flask, request, abort

import google_utils
from github_build_service.github import downloadzip_and_unzip, downloadzip_and_unzip_by_commit, get_last_release, get_release_by_tag
from github_build_service.settings import Config

import yaml
# import shutil

application = Flask(__name__)

def runShell(script, *args):
    proc = Popen([script, *args], stdout=PIPE, stderr=PIPE)
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


def get_pipelines_release(version):    
    if version is Config.PIPELINES_DEFAULT_VERSION:
        return get_last_release(Config.GITHUB_OWNER, Config.PIPELINES_REPO)
    return get_release_by_tag(Config.GITHUB_OWNER, Config.PIPELINES_REPO, version)

def get_lmesci(repo_path):
    filepath = os.path.join(repo_path, Config.LMESCI_FILENAME)
    if os.path.exists(filepath):
        with open(filepath, 'r') as stream:
            return yaml.safe_load(stream)
    return {'build':{}}

def get_pipelines_version(lmes_version=None):
    if lmes_version is None:
        return Config.PIPELINES_VERSION
    return lmes_version

def get_pipeline_by_lmestype(pipelines_path, lmestype=None):
    if lmestype is None:
        return lmestype
    return os.path.join(pipelines_path, 'gwalker', f'cloudbuild_{lmestype}.yaml')

# def asdsd:

# prepare
#     download repo
#     download pipelines 
#     run hooks
def runFunction(scripts, payload, event, version, language):
    repo_container_path = mkdtemp()

    # TODO: replace it by a strategy pattern
    repo_path = downloadzip_and_unzip_by_commit(
        payload['repository']['html_url'],
        payload['head_commit']['id'],
        target_path=repo_container_path,
    ) if event == 'push' else downloadzip_and_unzip(
        payload['release']['zipball_url'],
        repo_container_path,
    )

    lmesci = get_lmesci(repo_path)
    pipelines_version = get_pipelines_version(lmesci['build'].get('pipeline_version'))
    pipeline_release = get_pipelines_release(pipelines_version)
    pipelines_container_path = mkdtemp()
    pipelines_path = downloadzip_and_unzip(
        pipeline_release['zipball_url'],
        pipelines_container_path,
    )

    pipeline = get_pipeline_by_lmestype(
        pipelines_path,
        lmesci['build'].get('type'),
    )

    # Save payload to temporal file
    osfd, tmpfile = mkstemp()
    with fdopen(osfd, 'w') as pf:
        pf.write(dumps(payload))

    args = filter(None, [tmpfile, event, version, language, repo_path, os.path.join(pipelines_path, 'gwalker'), pipeline])
    ran = {}
    for s in scripts:
        ran[basename(s)] = runShell(s, *args)

    # Remove temporal files
    remove(tmpfile)
    shutil.rmtree(repo_container_path)
    shutil.rmtree(pipelines_container_path)

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
            if "images" in image_dict:
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

    if not scripts:
        return dumps({'status': 'nop'})

    # Calculate version
    version = getVersion(payload, branch, is_tag, event, commit_id)
    if payload["repository"]["language"]:
        language=payload["repository"]["language"]
    else:
        language="unknown"
    # Run scripts
    ran = runFunction(scripts, payload, event, version, language)

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
    
