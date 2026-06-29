import boto3
from botocore.exceptions import ClientError
from app.config import settings


def _r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        region_name="auto",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
    )


def upload_file_to_s3(file_bytes: bytes, s3_key: str) -> str:
    if not settings.r2_bucket:
        return s3_key

    client = _r2_client()
    try:
        client.put_object(
            Bucket=settings.r2_bucket,
            Key=s3_key,
            Body=file_bytes,
            ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ClientError as e:
        raise RuntimeError(f"R2 upload failed: {e.response['Error']['Message']}")
    return s3_key


def download_file_from_s3(s3_key: str) -> bytes:
    if not settings.r2_bucket:
        raise RuntimeError("R2 storage not configured")

    client = _r2_client()
    try:
        response = client.get_object(Bucket=settings.r2_bucket, Key=s3_key)
        return response["Body"].read()
    except ClientError as e:
        raise RuntimeError(f"R2 download failed: {e.response['Error']['Message']}")
