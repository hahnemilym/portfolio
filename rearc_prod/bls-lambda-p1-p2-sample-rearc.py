import os
import json
import hashlib
import requests
import boto3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from botocore.exceptions import ClientError

s3_client = os.environ.get('s3_client')
S3_BUCKET = os.environ.get('S3_BUCKET')
base_url = "https://download.bls.gov/pub/time.series/pr/"

def lambda_handler(event, context):
    def md5(fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def fetch_and_upload(file_name):
        file_url = urljoin(base_url, file_name)
        r = requests.get(file_url)
        local_file = f"/tmp/{file_name}"
        with open(local_file, 'wb') as f:
            f.write(r.content)
        current_md5 = md5(local_file)
        try:
            s3_md5 = s3_client.head_object(Bucket=S3_BUCKET, Key=file_name)['ETag'][1:-1]
            if current_md5 != s3_md5:
                s3_client.upload_file(local_file, S3_BUCKET, file_name)
        except ClientError as e:
            if e.response['Error']['Code'] in ('403', '404'):
                s3_client.upload_file(local_file, S3_BUCKET, file_name)
        os.remove(local_file)

    r = requests.get(base_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    for link in soup.find_all('a'):
        file_name = os.path.basename(urlparse(link.get('href')).path)
        if file_name:
            fetch_and_upload(file_name)

    api_url = "https://datausa.io/api/data?drilldowns=Nation&measures=Population"
    response = requests.get(api_url)
    data = response.json()
    with open("/tmp/population_data_temp.json", "w") as f:
        json.dump(data, f)
    s3_client.upload_file("/tmp/population_data_temp.json", S3_BUCKET, "population_data.json")
