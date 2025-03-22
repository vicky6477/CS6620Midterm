This project implements an automatic backup system for S3 objects using AWS Lambda, S3, and DynamoDB.

**Project Structure**
1. app.py: main entry point for CDK
2. three stacks:
    1. resource_stack.py: defines S3 buckets and DynamoDB table
    2. replicator_stack.py: defines the Replicator Lambda and configures S3 triggers
    3. cleaner_stack.py: defines the Cleaner Lambda and configures a scheduled rule
3. lambda: contains Lambda code
      1. replicator_lambda.py: Handles S3 events(put/delete)
      2. cleaner_lambda.py: Cleans up disowned objects



**How it works**
The system consists of two Lambda functions:

1. Replicator: Creates copies of objects when they're added to the source bucket. Maintains max 3 copies per object.
2. Cleaner: Runs every 1 minutes to clean up copies of deleted objects after a 10s waiting period.

**Setup**

1. Make sure you have AWS CDK installed:
   
        npm install -g aws-cdk

2. Install the project dependencies:

        pip install -r requirements.txt
3. Deploy the system:

        cdk bootstrap
        cdk deploy

