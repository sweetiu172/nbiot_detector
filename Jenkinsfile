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
        registryCredential = 'dockerhub'      
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
        stage('Cooldown') {
            steps {
                echo "Pausing for 15 seconds..."
                sh "sleep 15"
            }
        }
        stage('Build') {
            steps {
                script {
                    echo 'Building image for deployment..'
                    dockerImage = docker.build registry + ":$BUILD_NUMBER" 
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