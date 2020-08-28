
import logging
import os
import zipfile, io
import requests

HOST = 'api.github.com'

def get(url):
    response = requests.get(url, auth=(os.getenv("GITHUB_USER"), os.getenv("GITHUB_TOKEN")))
    response.raise_for_status()
    return response

def downloadzip_and_unzip(url, target_path):
    zipball_response = get(url)
    zipFile = zipfile.ZipFile(io.BytesIO(zipball_response.content))
    if not os.path.exists(target_path):
        os.mkdir(target_path)
    zipFile.extractall(target_path)
    list_subfolders_with_paths = [f.path for f in os.scandir(target_path) if f.is_dir()]
    return list_subfolders_with_paths[0]


def downloadzip_and_unzip_by_commit(baseurl, commit, **kwargs):
    return downloadzip_and_unzip(
        f'{baseurl}/archive/{commit}.zip',
        # commit=commit,
        **kwargs,
    )

def get_release_by_tag(owner, repo, tag):
    return get(f'https://{HOST}/repos/{owner}/{repo}/releases/tags/{tag}').json()


def get_last_release(owner, repo):
    return get(f'https://{HOST}/repos/{owner}/{repo}/releases/latest').json()

