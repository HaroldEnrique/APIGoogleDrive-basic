# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]

# coding: utf-8

from flask import Flask
from extensions import create_folder, get_credentials, get_files, upload_file, copy_file_into_folder, copy_file_into_folder, give_permissions, revoke_permissions

from values import config


import logging
logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level = logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World"

@app.route("/show_files")
def show_files():
    service = get_credentials()
    get_files(service,10,"")
    return "SUCCESS show_files"

@app.route("/create_folders")
def create_folder_day():
    service = get_credentials()
    
    #create a folder for the day report
    quarantine_folder = config.get("base_folder_report","")
    id_folder = create_folder(service,quarantine_folder)

    logging.info("Folder day created > %s", id_folder)

    #create the subfolders for each teacher
    teacher_list = config.get("teachers",[])
    metadata_subfolder = []
    for item in teacher_list:
        teacher_response = {}
        teacher_name = item.get("name")
        id_subfolder = create_folder(service,id_folder,teacher_name.upper())
        logging.info("Subfolder id created > %s " , id_subfolder)

        teacher_response['id_basic_file'] = item.get("id_basic_file")
        teacher_response['name'] = teacher_name
        teacher_response['email'] = item.get("email")
        teacher_response['subfolder_id'] = id_subfolder
        metadata_subfolder.append(teacher_response)

    #copy the base spreadsheet into each subfolder
    #folder_sheet_id = config.get("base_folder_spreadsheet","")
    for subfolder in metadata_subfolder:
        sheet_name = subfolder.get("name","").upper() + "_INFORME_APRENDOENCASA"
        res = copy_file_into_folder(service, subfolder.get("subfolder_id",""), subfolder.get("id_basic_file",""), sheet_name)


    #giving permissions
    for subfolder in metadata_subfolder:
        other_res = give_permissions(service,subfolder)

    return "SUCCESS create_folder_day"

@app.route("/revoke_permissions")
def app_revoke_permissios():
    service = get_credentials()
    revoke_permissions(service)
    return "SUCCESS revoke_permissions"

# @app.route("/single_share")
# def app_single_share():
#     service = get_credentials()
#     metadata = {}
#     metadata['email'] = "harolcotac@gmail.com"
#     metadata['subfolder_id'] = "1ohZJ5TQFm3anqrzVgcsiInr32cCKU3e-"

#     give_permissions(service,metadata)
#     return "SUCCESS app_single_share"

@app.route("/upload_file")
def upload_image():
    service = get_credentials()
    upload_file(service)
    return "SUCCESS upload_file"

#create folders by day
#create subfolders for each professor
#send email for each professor
#deactivate shared folder every day



if __name__ == "__main__":
    app.run(host="0.0.0.0",port="8088",debug=True)
