import boto3
import os

from botocore.exceptions import ClientError

s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("MINIO_URL"),
    aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
    aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD")
)
bucket_name = os.getenv("S3_BUCKET_NAME")
print('lol', bucket_name)
try:
    s3_client.head_bucket(Bucket=bucket_name)
except ClientError:
    # Если бакет не существует, создаем его
    s3_client.create_bucket(Bucket=bucket_name)


def upload_file_to_s3(file) -> None:
    s3_client.upload_fileobj(file.file, bucket_name, file.filename)

