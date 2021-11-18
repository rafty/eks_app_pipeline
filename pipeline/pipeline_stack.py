from aws_cdk import core as cdk
from aws_cdk import aws_iam
from aws_cdk import aws_codecommit
from aws_cdk import aws_codebuild
# from aws_cdk import aws_codepipeline
# from aws_cdk import aws_codepipeline_actions
from aws_cdk.pipelines import CodePipeline
from aws_cdk.pipelines import CodePipelineSource
from aws_cdk.pipelines import ShellStep

github_repository = 'rafty/cdk_eks_pipeline_blueprint'
github_action = ('arn:aws:codestar-connections:ap-northeast-1:338456725408:'
                 'connection/f0adad55-8456-4682-8d27-3e8b4dfa618b')
pipeline_name = 'eks-app-1'


class PipelineStack(cdk.Stack):

    def __init__(self,
                 scope: cdk.Construct,
                 construct_id: str,
                 env: cdk.Environment,
                 **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # ----------------------------------------
        # Source
        # ----------------------------------------
        # repository_name = self.node.try_get_context('repository-name')
        # github_action = self.node.try_get_context('github-action')
        github_connection = CodePipelineSource.connection(
            repo_string=github_repository,
            branch='master',
            connection_arn=github_action
        )

        # ----------------------------------------
        # Pipeline
        # ----------------------------------------
        # pipeline_name = self.node.try_get_context('pipeline-name')

        pipeline = CodePipeline(
            scope=self,
            id='EksPipeline',
            pipeline_name=pipeline_name,
            self_mutation=True,
            synth=ShellStep(
                id='Synth',
                input=github_connection,
                commands=[
                    'npm install -g aws-cdk',
                    'python -m pip install -r requirements.txt',
                    'cdk synth'
                ],
            )
        )

        # # ----------------------------------------
        # # EKS Cluster Stage
        # # ----------------------------------------
        # eks_cluster_dev_stage = EksClusterStage(
        #     scope=self,
        #     construct_id='EksClusterDev',
        #     env=env
        # )
        # pipeline.add_stage(eks_cluster_dev_stage)

