from aws_cdk import core as cdk
from aws_cdk import aws_ecr


class EcrStack(cdk.Stack):

    def __init__(self,
                 scope: cdk.Construct,
                 construct_id: str,
                 env: cdk.Environment,
                 **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # ----------------------------------------
        # Get a value from a context variable (cdk.json)
        # ----------------------------------------
        # github_repository = self.node.try_get_context("github_repository")
        # github_action = self.node.try_get_context("github_action")
        container_image_name = self.node.try_get_context("container_image_name")


        # remove_old_images = aws_ecr.LifecycleRule(
        #     description='Expire old images, keep 10 latest',
        #     rule_priority=1,
        #     max_image_count=10,
        #     tag_status=aws_ecr.TagStatus.ANY
        # )
        # Determine what happens to the repository
        # when the resource/stack is deleted.
        # Default: RemovalPolicy.Retain

        ecr_repository = aws_ecr.Repository(
            scope=self,
            # id='eks_app1',
            # repository_name='eks_app1',
            id=f'{container_image_name}-repository',
            repository_name=container_image_name,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            image_scan_on_push=True
            # lifecycle_rules=[remove_old_images]
        )
        # image_scan_on_push:
        # Enable the scan on push when creating the repository.
        # Default: false

