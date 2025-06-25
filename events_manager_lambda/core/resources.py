import os
import boto3


def get_boto3_resource(service_name):
    config = {}
    endpoint_var = f"{service_name.upper()}_ENDPOINT_OVERRIDE"

    if endpoint_url := os.environ.get(endpoint_var):
        config["endpoint_url"] = endpoint_url
        config["region_name"] = "us-east-1"

    return boto3.client(service_name, **config)
