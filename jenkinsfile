pipeline {
    agent any

    environment {
        IMAGE_NAME = 'flask-taskmanager'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Build') {
            steps {
                echo "Building Docker image..."
                bat "docker build -t %IMAGE_NAME%:%IMAGE_TAG% -t %IMAGE_NAME%:latest ."
                echo "Build complete: %IMAGE_NAME%:%IMAGE_TAG%"
            }
            post {
                success { echo "BUILD PASSED" }
                failure { echo "BUILD FAILED" }
            }
        }

        stage('Test') {
            steps {
                echo "Running tests..."
                bat "if not exist test-results mkdir test-results"
                bat """
                    docker run --rm ^
                      -v %CD%/test-results:/app/test-results ^
                      -e FLASK_ENV=testing ^
                      %IMAGE_NAME%:%IMAGE_TAG% ^
                      python -m pytest tests/ ^
                        --junitxml=test-results/results.xml ^
                        --cov=app ^
                        --cov-report=xml:coverage.xml ^
                        --cov-report=term-missing ^
                        -v
                """
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'test-results/results.xml'
                }
                success { echo "ALL TESTS PASSED" }
                failure { error "TESTS FAILED - stopping pipeline" }
            }
        }

        stage('Code Quality') {
            steps {
                echo "Running SonarQube analysis..."
                withSonarQubeEnv('SonarQube') {
                    bat """
                        sonar-scanner ^
                          -Dsonar.projectKey=flask-taskmanager ^
                          -Dsonar.sources=app ^
                          -Dsonar.tests=tests ^
                          -Dsonar.python.coverage.reportPaths=coverage.xml ^
                          -Dsonar.projectVersion=%IMAGE_TAG%
                    """
                }
                timeout(time: 3, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
            post {
                success { echo "CODE QUALITY PASSED" }
                failure { echo "CODE QUALITY GATE FAILED" }
            }
        }

        stage('Security') {
            steps {
                echo "Running Bandit security scan..."
                bat """
                    docker run --rm ^
                      -v %CD%:/src ^
                      python:3.11-slim ^
                      sh -c "pip install bandit -q && bandit -r /src/app -f json -o /src/bandit-report.json --severity-level medium || true"
                """
                echo "Running Trivy image scan..."
                bat """
                    docker run --rm ^
                      -v //var/run/docker.sock:/var/run/docker.sock ^
                      aquasec/trivy:latest image ^
                      --exit-code 0 ^
                      --severity HIGH,CRITICAL ^
                      --format table ^
                      %IMAGE_NAME%:%IMAGE_TAG%
                """
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.json',
                                     allowEmptyArchive: true
                    echo "Security reports archived"
                }
            }
        }

        stage('Deploy - Staging') {
            steps {
                echo "Deploying to staging..."
                bat "docker-compose -f docker-compose.yml down || true"
                bat "docker-compose -f docker-compose.yml up -d"
                echo "Waiting for app to start..."
                bat "ping -n 15 127.0.0.1 > nul"
                bat "curl -f http://localhost:5000/health"
                echo "Staging deployment successful"
            }
            post {
                success { echo "STAGING DEPLOY PASSED" }
                failure { echo "STAGING DEPLOY FAILED" }
            }
        }

        stage('Release - Production') {
            steps {
                echo "Releasing to production..."
                bat "docker-compose -f docker-compose.prod.yml down || true"
                bat "docker-compose -f docker-compose.prod.yml up -d"
                bat "ping -n 10 127.0.0.1 > nul"
                bat "curl -f http://localhost:5001/health"
                echo "Production release v%IMAGE_TAG% successful"
            }
            post {
                success { echo "PRODUCTION RELEASE PASSED" }
                failure { echo "PRODUCTION RELEASE FAILED" }
            }
        }

        stage('Monitoring') {
            steps {
                echo "Starting monitoring stack..."
                bat "docker-compose -f monitoring/docker-compose.monitoring.yml up -d"
                bat "ping -n 15 127.0.0.1 > nul"
                bat "curl -f http://localhost:9090/-/healthy"
                echo "Monitoring active!"
                echo "Grafana:    http://localhost:3001"
                echo "Prometheus: http://localhost:9090"
            }
            post {
                success { echo "MONITORING ACTIVE" }
            }
        }
    }

    post {
        success {
            echo "PIPELINE COMPLETE - All 7 stages passed!"
        }
        failure {
            echo "PIPELINE FAILED - Check the logs above"
        }
        always {
            echo "Pipeline finished."
        }
    }
}