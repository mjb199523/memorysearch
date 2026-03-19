import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def log(msg):
    print(msg)
    with open('refresh_log.txt', 'a') as f:
        f.write(msg + '\n')

def run_refresh():
    if os.path.exists('refresh_log.txt'): os.remove('refresh_log.txt')
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    log("Forcing full re-authentication...")
    creds = None

    if not creds or not creds.valid:
        if not os.path.exists('credentials.json'):
            log("Error: credentials.json missing. Download it from Google Cloud Console.")
            return

        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        flow.redirect_uri = 'http://localhost:61234/'
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        log(f"AUTHORIZATION_URL_START: {auth_url} :AUTHORIZATION_URL_END")
        creds = flow.run_local_server(port=61234, open_browser=False)
    
    # Save the token
    if creds:
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        log("SUCCESS! TOKEN UPDATED LOCALLY.")
        log("NEW_TOKEN_START")
        log(creds.to_json())
        log("NEW_TOKEN_END")
    else:
        log("Failed to acquire credentials.")

if __name__ == '__main__':
    run_refresh()
