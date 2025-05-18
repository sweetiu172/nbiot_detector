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
        // Helm chart details
        helmChartPath = './kubernetes/helm/app-nbiot-detector' // Path to your chart directory
        helmReleaseName = 'app-nbiot-detector'
        helmValuesFile = "${helmChartPath}/values.yaml"
        // Kubernetes namespace (optional, defaults to 'default' if not specified in kubeconfig or command)
        kubernetesNamespace = 'default'
        // Kubeconfig credentials ID (if using Kubernetes plugin for credentials)
        // kubeconfigCredentialsId = 'your-kubeconfig-credentials-id'
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
            agent {
                docker { image 'alpine/k8s:1.32.0' } 
            }
            environment {
                KUBE_DEPLOYMENT_NAME = "${env.helmReleaseName}"
            }
            steps {
                script {
                    echo "Deploying ${helmReleaseName} using Helm chart from ${helmChartPath}..."
                    echo "Image to be deployed: ${registry}:${env.BUILD_NUMBER}"

                    // try {

                    //     // Lint the Helm chart (optional, but good practice)
                    //     sh "helm lint ${helmChartPath}"

                    //     sh """
                    //         helm -n ${kubernetesNamespace} upgrade --install ${helmReleaseName} ${helmChartPath} \
                    //             -f ${helmValuesFile} \
                    //             --set image.repository=${registry} \
                    //             --set image.tag=${env.BUILD_NUMBER} \
                    //             --atomic \
                    //             --timeout 10m \
                    //             --wait \
                    //             --debug
                    //     """

                    //     echo "Helm upgrade of ${helmReleaseName} initiated successfully."
                    //     echo "Waiting for rollout to complete for deployment/${KUBE_DEPLOYMENT_NAME}..."

                    //     sh "kubectl rollout status deployment/${KUBE_DEPLOYMENT_NAME} --timeout=5m"

                    //     echo "Deployment ${KUBE_DEPLOYMENT_NAME} successfully rolled out."

                    //     echo "Running application-specific health checks (if any)..."

                    //     // Ask for manual confirmation before proceeding or offering rollback
                    //     timeout(time: 15, unit: 'MINUTES') { // Timeout for the input step
                    //         def userInput = input(
                    //             id: 'confirmDeployment',
                    //             message: "Deployment of ${helmReleaseName} (Image: ${registry}:${env.BUILD_NUMBER}) seems successful. Proceed or Rollback?",
                    //             parameters: [
                    //                 [$class: 'ChoiceParameterDefinition', choices: 'Proceed\nRollback', name: 'ACTION']
                    //             ]
                    //         )
                    //         if (userInput == 'Rollback') {
                    //             echo "Manual rollback initiated for ${helmReleaseName}."
                    //             sh "helm rollback ${helmReleaseName} 0" // 0 rolls back to the previous revision
                    //             error("Deployment manually rolled back by user.")
                    //         } else {
                    //             echo "Deployment confirmed by user."
                    //         }
                    //     }

                    // } catch (err) {
                    //     echo "Deployment failed for ${helmReleaseName}. Error: ${err.getMessage()}"
                    //     echo "Attempting automatic rollback..."
                        
                    //     sh "helm history ${helmReleaseName}" // Show history before rollback
                    //     sh "helm rollback ${helmReleaseName} 0 || echo 'Rollback to previous revision failed or no previous revision found.'"

                    //     // You might want to check the status of the release again after rollback attempt
                    //     sh "helm status ${helmReleaseName}"
                    //     error("Deployment failed and rollback attempted for ${helmReleaseName}.")
                    // }
                }
            }
            // post {
            //     // This block executes regardless of the stage's success or failure,
            //     // unless an error within the 'steps' block was not caught and terminated the pipeline.
            //     // always {
            //     //     echo "Cleaning up deployment step..."
            //     //     // Example: remove temporary kubeconfig if created
            //     //     sh 'rm -f ./kubeconfig'
            //     // }
            //     // 'failure' block in 'post' could also be used for rollback if not handled by try/catch or --atomic
            //     // failure {
            //     //     echo "Deployment failed in post actions, attempting rollback if not already done."
            //     //     sh "helm rollback ${helmReleaseName} 0"
            //     // }
            // }
        }
    }
}