import os
import uuid

import boto3
from botocore.client import Config
from google.cloud import storage


class FirebaseTransport:
    def upload(self):
        raise NotImplementedError


class FirebaseStorageTransport(FirebaseTransport):

    def __init__(self, from_filename=None):
        self.from_filename = from_filename
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'modules/config-google.json'
        self.client = storage.Client()
        self.bucket = self.client.get_bucket('suptitle-kvando.appspot.com')

    def upload(self):
        filename = self.from_filename.split('/')[-1]
        if filename == 'blob':
            filename = str(uuid.uuid4().hex[:16]) + '.wav'
        blob = self.bucket.blob('husen/' + filename)
        blob.upload_from_filename(self.from_filename)
        # if filename.split('.')[1] == 'wav':
        #     self.delete('husen/' + filename)
        return f"gs://suptitle-kvando.appspot.com/husen/{filename}"

    def delete(self, filename):
        blobs = self.bucket.list_blobs()
        for blob in blobs:
            if filename == blob.name:
                blob.delete()


class WassabiStorageTransport:
    def __init__(self, from_filename=None):
        self.endpoint_url = 'https://s3.us-west-1.wasabisys.com'
        self.from_filename = from_filename
        self.bucket = 'suptitle'
        self.s3 = boto3.resource(
                                    's3',
                                    endpoint_url=self.endpoint_url,
                                    aws_access_key_id='H65G53K0E0IPIP95QQ6L',
                                    aws_secret_access_key='GSpLRT4IFa67fGbWYIRHugC2nzmQ9l7RS1Hl7Mqq',
                                    config=Config(signature_version='s3v4')
                                )


    def upload(self):
        data = open(self.from_filename, 'rb')
        key_file = 'hosen/' + self.from_filename.split('/')[-1]

        self.s3.Bucket(self.bucket).put_object(ACL='public-read', Key=key_file, Body=data)
        return f'https://{self.bucket}.s3.us-west-1.wasabisys.com/{key_file}'


    def list_files(self):
        listObjSummary = self.s3.Bucket(self.bucket).objects.all()
        for obj in listObjSummary:
            print(f'https://{self.bucket}.s3.us-west-1.wasabisys.com/{obj.key}')


    def clear_all_bucket(self):
        listObjSummary = self.s3.Bucket(self.bucket).objects.all()
        for obj in listObjSummary:
            obj.delete()
            print(f'Deleted https://{self.bucket}.s3.us-west-1.wasabisys.com/{obj.key}')

    def clear_user_bucket(self, user):
        listObjSummary = self.s3.Bucket(self.bucket).objects.all()
        for obj in listObjSummary:
            if user in obj.key:
                obj.delete()
                print(f'Deleted from {user}: https://{self.bucket}.s3.us-west-1.wasabisys.com/{obj.key}')


if __name__ == '__main__':
    url = FirebaseStorageTransport().delete('1.mp3')