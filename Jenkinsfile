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
                APP_NAMESPACE = "${env.kubernetesNamespace}"
            }
            steps {
                script {
                    echo "Deploying ${helmReleaseName} to namespace ${APP_NAMESPACE} using Helm chart from ${helmChartPath}..."
                    echo "Image to be deployed: ${registry}:${env.BUILD_NUMBER}"

                    try {
                        // No need to explicitly manage KUBECONFIG when running in-cluster with a service account
                        sh "kubectl config view" // Should show in-cluster config
                        sh "kubectl auth can-i '*' '*' --all-namespaces=false -n ${APP_NAMESPACE}" // Verify permissions for the SA

                        sh "helm lint ${helmChartPath}"

                        // Add --namespace to helm and kubectl commands
                        sh """
                            helm upgrade --install ${helmReleaseName} ${helmChartPath} \
                                -n ${APP_NAMESPACE} \
                                -f ${helmValuesFile} \
                                --set image.repository=${registry} \
                                --set image.tag=${env.BUILD_NUMBER} \
                                --atomic \
                                --timeout 10m \
                                --wait \
                                --debug
                        """

                        echo "Helm upgrade of ${helmReleaseName} in namespace ${APP_NAMESPACE} initiated successfully."
                        echo "Waiting for rollout to complete for deployment/${KUBE_DEPLOYMENT_NAME} in namespace ${APP_NAMESPACE}..."

                        sh "kubectl rollout status deployment/${KUBE_DEPLOYMENT_NAME} -n ${APP_NAMESPACE} --timeout=5m"
                        echo "Deployment ${KUBE_DEPLOYMENT_NAME} successfully rolled out in namespace ${APP_NAMESPACE}."

                        echo "Running application-specific health checks (if any)..."

                        timeout(time: 15, unit: 'MINUTES') {
                            def userInput = input(
                                id: 'confirmDeployment',
                                message: "Deployment of ${helmReleaseName} (Image: ${registry}:${env.BUILD_NUMBER}) in namespace ${APP_NAMESPACE} seems successful. Proceed or Rollback?",
                                parameters: [
                                    [$class: 'ChoiceParameterDefinition', choices: 'Proceed\nRollback', name: 'ACTION']
                                ]
                            )
                            if (userInput == 'Rollback') {
                                echo "Manual rollback initiated for ${helmReleaseName} in namespace ${APP_NAMESPACE}."
                                sh "helm rollback ${helmReleaseName} 0 -n ${APP_NAMESPACE}"
                                error("Deployment manually rolled back by user.")
                            } else {
                                echo "Deployment confirmed by user."
                            }
                        }

                    } catch (err) {
                        echo "Deployment failed for ${helmReleaseName} in namespace ${APP_NAMESPACE}. Error: ${err.getMessage()}"
                        echo "Attempting automatic rollback..."
                        sh "helm history ${helmReleaseName} -n ${APP_NAMESPACE}"
                        sh "helm rollback ${helmReleaseName} 0 -n ${APP_NAMESPACE} || echo 'Rollback to previous revision failed or no previous revision found.'"
                        sh "helm status ${helmReleaseName} -n ${APP_NAMESPACE}"
                        error("Deployment failed and rollback attempted for ${helmReleaseName}.")
                    }
                }
            }
            post {
                always {
                    echo "Cleaning up deployment step..."
                }
            }
        }
    }
}