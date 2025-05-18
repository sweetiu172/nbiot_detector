pipeline {
    agent any

    options{
        // Max number of build logs to keep and days to keep
        buildDiscarder(logRotator(numToKeepStr: '5', daysToKeepStr: '5'))
        // Enable timestamp at each job in the pipeline
        timestamps()
    }

    environment{
        registry = 'minhtuan172/nbiot-detector-app'
        registryCredential = 'docker'      
    }

    stages {
        stage('Test') {
            agent {
                docker {
                    image 'python:3.12' 
                }
            }
            steps {
                echo 'Testing model correctness..'
                sh '''
                    cd app
                    python3 -m venv venv
                    echo "Activating virtual environment"
                    . venv/bin/activate 
                    echo "Installing packages into virtual environment"
                    pip install --no-cache-dir --upgrade pip
                    pip install --no-cache-dir -r requirements.txt
                    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
                    echo "Running tests"
                    cd ..
                    pytest
                    echo "Deactivating virtual environment"
                    deactivate
                '''
            }
        }
        stage('Build') {
            agent {
                docker {
                    image 'docker:28-dind' 
                }
            }
            steps {
                echo "--- Build Stage: Entering steps ---"
                script {
                    // Attempt to pull the latest image for caching, but don't fail if it doesn't exist
                    try {
                        sh "docker pull ${registry}:latest || true"
                    } catch (Exception e) {
                        echo "Could not pull latest image for cache, proceeding without it. Error: ${e.getMessage()}"
                    }

                    echo 'Building image for deployment..'
                    // Add --cache-from to the docker.build command
                    dockerImage = docker.build registry + ":$BUILD_NUMBER", "--cache-from ${registry}:latest ."

                    echo 'Pushing image to dockerhub..'
                    docker.withRegistry( '', registryCredential ) {
                        dockerImage.push()
                        dockerImage.push('latest')
                    }
                }
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying models..'
                echo 'Running a script to trigger pull and start a docker container'
            }
        }
    }
}