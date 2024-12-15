import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError, EndpointConnectionError

from app.config import cfg


class S3Service:
    def __init__(self):
        self.s3_client: BaseClient = boto3.client(
            "s3",
            endpoint_url=cfg.minio_url,
            aws_access_key_id=cfg.minio_root_user,
            aws_secret_access_key=cfg.minio_root_password
        )
        self.bucket_name = cfg.s3_bucket_name
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            # Если бакет не существует, создаем его
            self.s3_client.create_bucket(Bucket=self.bucket_name)

    @staticmethod
    def create_key(folder: str, key: str) -> str:
        return f"{folder}/{key}"

    def upload_file(self, file, key: str) -> str:
        self.s3_client.upload_fileobj(file.file, self.bucket_name, key)

        return self.get_link(key)

    def check_object_exists(self, key):
        try:
            # Попробуем получить метаданные объекта
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False  # Объект не найден

    def get_link(self, key):
        if not self.check_object_exists(key):
            raise FileNotFoundError("Object does not exist.")
        return self.s3_client.generate_presigned_url('get_object',
                                                      Params={'Bucket': self.bucket_name, 'Key': key},
                                                      ExpiresIn=3600)



s3_service = S3Service()


async def get_s3():
    yield s3_service
