import boto3
import os
import time
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
table = dynamodb.Table(os.environ["TABLE_NAME"])

DEST_BUCKET = os.environ["DEST_BUCKET"]
TTL_SECONDS = int(os.environ.get("TTL_SECONDS", "10"))

def lambda_handler(event, context):
    now = int(time.time())
    threshold = now - TTL_SECONDS
    start_key = None

    while True:
        query_args = {
            "IndexName": "DisownedIndex",
            "KeyConditionExpression": Key("disowned").eq("true") & Key("disowned_time").lt(threshold)
        }
        if start_key:
            query_args["ExclusiveStartKey"] = start_key

        resp = table.query(**query_args)

        for item in resp.get("Items", []):
            try:
                s3.delete_object(Bucket=DEST_BUCKET, Key=item["dst_key"])
            except Exception as e:
                print(f"Failed to delete {item['dst_key']}: {e}")
                continue
            table.delete_item(Key={"object_name": item["object_name"], "copy_id": item["copy_id"]})

        if "LastEvaluatedKey" not in resp:
            break
        start_key = resp["LastEvaluatedKey"]
