from aws_cdk import core as cdk
from pipeline.stacks.ecr_stack import EcrStack


class DockerBuildStage(cdk.Stage):

    def __init__(self,
                 scope: cdk.Construct,
                 construct_id: str,
                 env: cdk.Environment,
                 **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        self._ecr_stack = EcrStack(
            scope=self,
            construct_id='EcrStack',
            env=env)

    @property
    def ecr_stack(self):
        return self._ecr_stack
