import requests

LANG_DETECTOR_URL= "https://language-detector-ellp3rmx2a-ew.a.run.app"

def get_language_repo(repoURL, commit_id):
    auth = {'Authorization': 'Bearer ' + get_identity_token()}
    params = {
        "repoURL": repoURL,
        "rev": commit_id,
    }
    response = requests.get(LANG_DETECTOR_URL + "/languages", headers=auth, params=params)
    response.raise_for_status()
    return response.json()["name"]

def get_identity_token():
    request_http_headers = {'Metadata-Flavor': 'Google'}
    params = {
        'audience': LANG_DETECTOR_URL,
    }
    try:
        response = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity", headers=request_http_headers, params=params)
    except Exception as e:
        print('[ERROR] get_identity_token(): Exception in requests.get: %s\n' % e)
        response = None
    if response is not None:
        if response.status_code == 200:
            if response.text is not None:
                return response.text
            else:
                print('[ERROR] get_identity_token(): Wrong received json from server')
        else:
            print('[ERROR] get_identity_token(): Response from Google Metadata with status code ' +
                  format(response.status_code))
    return None
