import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    aws_dynamodb as dynamodb
)
from constructs import Construct

class CleanerStack(Stack):
    def __init__(self, scope: Construct, id: str,
                destination_bucket: s3.Bucket,
                table: dynamodb.Table,
                ttl_seconds: int = 10, 
                **kwargs):
        super().__init__(scope, id, **kwargs)

        cleaner_lambda = _lambda.Function(
            self, "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="cleaner_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda/cleaner_lambda.zip"),
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "DEST_BUCKET": destination_bucket.bucket_name,
                "TABLE_NAME": table.table_name,
                "TTL_SECONDS": str(ttl_seconds)
            }
        )

        rule = events.Rule(
            self, "CleanerSchedule",
            schedule=events.Schedule.rate(cdk.Duration.minutes(1)) 
        )
        rule.add_target(targets.LambdaFunction(cleaner_lambda))

        destination_bucket.grant_delete(cleaner_lambda)
        table.grant_read_write_data(cleaner_lambda)
