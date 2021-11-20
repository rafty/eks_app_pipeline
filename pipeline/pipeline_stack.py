from aws_cdk import core as cdk
from aws_cdk import aws_iam
from aws_cdk import aws_codebuild
# from aws_cdk import aws_ssm
from aws_cdk.pipelines import CodePipeline
from aws_cdk.pipelines import CodePipelineSource
from aws_cdk.pipelines import StackSteps
from aws_cdk.pipelines import CodeBuildStep
from aws_cdk.pipelines import ShellStep
from pipeline.stages.docker_build_stage import DockerBuildStage
from steps.code_build_step import create_docker_build_step


class PipelineStack(cdk.Stack):

    def __init__(self,
                 scope: cdk.Construct,
                 construct_id: str,
                 env: cdk.Environment,
                 **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        # ----------------------------------------
        # environment region & account
        # ----------------------------------------
        region = env.region
        account = env.account

        # ----------------------------------------
        # Get a value from a context variable (cdk.json)
        # ----------------------------------------
        github_repository = self.node.try_get_context("github_repository")
        github_action = self.node.try_get_context("github_action")
        container_image_name = self.node.try_get_context("container_image_name")

        # ----------------------------------------
        # Source
        # ----------------------------------------
        github_source = CodePipelineSource.connection(
            repo_string=github_repository,
            branch='master',
            connection_arn=github_action
        )

        # ----------------------------------------
        # CodePipeline
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

        # # ----------------------------------------
        # # Stage - Policy
        # # ----------------------------------------
        # codebuild_ecr_policy = aws_iam.PolicyStatement(
        #     actions=[
        #         'codebuild:*',
        #         'ecr:*'
        #     ],
        #     effect=aws_iam.Effect.ALLOW,
        #     resources=['*']
        # )
        # ssm_policy = aws_iam.PolicyStatement(
        #     effect=aws_iam.Effect.ALLOW,
        #     actions=['ssm:GetParameter', 'ssm:GetParameters'],
        #     resources=[f'arn:aws:ssm:{region}:{account}:parameter/*']
        # )
        # logs_policy = aws_iam.PolicyStatement(
        #     actions=['logs:GetLogEvents'],
        #     effect=aws_iam.Effect.ALLOW,
        #     resources=[f'arn:aws:logs:{region}:{account}:log-group:/aws/codebuild/*:*']
        # )

        # # ----------------------------------------
        # # Stage - Build Step
        # # ----------------------------------------
        # # CodeBuildStep()
        # #   role:
        # #       Custom execution role to be used for the CodeBuild project.
        # #       Default: - A role is automatically created
        # #
        # #   role_policy_statements:
        # #       Policy statements to add to role used during the synth.
        # #       Can be used to add access to a CodeArtifact repository etc.
        # #       Default: - No policy statements added to CodeBuild Project Role
        # # ----------------------------------------
        # docker_build_step = CodeBuildStep(
        #     id='DockerBuildStep',
        #     input=github_source,
        #     build_environment=aws_codebuild.BuildEnvironment(privileged=True),  # for docker
        #     # install_commands=[],
        #     commands=[
        #         'echo --- AWS ECR login. ---',
        #         f'aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com/{container_image_name}',
        #         'echo --- Dockerfile in app directory'
        #         'cd app',
        #         'echo --- Docker Hub login. ---',
        #         f"DOCKERHUB_USER_ID=$(aws --region='{region}' ssm get-parameters --names '/CodeBuild/DOCKERHUB_USER_ID' | jq --raw-output '.Parameters[0].Value')",
        #         f"DOCKERHUB_PASSWORD=$(aws --region='{region}' ssm get-parameters --names '/CodeBuild/DOCKERHUB_PASSWORD' --with-decryption | jq --raw-output '.Parameters[0].Value')",
        #         f'echo $DOCKERHUB_PASSWORD | docker login -u $DOCKERHUB_USER_ID --password-stdin',
        #         'echo --- docker build. ---',
        #         'COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-8)',
        #         'IMAGE_TAG=$(date +%Y-%m-%dH%H.%M.%S)-${COMMIT_HASH:=latest}',
        #         f'USER_NAME={account}.dkr.ecr.{region}.amazonaws.com',
        #         f'docker build --tag {container_image_name} .',
        #         f'docker tag {container_image_name}:latest $USER_NAME/{container_image_name}:$IMAGE_TAG',
        #         f'docker push $USER_NAME/{container_image_name}:$IMAGE_TAG',
        #     ],
        #     # role=codebuild_ecr_role  # Default: - A role is automatically created
        #     role_policy_statements=[
        #         codebuild_ecr_policy,
        #         logs_policy,
        #         ssm_policy
        #     ]
        # )

        docker_build_step = create_docker_build_step(
            source=github_source,
            container_image_name=container_image_name,
            env=env)

        # ----------------------------------------
        # Stage - Add Steps to Stack
        # ----------------------------------------
        stack_step = StackSteps(
            stack=docker_build_stage.ecr_stack,
            post=[docker_build_step]
        )

        # ----------------------------------------
        # Stage - add_stage
        # ----------------------------------------
        pipeline.add_stage(
            stage=docker_build_stage,
            stack_steps=[stack_step],
        )
