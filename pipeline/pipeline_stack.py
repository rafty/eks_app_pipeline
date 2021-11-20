from aws_cdk import core as cdk
from aws_cdk import aws_iam
from aws_cdk import aws_codebuild
from aws_cdk import aws_ssm
from aws_cdk.pipelines import CodePipeline
from aws_cdk.pipelines import CodePipelineSource
from aws_cdk.pipelines import StackSteps
from aws_cdk.pipelines import CodeBuildStep
from aws_cdk.pipelines import ShellStep

from pipeline.stages.docker_build import DockerBuildStage


# github_repository = 'rafty/eks_app_pipeline'
# github_action = ('arn:aws:codestar-connections:ap-northeast-1:338456725408:'
#                  'connection/81ccd08e-fe91-4a79-a459-398ae1b84aff')
# container_image_name = 'eks-demo-app'


class PipelineStack(cdk.Stack):

    def __init__(self,
                 scope: cdk.Construct,
                 construct_id: str,
                 env: cdk.Environment,
                 **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # ----------------------------------------
        # Get a value from a context variable (cdk.json)
        # ----------------------------------------
        github_repository = self.node.try_get_context("github_repository")
        github_action = self.node.try_get_context("github_action")
        container_image_name = self.node.try_get_context("container_image_name")

        # ----------------------------------------
        # Source
        # ----------------------------------------
        # repository_name = self.node.try_get_context('repository-name')
        # github_action = self.node.try_get_context('github-action')
        github_source = CodePipelineSource.connection(
            repo_string=github_repository,
            branch='master',
            connection_arn=github_action
        )

        # ----------------------------------------
        # Pipeline
        # ----------------------------------------

        pipeline = CodePipeline(
            scope=self,
            id='EksPipeline',
            pipeline_name=container_image_name,
            self_mutation=True,
            # cross_account_keys=True,
            synth=ShellStep(
                id='Synth',
                input=github_source,
                commands=[
                    'npm install -g aws-cdk',
                    'python -m pip install -r requirements.txt',
                    'cdk synth'
                ],
            )
        )

        # ----------------------------------------
        # Stage - Docker Container Build
        # ----------------------------------------

        docker_build_stage = DockerBuildStage(
            scope=self,
            construct_id='DockerBuildStage',
            env=env
        )

        region = env.region
        account = env.account

        # # ----------------------------------------
        # codebuild_ecr_role = aws_iam.Role(
        #     scope=self,
        #     id='codebuild-ecr-role',
        #     role_name='codebuild-ecr-role',
        #     assumed_by=aws_iam.CompositePrincipal(
        #         # aws_iam.ServicePrincipal('ecr.amazonaws.com'),
        #         aws_iam.ServicePrincipal('codebuild.amazonaws.com')
        #     )
        # )
        # codebuild_run_policy = aws_iam.Policy(
        #     scope=self,
        #     id='codebuild_run',
        #     policy_name='codebuild_run'
        # )
        # codebuild_run_policy.add_statements(
        #     aws_iam.PolicyStatement(
        #         actions=[
        #             'codebuild:*',
        #             'ecr:*'
        #         ],
        #         effect=aws_iam.Effect.ALLOW,
        #         resources=['*']
        #     )
        # )
        # codebuild_run_policy.add_statements(
        #     aws_iam.PolicyStatement(
        #         actions=['logs:GetLogEvents',],
        #         effect=aws_iam.Effect.ALLOW,
        #         resources=[f'arn:aws:logs:{region}:{account}:log-group:/aws/codebuild/*:*']
        #     )
        # )
        # codebuild_ecr_role.attach_inline_policy(codebuild_run_policy)
        # # ----------------------------------------

        codebuild_ecr_policy = aws_iam.PolicyStatement(
            actions=[
                'codebuild:*',
                'ecr:*'
            ],
            effect=aws_iam.Effect.ALLOW,
            resources=['*']
        )
        ssm_policy = aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['ssm:GetParameter', 'ssm:GetParameters'],
            resources=[f'arn:aws:ssm:{region}:{account}:parameter/*']
        )
        logs_policy = aws_iam.PolicyStatement(
            actions=['logs:GetLogEvents'],
            effect=aws_iam.Effect.ALLOW,
            resources=[f'arn:aws:logs:{region}:{account}:log-group:/aws/codebuild/*:*']
        )

        docker_build_step = CodeBuildStep(
            id='DockerBuildStep',
            input=github_source,
            build_environment=aws_codebuild.BuildEnvironment(privileged=True),  # for docker
            # install_commands=[],
            commands=[
                'echo ecr login.',
                f'aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com/{container_image_name}',
                'cd app',  # Dockerfile in app directory
                'echo Docker Hub login.',
                f"DOCKERHUB_USER_ID=$(aws --region='{region}' ssm get-parameters --names '/CodeBuild/DOCKERHUB_USER_ID' | jq --raw-output '.Parameters[0].Value')",
                f"DOCKERHUB_PASSWORD=$(aws --region='{region}' ssm get-parameters --names '/CodeBuild/DOCKERHUB_PASSWORD' --with-decryption | jq --raw-output '.Parameters[0].Value')",
                f'echo $DOCKERHUB_PASSWORD | docker login -u $DOCKERHUB_USER_ID --password-stdin',
                # # 'TAG="$(date +%Y-%m-%d.%H.%M.%S).$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | head -c 8)"',
                # # It may be better to use Tag instead of "latest".
                # f'docker build --tag {container_image_name} .',
                # # f'docker tag {container_image_name}:latest {account}.dkr.ecr.{region}.amazonaws.com/{container_image_name}:latest',
                # f'docker tag {container_image_name}:latest {account}.dkr.ecr.{region}.amazonaws.com/{container_image_name}:latest',
                # f'docker push {account}.dkr.ecr.{region}.amazonaws.com/{container_image_name}:latest',
                # 'IMAGE_TAG="$(date +%Y-%m-%d.%H.%M.%S).$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | head -c 8)"',
                'COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)',
                'IMAGE_TAG=${COMMIT_HASH:=latest}',
                f'docker build --tag {container_image_name}:latest .',
                f'docker tag {container_image_name}:latest {container_image_name}:$IMAGE_TAG',
                f'docker push {container_image_name}:latest',
                f'docker push {container_image_name}:$IMAGE_TAG',
            ],
            # role=codebuild_ecr_role  # Default: - A role is automatically created
            role_policy_statements=[
                codebuild_ecr_policy,
                logs_policy,
                ssm_policy
            ]
        )
        # role - Custom execution role to be used for the CodeBuild project.
        #        Default: - A role is automatically created
        #
        # role_policy_statements – Policy statements to add to role used during the synth.
        #                          Can be used to add acces to a CodeArtifact repository etc.
        #                          Default: - No policy statements added to CodeBuild Project Role

        stack_step = StackSteps(
            stack=docker_build_stage.ecr_stack,
            post=[docker_build_step]
        )

        pipeline.add_stage(
            stage=docker_build_stage,
            stack_steps=[stack_step],
        )

