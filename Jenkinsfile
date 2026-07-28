pipeline {
    agent {
        label 'built-in'
    }

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev'],
            description: 'Target environment'
        )
    }

    environment {
        APP_NAME = 'eks-python-app'
        APP_PORT = '9010'
        SMOKE_CONTAINER = 'eks-python-app-smoke'

        AWS_REGION = 'us-east-1'
        AWS_PROFILE = 'jhansi'

        ECR_REGISTRY =
            '758854589827.dkr.ecr.us-east-1.amazonaws.com'

        ECR_REPOSITORY =
            'dev/eks-python-app'

        PYTHON_EXE =
            'C:\\Users\\Balasekhar\\AppData\\Local\\Python\\bin\\python.exe'

        AWS_CONFIG_FILE =
            'C:\\Users\\Balasekhar\\.aws\\config'

        AWS_SHARED_CREDENTIALS_FILE =
            'C:\\Users\\Balasekhar\\.aws\\credentials'
    }

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        timestamps()

        timeout(
            time: 60,
            unit: 'MINUTES'
        )

        buildDiscarder(
            logRotator(
                numToKeepStr: '20'
            )
        )
    }

    stages {
        stage('Clone Repo') {
            steps {
                checkout scm
            }
        }

        stage('Generate Image Tag') {
            steps {
                script {
                    env.GIT_COMMIT_SHORT = bat(
                        script: '@git rev-parse --short=8 HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE_TAG =
                        "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"

                    env.LOCAL_IMAGE =
                        "${env.APP_NAME}:${env.IMAGE_TAG}"

                    env.ECR_IMAGE =
                        "${env.ECR_REGISTRY}/" +
                        "${env.ECR_REPOSITORY}:" +
                        "${env.IMAGE_TAG}"

                    currentBuild.displayName =
                        "#${env.BUILD_NUMBER} ${env.IMAGE_TAG}"

                    echo "Local image: ${env.LOCAL_IMAGE}"
                    echo "ECR image: ${env.ECR_IMAGE}"
                }
            }
        }

        stage('Check Tools') {
            steps {
                bat '''
                    @echo off

                    echo Jenkins user:
                    whoami

                    echo.
                    echo Workspace:
                    echo %WORKSPACE%

                    echo.
                    echo Checking Git:
                    git --version

                    echo.
                    echo Checking Python:
                    echo PYTHON_EXE=%PYTHON_EXE%

                    if not exist "%PYTHON_EXE%" (
                        echo Python executable not found:
                        echo %PYTHON_EXE%
                        exit /b 1
                    )

                    "%PYTHON_EXE%" --version

                    echo.
                    echo Checking Docker:
                    docker version

                    echo.
                    echo Checking AWS CLI:
                    aws --version

                    echo.
                    echo Checking Trivy:
                    trivy --version
                '''
            }
        }

        stage('Create Virtual Environment') {
            steps {
                bat '''
                    @echo off

                    if not exist ".venv\\Scripts\\python.exe" (
                        echo Creating Python virtual environment...
                        "%PYTHON_EXE%" -m venv .venv
                    ) else (
                        echo Virtual environment already exists.
                    )

                    ".venv\\Scripts\\python.exe" --version
                    ".venv\\Scripts\\python.exe" -m pip --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '''
                    @echo off

                    ".venv\\Scripts\\python.exe" ^
                      -m pip install ^
                      --disable-pip-version-check ^
                      --upgrade pip

                    ".venv\\Scripts\\python.exe" ^
                      -m pip install ^
                      --disable-pip-version-check ^
                      -r "application\\requirements.txt"
                '''
            }
        }

        stage('Run Test Cases') {
    steps {
        dir('application') {
            bat '''
                @echo off

                "..\\.venv\\Scripts\\python.exe" ^
                  -m pytest ^
                  --junitxml=pytest-results.xml
            '''
        }
    }

    post {
        always {
            junit(
                testResults: 'application/pytest-results.xml',
                allowEmptyResults: true
            )
        }
    }
}

stage('Build Docker Image') {
    steps {
        dir('application') {
            bat '''
                @echo off

                echo Building image:
                echo %LOCAL_IMAGE%

                docker build ^
                  --pull ^
                  --tag "%LOCAL_IMAGE%" ^
                  .
            '''
        }
    }
}

        stage('Smoke Test Container') {
            steps {
                bat '''
                    @echo off
                    setlocal EnableDelayedExpansion

                    docker rm -f "%SMOKE_CONTAINER%" 2>nul

                    docker run -d ^
                      --name "%SMOKE_CONTAINER%" ^
                      -e PORT=%APP_PORT% ^
                      -p 127.0.0.1:%APP_PORT%:%APP_PORT% ^
                      "%LOCAL_IMAGE%"

                    set "READY="

                    for /L %%I in (1,1,20) do (
                        curl --silent --fail ^
                          "http://127.0.0.1:%APP_PORT%/health/ready" >nul 2>&1

                        if !ERRORLEVEL! EQU 0 (
                            set "READY=1"
                            goto :healthy
                        )

                        timeout /t 2 /nobreak >nul
                    )

                    :healthy
                    if not defined READY (
                        echo Container did not become ready on port %APP_PORT%.
                        docker logs "%SMOKE_CONTAINER%"
                        docker rm -f "%SMOKE_CONTAINER%" 2>nul
                        exit /b 1
                    )

                    curl --silent --fail ^
                      "http://127.0.0.1:%APP_PORT%/"

                    docker rm -f "%SMOKE_CONTAINER%"
                '''
            }

            post {
                always {
                    bat '''
                        @echo off
                        docker rm -f "%SMOKE_CONTAINER%" 2>nul
                        exit /b 0
                    '''
                }
            }
        }

        stage('Inspect Docker Image') {
            steps {
                bat '''
                    @echo off

                    docker image inspect "%LOCAL_IMAGE%"
                '''
            }
        }

        stage('Scan Docker Image') {
    steps {
        bat '''
            @echo off

            trivy image ^
              --db-repository ghcr.io/aquasecurity/trivy-db:2 ^
              --no-progress ^
              --severity HIGH,CRITICAL ^
              --format table ^
              --output trivy-report.txt ^
              "%LOCAL_IMAGE%"

            trivy image ^
              --db-repository ghcr.io/aquasecurity/trivy-db:2 ^
              --no-progress ^
              --ignore-unfixed ^
              --severity HIGH,CRITICAL ^
              --exit-code 0 ^
              "%LOCAL_IMAGE%"
        '''
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'trivy-report.txt',
                allowEmptyArchive: true
            )
        }
    }
}

        stage('Verify AWS Identity') {
            steps {
                bat '''
                    @echo off

                    aws sts get-caller-identity ^
                      --profile "%AWS_PROFILE%"
                '''
            }
        }

        stage('Verify ECR Repository') {
            steps {
                bat '''
                    @echo off

                    aws ecr describe-repositories ^
                      --repository-names "%ECR_REPOSITORY%" ^
                      --region "%AWS_REGION%" ^
                      --profile "%AWS_PROFILE%"
                '''
            }
        }

        stage('Login to ECR') {
            steps {
                bat '''
                    @echo off

                    aws ecr get-login-password ^
                      --region "%AWS_REGION%" ^
                      --profile "%AWS_PROFILE%" ^
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

                    echo Publishing image:
                    echo %ECR_IMAGE%

                    docker push "%ECR_IMAGE%"
                '''
            }
        }

        stage('Save Image Metadata') {
            steps {
                bat '''
                    @echo off

                    (
                        echo ENVIRONMENT=%ENVIRONMENT%
                        echo IMAGE_TAG=%IMAGE_TAG%
                        echo IMAGE_URI=%ECR_IMAGE%
                        echo GIT_COMMIT=%GIT_COMMIT%
                        echo BUILD_NUMBER=%BUILD_NUMBER%
                    ) > image-metadata.properties

                    type image-metadata.properties
                '''

                archiveArtifacts(
                    artifacts: 'image-metadata.properties',
                    fingerprint: true
                )
            }
        }
    }

    post {
        success {
            echo """
                Pipeline completed successfully.

                Environment : ${params.ENVIRONMENT}
                Image       : ${env.ECR_IMAGE}
                Commit      : ${env.GIT_COMMIT_SHORT}
            """
        }

        failure {
            echo """
                Pipeline failed.

                Job         : ${env.JOB_NAME}
                Build       : #${env.BUILD_NUMBER}
                Environment : ${params.ENVIRONMENT}
                URL         : ${env.BUILD_URL}
            """
        }

        unstable {
            echo """
                Pipeline completed with unstable status.

                Job   : ${env.JOB_NAME}
                Build : #${env.BUILD_NUMBER}
                URL   : ${env.BUILD_URL}
            """
        }

        always {
            bat '''
                @echo off

                docker rm -f "%SMOKE_CONTAINER%" 2>nul
                docker logout "%ECR_REGISTRY%" 2>nul

                docker image rm "%ECR_IMAGE%" 2>nul
                docker image rm "%LOCAL_IMAGE%" 2>nul

                exit /b 0
            '''

            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true
            )
        }
    }
}
