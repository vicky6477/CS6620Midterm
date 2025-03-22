import boto3
import os
import json
import uuid
import time
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
table = dynamodb.Table(os.environ["TABLE_NAME"])

SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]
DEST_BUCKET = os.environ["DEST_BUCKET"]

def lambda_handler(event, context):
    for record in event.get("Records", []):
        event_name = record.get("eventName", "")
        key = record["s3"]["object"]["key"]

        if event_name.startswith("ObjectCreated"):
            handle_put_event(key)
        elif event_name.startswith("ObjectRemoved"):
            handle_delete_event(key)

def handle_put_event(key):
    timestamp = int(time.time())
    copy_id = str(uuid.uuid4())
    dst_key = f"{key}-{copy_id}"

    try:
        s3.copy_object(
            Bucket=DEST_BUCKET,
            CopySource={"Bucket": SOURCE_BUCKET, "Key": key},
            Key=dst_key
        )
    except Exception as e:
        print(f"Failed to copy object {key} to {dst_key}: {e}")
        return

    # Save new copy record
    table.put_item(Item={
        "object_name": key,
        "copy_id": copy_id,
        "dst_key": dst_key,
        "timestamp": timestamp,
        "disowned": "false"
    })

    # Clean up if more than 3 copies exist
    all_items = query_all_versions(key)
    if len(all_items) > 3:
        oldest = sorted(all_items, key=lambda x: x["timestamp"])[0]
        try:
            s3.delete_object(Bucket=DEST_BUCKET, Key=oldest["dst_key"])
        except Exception as e:
            print(f"Failed to delete S3 object: {e}")
        table.delete_item(Key={"object_name": oldest["object_name"], "copy_id": oldest["copy_id"]})

def handle_delete_event(key):
    now = int(time.time())
    all_items = query_all_versions(key)
    for item in all_items:
        table.update_item(
            Key={"object_name": key, "copy_id": item["copy_id"]},
            UpdateExpression="SET disowned = :d, disowned_time = :t",
            ExpressionAttributeValues={":d": "true", ":t": now}
        )

def query_all_versions(object_name):
    items = []
    start_key = None
    while True:
        kwargs = {
            "KeyConditionExpression": Key("object_name").eq(object_name)
        }
        if start_key:
            kwargs["ExclusiveStartKey"] = start_key
        resp = table.query(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            break
        start_key = resp["LastEvaluatedKey"]
    return items
