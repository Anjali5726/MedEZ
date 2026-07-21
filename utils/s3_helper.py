import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

load_dotenv()

def is_s3_configured():
    """Check if all required AWS environment variables are set"""
    return all([
        os.getenv('AWS_ACCESS_KEY_ID'),
        os.getenv('AWS_SECRET_ACCESS_KEY'),
        os.getenv('AWS_S3_BUCKET')
    ])

def get_s3_client():
    """Initialise and return the S3 client"""
    return boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )

def upload_file_to_s3(local_file_path, s3_key):
    """
    Uploads a local file to S3.
    Returns: (success_bool, result_string)
    result_string will be the S3 key if successful, or error message.
    """
    if not is_s3_configured():
        return False, "S3 is not configured in .env"
        
    bucket_name = os.getenv('AWS_S3_BUCKET')
    s3_client = get_s3_client()
    
    try:
        s3_client.upload_file(
            Filename=local_file_path,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={'ContentType': 'application/pdf'} # Make sure browser renders it as PDF
        )
        print(f"S3: Successfully uploaded {local_file_path} to key {s3_key}")
        return True, s3_key
    except FileNotFoundError:
        return False, "The local file was not found."
    except NoCredentialsError:
        return False, "AWS credentials not found."
    except Exception as e:
        print(f"S3: Upload error: {e}")
        return False, str(e)

def get_s3_presigned_url(s3_key, expires_in=3600):
    """
    Generate a secure pre-signed URL to view a private S3 object.
    Expires in 3600 seconds (1 hour) by default.
    """
    if not is_s3_configured():
        return None
        
    bucket_name = os.getenv('AWS_S3_BUCKET')
    s3_client = get_s3_client()
    
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        print(f"S3: Error generating pre-signed URL: {e}")
        return None

def delete_file_from_s3(s3_key):
    """Delete a file from S3 bucket"""
    if not is_s3_configured():
        return False
        
    bucket_name = os.getenv('AWS_S3_BUCKET')
    s3_client = get_s3_client()
    
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"S3: Deleted key {s3_key} from bucket {bucket_name}")
        return True
    except Exception as e:
        print(f"S3: Delete error: {e}")
        return False
