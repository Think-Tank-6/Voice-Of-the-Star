import os
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

load_dotenv()


class S3Service:
    def __init__(self, s3_bucket, aws_access_key_id, aws_secret_access_key):
        # AWS S3 클라이언트 초기화
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.S3_BUCKET = s3_bucket
    
    def upload_fileobj_to_s3(self, file_stream, object_name):
        try:
            self.s3_client.upload_fileobj(file_stream, self.S3_BUCKET, object_name)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload to S3")

    def upload_audio_file_to_s3(self, audio_file, object_name):
        try:
            self.s3_client.upload_file(audio_file, self.S3_BUCKET, object_name)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload to S3")
 

def get_s3_service(
    S3_BUCKET: str = Depends(lambda: os.getenv("S3_BUCKET")),
    aws_access_key_id: str = Depends(lambda: os.getenv("AWS_ACCESS_KEY_ID")),
    aws_secret_access_key: str = Depends(lambda: os.getenv("AWS_SECRET_ACCESS_KEY")),
) -> S3Service:
    if not aws_access_key_id or not aws_secret_access_key:
        raise NoCredentialsError
    
    
    return S3Service(S3_BUCKET, aws_access_key_id, aws_secret_access_key)