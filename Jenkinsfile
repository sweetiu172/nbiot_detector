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
        stage('Build') {
            steps {
                echo "--- Build Stage: Entering steps ---"
                script {
                    try {
                        echo "Attempting 'docker version' directly before build logic..."
                        sh 'docker version' // Basic client-server version check
                        echo "'docker version' succeeded."
                        echo "Attempting 'docker ps' directly before build logic..."
                        sh 'docker ps'      // Check if daemon can list containers
                        echo "'docker ps' succeeded."
                    } catch (Exception e) {
                        echo "CRITICAL DIAGNOSTIC: A simple Docker command FAILED right before docker.build. Error: ${e.getMessage()}"
                        // This would strongly indicate the connection is already lost by the time 'Build' steps begin
                    }

                    echo 'Building image for deployment..'
                    // This is the line that previously failed
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