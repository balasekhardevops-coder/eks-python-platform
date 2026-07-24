pipeline {
    agent {
        label 'built-in'
    }

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'qa', 'stage'],
            description: 'Target environment'
        )
    }

    environment {
        APP_NAME       = 'eks-python-app'
        AWS_REGION     = 'us-east-1'
        AWS_ACCOUNT_ID = '758854589827'

        ECR_REGISTRY   = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        ECR_REPOSITORY = "${ENVIRONMENT}/${APP_NAME}"
        IMAGE_TAG      = "${BUILD_NUMBER}"
        LOCAL_IMAGE    = "${APP_NAME}:${BUILD_NUMBER}"
        ECR_IMAGE      = "${ECR_REGISTRY}/${ECR_REPOSITORY}:${BUILD_NUMBER}"
    }

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()
        timeout(time: 60, unit: 'MINUTES')
    }

    stages {
        stage('Check Tools') {
            steps {
                bat '''
                    @echo off
                    git --version
                    python --version
                    docker version
                    aws --version
                    trivy --version
                '''
            }
        }

        stage('Clone Repo') {
            steps {
                checkout scm
            }
        }

      stage('Run Test Cases') {
            steps {
                bat '''
                    @echo off

                    "%PYTHON_EXE%" --version

                    if not exist ".venv\\Scripts\\python.exe" (
                        "%PYTHON_EXE%" -m venv .venv
                    )

                    ".venv\\Scripts\\python.exe" -m pip install --upgrade pip
                    ".venv\\Scripts\\python.exe" -m pip install -r requirements.txt
                    ".venv\\Scripts\\python.exe" -m pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                bat '''
                    @echo off
                    docker build ^
                      -t "%LOCAL_IMAGE%" ^
                      .
                '''
            }
        }

        stage('Scan Docker Image') {
            steps {
                bat '''
                    @echo off
                    trivy image ^
                      --severity HIGH,CRITICAL ^
                      --exit-code 1 ^
                      "%LOCAL_IMAGE%"
                '''
            }
        }

        stage('Verify AWS Identity') {
            steps {
                bat '''
                    @echo off
                    aws sts get-caller-identity
                '''
            }
        }

        stage('Verify ECR Repository') {
            steps {
                bat '''
                    @echo off
                    aws ecr describe-repositories ^
                      --repository-names "%ECR_REPOSITORY%" ^
                      --region "%AWS_REGION%"
                '''
            }
        }

        stage('Login to ECR') {
            steps {
                bat '''
                    @echo off
                    aws ecr get-login-password ^
                      --region "%AWS_REGION%" ^
                    | docker login ^
                      --username AWS ^
                      --password-stdin "%ECR_REGISTRY%"
                '''
            }
        }

        stage('Tag Docker Image') {
            steps {
                bat '''
                    @echo off
                    docker tag ^
                      "%LOCAL_IMAGE%" ^
                      "%ECR_IMAGE%"

                    docker image inspect "%ECR_IMAGE%"
                '''
            }
        }

        stage('Publish Docker Image to ECR') {
            steps {
                bat '''
                    @echo off
                    docker push "%ECR_IMAGE%"
                '''
            }
        }
    }

    post {
        success {
            echo """
                Pipeline completed successfully.

                Environment : ${params.ENVIRONMENT}
                Image       : ${env.ECR_IMAGE}
            """
        }

        failure {
            echo """
                Pipeline failed.

                Job         : ${env.JOB_NAME}
                Build       : ${env.BUILD_NUMBER}
                Environment : ${params.ENVIRONMENT}
                URL         : ${env.BUILD_URL}
            """
        }

        always {
            bat '''
                @echo off
                docker logout "%ECR_REGISTRY%" 2>nul
                docker image rm "%ECR_IMAGE%" 2>nul
                docker image rm "%LOCAL_IMAGE%" 2>nul
                exit /b 0
            '''

            cleanWs()
        }
    }
}