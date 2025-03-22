import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_s3_notifications as s3n
)
from constructs import Construct

class ReplicatorStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 src_bucket_name: str,
                 dst_bucket_name: str,
                 table_name: str,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # Import resources
        src_bucket = s3.Bucket.from_bucket_name(self, "ImportedSrc", src_bucket_name)
        dst_bucket = s3.Bucket.from_bucket_name(self, "ImportedDst", dst_bucket_name)
        table = dynamodb.Table.from_table_name(self, "ImportedTable", table_name)

        # Lambda function
        replicator_lambda = _lambda.Function(
            self, "ReplicatorLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="replicator_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda/replicator_lambda.zip"),
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "SOURCE_BUCKET": src_bucket_name,
                "DEST_BUCKET": dst_bucket_name,
                "TABLE_NAME": table_name
            },
            timeout=cdk.Duration.seconds(30)
        )

        # Permissions
        src_bucket.grant_read(replicator_lambda)
        dst_bucket.grant_read_write(replicator_lambda)
        dst_bucket.grant_delete(replicator_lambda)
        table.grant_read_write_data(replicator_lambda)

        # 
        src_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED_PUT,
            s3n.LambdaDestination(replicator_lambda)
        )

        src_bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED_DELETE,
            s3n.LambdaDestination(replicator_lambda)
        )
