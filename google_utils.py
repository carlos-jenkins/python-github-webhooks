from google.oauth2 import service_account
import google.auth.transport.requests

    #DOC: https://firebase.google.com/docs/database/rest/auth
def getGoogleAccessToken(service_account_info):
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
    credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=scopes)
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token