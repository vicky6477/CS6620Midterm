import boto3
import os
import time
from boto3.dynamodb.conditions import Key

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")

# Environment variables
table = dynamodb.Table(os.environ["TABLE_NAME"])
DEST_BUCKET = os.environ["DEST_BUCKET"]
TTL_SECONDS = int(os.environ.get("TTL_SECONDS", "10"))

def lambda_handler(event, context):
    now = int(time.time())
    threshold = now - TTL_SECONDS
    start_key = None

    print(f"Cleaner running at {now}, threshold for deletion: {threshold}")

    while True:
        query_args = {
            "IndexName": "DisownedIndex",
            "KeyConditionExpression": Key("disowned").eq("true") & Key("disowned_time").lt(threshold)
        }

        if start_key:
            query_args["ExclusiveStartKey"] = start_key

        try:
            resp = table.query(**query_args)
        except Exception as e:
            print(f"Error querying DynamoDB: {e}")
            break

        items = resp.get("Items", [])
        print(f"Found {len(items)} disowned objects to delete.")

        for item in items:
            dst_key = item.get("dst_key")
            if not dst_key:
                print(f"Skipping item with missing dst_key: {item}")
                continue

            # Delete from S3
            try:
                s3.delete_object(Bucket=DEST_BUCKET, Key=dst_key)
                print(f"Deleted S3 object: {dst_key}")
            except Exception as e:
                print(f"Failed to delete S3 object {dst_key}: {e}")
                continue

            # Delete from DynamoDB
            try:
                table.delete_item(Key={
                    "object_name": item["object_name"],
                    "copy_id": item["copy_id"]
                })
                print(f"Deleted DynamoDB item: {item['object_name']} - {item['copy_id']}")
            except Exception as e:
                print(f"Failed to delete DynamoDB item: {e}")

        if "LastEvaluatedKey" not in resp:
            break
        start_key = resp["LastEvaluatedKey"]
