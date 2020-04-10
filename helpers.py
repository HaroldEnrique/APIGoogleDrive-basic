#!/usr/bin/env python
# coding: utf-8

from values import config
import datetime

import pickle
import os.path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_name_folder():
    name_folder = datetime.date.today().__str__()
    return name_folder


def get_credentials():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', config.get("scopes", []))
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds)

    return service


def get_files(drive_service, page_size, query):
    # Call the Drive v3 API
    results = drive_service.files().list(
        q=query,
        pageSize=page_size,
        orderBy='createdTime desc',
        fields="nextPageToken, files(id, name, owners, parents, permissionIds)").execute()
    items = results.get('files', [])

    if not items:
        logging.warning("No files found")
    else:
        logging.info("Files : ")
        
        for item in items:
            print(item)
        #     print(u'{0} ({1}) - {2}'.format(item['name'], item['id']))
    
    return items


def create_folder(drive_service, parent_id, name_folder=None):

    if name_folder is None:
        name_folder = _get_name_folder()
    else:
        name_folder = "PFR_"+name_folder+_get_name_folder()

    file_metadata = {
        'name': name_folder,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    file = drive_service.files().create(body=file_metadata,
                                        fields='id').execute()

    return file.get("id", "None")


def copy_file_into_folder(drive_service, id_folder, id_file, new_name,):

    response = drive_service.files().copy(fileId=id_file,
                                          body={"parents": [id_folder], 'name': new_name}).execute()

    logging.info("copy file response > %s", response)
    return response


def give_permissions(drive_service, metadata_single_subfolder):
    folder_id_to_share = metadata_single_subfolder.get("subfolder_id")
    user_permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': metadata_single_subfolder.get("email")
    }
    response = drive_service.permissions().create(
        fileId=folder_id_to_share,
        body=user_permission,
        fields='id'
    ).execute()

    logging.info("give permissions response > %s", response)




    return response


def revoke_permissions(drive_service):
    #get the folder of the day
    qt_folder_id = config.get("base_folder_report")
    
    date_today=_get_name_folder()
    query_folder_quarantine = f"mimeType='application/vnd.google-apps.folder' and 'frihai2@hotmail.com' in owners and name='{date_today}' and '{qt_folder_id}' in parents"
    folder_day = get_files(drive_service,1,query_folder_quarantine)
    id_folder_day = folder_day[0].get("id","")
    owners_permissionids = folder_day[0].get("permissionIds",[])

    #query = "mimeType='application/vnd.google-apps.folder' and 'frihai2@hotmail.com' in owners and name contains 'PFR'"
    query = f"mimeType='application/vnd.google-apps.folder' and 'frihai2@hotmail.com' in owners and '{id_folder_day}' in parents"
    all_teachers = get_files(drive_service,20, query)

    for share_teacher in all_teachers:
        file_id = share_teacher.get("id")
        file_name = share_teacher.get("name")
        role = "reader"
        permissions = share_teacher.get("permissionIds")
        print(permissions)
        for perm_id in permissions:
            if perm_id not in owners_permissionids:
                res_update = drive_service.permissions().update(
                    fileId = file_id,
                    permissionId = perm_id,
                    body={
                        'role':role
                    },
                    fields='id'
                ).execute()

                logging.info("update permissions response for %s > %s", file_name, res_update)
            else:
                logging.debug("owner permission cant be removed : %s",perm_id)

def upload_file(drive_service):
    folder_id = '1Ymxz2u5MF0w6nUMkNq1CLCcv_NNquqOu'
    file_metadata = {
        'name': 'buhologo.jpg',
        'parents': [folder_id]
    }
    media = MediaFileUpload('buhologo.jpg',
                            mimetype='image/jpeg',
                            resumable=True)
    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print('File ID: %s' % file.get('id'))
