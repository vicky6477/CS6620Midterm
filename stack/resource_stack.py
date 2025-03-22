import aws_cdk as cdk
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_dynamodb as dynamodb
)
from constructs import Construct

class ResourceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create source bucket
        self.src_bucket = s3.Bucket(self, "BucketSrc",
            versioned=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create destination bucket
        self.dst_bucket = s3.Bucket(self, "BucketDst",
            versioned=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create DynamoDB table
        self.table = dynamodb.Table(self, "TableT",
            partition_key=dynamodb.Attribute(
                name="object_name", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="copy_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Add GSI for disowned cleanup
        self.table.add_global_secondary_index(
            index_name="DisownedIndex",
            partition_key=dynamodb.Attribute(
                name="disowned", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="disowned_time", type=dynamodb.AttributeType.NUMBER
            )
        )

        # Expose name/arn for cross-stack use as plain strings
        self.src_bucket_name = self.src_bucket.bucket_name
        self.dst_bucket_name = self.dst_bucket.bucket_name
        self.src_bucket_arn = self.src_bucket.bucket_arn
        self.dst_bucket_arn = self.dst_bucket.bucket_arn
        self.table_name = self.table.table_name
        self.table_arn = self.table.table_arn
