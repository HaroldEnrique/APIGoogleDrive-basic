# -*- coding: utf-8 -*-

import os
import flask
import requests

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from extensions import create_folder, get_credentials, get_files, upload_file, copy_file_into_folder, copy_file_into_folder, give_permissions, revoke_permissions

from values import config

import logging
logging.basicConfig(
    format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


CLIENT_SECRETS_FILE = config.get("credential_file")
SCOPES = config.get("scopes")
API_SERVICE_NAME = config.get("api_service_name")
API_VERSION = config.get("api_version")

app = flask.Flask(__name__)
app.secret_key = 'secret_key'


@app.route('/')
def index():
    return print_index_table()


@app.route('/test')
def test_api_request():

    drive = validate_credentials()
    files = drive.files().list().execute()

    return flask.jsonify(**files)


@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('index'))


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return('Credentials successfully revoked.' + print_index_table())
    else:
        return('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>' +
            print_index_table())


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def print_index_table():
    return ('<table>' +
            '<tr><td><a href="/test">Show some files</a></td>' +
            '<td>Submit an API request and see a formatted JSON response. ' +
            '    Go through the authorization flow if there are no stored ' +
            '    credentials for the user.</td></tr>' +
            '<tr><td><a href="/create_folders">Create folders</a></td>' +
            '<td>Create the folder for the day, one folder for each professor' +
            '    upload a basic template for each professor, and share the folder ' +
            '    with the professor.</td></tr>' +
            '<tr><td><a href="/revoke_permissions">Revoke permissions</a></td>' +
            '<td>At the end of the day the permissions are revoked for all professors' +
            '    To give back some permissions, do it manually.</td></tr>' +
            # '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
            # '<td>Go directly to the authorization flow. If there are stored ' +
            # '    credentials, you still might not be prompted to reauthorize ' +
            # '    the application.</td></tr>' +
            # '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
            # '<td>Revoke the access token associated with the current user ' +
            # '    session. After revoking credentials, if you go to the test ' +
            # '    page, you should see an <code>invalid_grant</code> error.' +
            # '</td></tr>' +
            # '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
            # '<td>Clear the access token currently stored in the user session. ' +
            # '    After clearing the token, if you <a href="/test">test the ' +
            # '    API request</a> again, you should go back to the auth flow.' +
            # '</td></tr>'+
            '</table>')


def validate_credentials():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return drive

# ACTIONS DRIVE


@app.route("/show_files")
def show_files():

    drive = validate_credentials()
    get_files(drive, 10, "")

    return ('Show files method run succesfully ! <br><br>' +
            print_index_table())


@app.route("/create_folders")
def create_folder_day():
    drive = validate_credentials()

    # create a folder for the day report
    quarantine_folder = config.get("base_folder_report", "")
    id_folder = create_folder(drive, quarantine_folder)

    logging.info("Folder day created > %s", id_folder)

    # create the subfolders for each teacher
    teacher_list = config.get("teachers", [])
    metadata_subfolder = []
    for item in teacher_list:
        teacher_response = {}
        teacher_name = item.get("name")
        id_subfolder = create_folder(drive, id_folder, teacher_name.upper())
        logging.info("Subfolder id created > %s ", id_subfolder)

        teacher_response['id_basic_file'] = item.get("id_basic_file")
        teacher_response['name'] = teacher_name
        teacher_response['email'] = item.get("email")
        teacher_response['subfolder_id'] = id_subfolder
        metadata_subfolder.append(teacher_response)

    # copy the base spreadsheet into each subfolder
    #folder_sheet_id = config.get("base_folder_spreadsheet","")
    for subfolder in metadata_subfolder:
        sheet_name = subfolder.get(
            "name", "").upper() + "_INFORME_APRENDOENCASA"
        res = copy_file_into_folder(drive, subfolder.get(
            "subfolder_id", ""), subfolder.get("id_basic_file", ""), sheet_name)

    # giving permissions
    for subfolder in metadata_subfolder:
        other_res = give_permissions(drive, subfolder)

    return ('Folders were created successfully ! <br><br>' +
            print_index_table())


@app.route("/revoke_permissions")
def app_revoke_permissios():
    drive = validate_credentials()
    revoke_permissions(drive)
    return ('Permissions were revoked ! <br><br>' +
            print_index_table())


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run('127.0.0.1', 8080, debug=True)
