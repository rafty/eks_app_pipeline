#!/usr/bin/env python3
import os
from aws_cdk import core as cdk
from pipeline.pipeline import PipelineStack

env = cdk.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]),
)


app = cdk.App()
PipelineStack(
    scope=app,
    construct_id="PipelineStack",
    env=env
)

app.synth()
