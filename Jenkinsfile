pipeline {
    agent any

    environment {
        SERVICE     = 'exchange'
        NAME        = 'rafaelken/exchange'
        EKS_CLUSTER = 'eks-store'
        AWS_REGION  = 'us-east-2'
    }

    stages {

        stage('SCM') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'docker build -t $NAME:latest .'
            }
        }

        stage('Build & Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker buildx create --use --name multiarch --driver docker-container || true
                        docker buildx build \
                            --platform linux/arm64,linux/amd64 \
                            -t $NAME:latest \
                            --push \
                            .
                    '''
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                withCredentials([
                    string(credentialsId: 'aws-access-key-id',     variable: 'AWS_ACCESS_KEY_ID'),
                    string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY'),
                    string(credentialsId: 'aws-session-token',     variable: 'AWS_SESSION_TOKEN')
                ]) {
                    sh '''
                        aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER
                        kubectl rollout restart deployment/$SERVICE
                    '''
                }
            }
        }
    }

    post {
        success { echo "Deploy de $SERVICE realizado com sucesso!" }
        failure { echo "Pipeline de $SERVICE falhou." }
    }
}
