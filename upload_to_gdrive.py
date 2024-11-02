from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import os

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials/keys.json'
LICENSE_FOLDER_ID = '1DTx02JnEgfjPi-4UBwBdECWHWsaNG-q0'

def authenticate():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

def upload_licene_image(file_path):
    creds = authenticate()  # Use the authenticate function
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': os.path.basename(file_path), 'parents': [LICENSE_FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype='image/jpeg')  # Adjust mimetype based on your file
    file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    
    # Set the file's sharing permissions to make it viewable by anyone with the link
    service.permissions().create(
        fileId=file.get('id'),
        body={"type": "anyone", "role": "reader"},
        fields='id'
    ).execute()

    # Get the file's web view link
    web_view_link = file.get('webViewLink')

    print(f'File {file_path} uploaded to Google Drive with link: {web_view_link}')
    return web_view_link

