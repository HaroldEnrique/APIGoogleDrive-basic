#!/usr/bin/env python
# coding: utf-8

config = {
    "base_folder_report":"1-VgaNrr9UNFQy51nCup_Nq561BHm0tgX", # folder INFORMES-CUARENTENA
    "base_folder_spreadsheet":"11FtkuXJ15kuxI81nMk0nxlE8UH_IzwLQ",
    "teachers": [
        {
            "id_basic_file":"1brY9hE4-9RonM5wNTwuy3iqJvsE2NriS",
            "name": "Harold_Samaria",
            "email": "harolcotac@gmail.com"
        },
        {
            "id_basic_file":"1wZieF9SuBkMNE9hjfn3Hkhfiy2b8JsEW",
            "name": "Ailen_Belen",
            "email": "iacm268@gmail.com"
        },
        {
            "id_basic_file":"1l_GDFm8NAq3XQ0fbqyJHwWsHIPpqUGhd",
            "name": "Edwin_Cota",
            "email": "edwinhaif@gmail.com"
        }
    ],
    "scopes": ['https://www.googleapis.com/auth/drive.metadata.readonly',
               'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file'],
    "credential_file": "client_credentials.json",
    "api_service_name": "drive",
    "api_version": "v3"
}
