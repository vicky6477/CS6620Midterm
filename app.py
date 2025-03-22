#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import aws_s3_notifications as s3n, aws_s3 as s3
from stack.resource_stack import ResourceStack
from stack.replicator_stack import ReplicatorStack
from stack.cleaner_stack import CleanerStack

app = cdk.App()

# Shared resources
resource_stack = ResourceStack(app, "ResourceStack")

# Replicator stack using only resource names 
replicator_stack = ReplicatorStack(app, "ReplicatorStack",
    src_bucket_name=resource_stack.src_bucket_name,
    dst_bucket_name=resource_stack.dst_bucket_name,
    table_name=resource_stack.table_name
)


# Cleaner stack remains unchanged 

cleaner_stack = CleanerStack(app, "CleanerStack",
    destination_bucket=resource_stack.dst_bucket,
    table=resource_stack.table,
    ttl_seconds=10
)

app.synth()
