pipeline {
    agent any

    environment {
        IMAGE_NAME = 'flask-taskmanager'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        // ─────────────────────────────────────────
        // STAGE 1: BUILD
        // ─────────────────────────────────────────
        stage('Build') {
            steps {
                echo "============================================"
                echo "STAGE 1: BUILD"
                echo "Building Docker image ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
                echo "============================================"
                bat "docker build -t %IMAGE_NAME%:%IMAGE_TAG% -t %IMAGE_NAME%:latest ."
                echo "Build complete: %IMAGE_NAME%:%IMAGE_TAG%"
            }
            post {
                success { echo "✅ BUILD STAGE PASSED" }
                failure { echo "❌ BUILD STAGE FAILED" }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 2: TEST
        // ─────────────────────────────────────────
        stage('Test') {
            steps {
                echo "============================================"
                echo "STAGE 2: TEST"
                echo "Running unit and integration tests..."
                echo "============================================"
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
                    junit allowEmptyResults: true,
                          testResults: 'test-results/results.xml'
                }
                success { echo "✅ TEST STAGE PASSED - All tests passed" }
                failure { error "❌ TEST STAGE FAILED - Pipeline stopped" }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 3: CODE QUALITY
        // ─────────────────────────────────────────
        stage('Code Quality') {
            steps {
                echo "============================================"
                echo "STAGE 3: CODE QUALITY"
                echo "Running SonarQube analysis..."
                echo "============================================"
                withSonarQubeEnv('SonarQube') {
                    bat """
                        sonar-scanner ^
                          -Dsonar.projectKey=flask-taskmanager ^
                          -Dsonar.sources=app ^
                          -Dsonar.tests=tests ^
                          -Dsonar.python.coverage.reportPaths=coverage.xml ^
                          -Dsonar.projectVersion=%IMAGE_TAG% ^
                          -Dsonar.qualitygate.wait=false
                    """
                }
            }
            post {
                success { echo "✅ CODE QUALITY STAGE PASSED" }
                failure { echo "❌ CODE QUALITY STAGE FAILED" }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 4: SECURITY
        // ─────────────────────────────────────────
        // ─────────────────────────────────────────
        // STAGE 4: SECURITY
        // ─────────────────────────────────────────
        stage('Security') {
            steps {
                echo "============================================"
                echo "STAGE 4: SECURITY"
                echo "Running security scans..."
                echo "============================================"

                echo "--- Running Bandit (Python SAST scan) ---"
                bat """
                    docker run --rm ^
                      -v "%WORKSPACE%:/src" ^
                      python:3.11-slim ^
                      sh -c "pip install bandit -q && bandit -r /src/app -f json -o /src/bandit-report.json --severity-level medium || true"
                """

                echo "--- Running Trivy (Docker image scan) ---"
                bat """
                    docker run --rm ^
                      -v /var/run/docker.sock:/var/run/docker.sock ^
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
                    echo "✅ Security reports archived"
                }
                success { echo "✅ SECURITY STAGE PASSED" }
                failure { echo "❌ SECURITY STAGE FAILED" }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 5: DEPLOY - STAGING
        // ─────────────────────────────────────────
        stage('Deploy - Staging') {
            steps {
                echo "============================================"
                echo "STAGE 5: DEPLOY - STAGING"
                echo "Deploying application to staging..."
                echo "============================================"
                bat "docker-compose -f docker-compose.yml down --remove-orphans || true"
                bat "docker-compose -f docker-compose.yml up -d"
                echo "Waiting for application to start..."
                bat "ping -n 15 127.0.0.1 > nul"
                bat "curl -f http://localhost:5000/health"
                echo "Staging deployment successful"
            }
            post {
                success { echo "✅ STAGING DEPLOY PASSED" }
                failure { echo "❌ STAGING DEPLOY FAILED" }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 6: RELEASE - PRODUCTION
        // ─────────────────────────────────────────
        stage('Release - Production') {
    steps {
        echo "============================================"
        echo "STAGE 6: RELEASE - PRODUCTION"
        echo "Promoting application to production..."
        echo "============================================"
        bat """
            docker-compose -f docker-compose.prod.yml down --remove-orphans
            exit /b 0
        """
        bat "ping -n 5 127.0.0.1 > nul"
        bat "docker-compose -f docker-compose.prod.yml up -d"
        echo "Waiting for production to start..."
        bat "ping -n 20 127.0.0.1 > nul"
        bat "curl -f http://localhost:5002/health"
        echo "Production release v%IMAGE_TAG% successful"
    }
    post {
        success { echo "✅ PRODUCTION RELEASE PASSED" }
        failure { echo "❌ PRODUCTION RELEASE FAILED" }
    }
}

        // ─────────────────────────────────────────
        // STAGE 7: MONITORING
        // ─────────────────────────────────────────
        stage('Monitoring') {
    steps {
        echo "============================================"
        echo "STAGE 7: MONITORING"
        echo "Starting Prometheus and Grafana..."
        echo "============================================"
        bat """
            docker-compose -f monitoring/docker-compose.monitoring.yml down --remove-orphans
            exit /b 0
        """
        bat "ping -n 5 127.0.0.1 > nul"
        bat "docker-compose -f monitoring/docker-compose.monitoring.yml up -d"
        echo "Waiting for monitoring stack to start..."
        bat "ping -n 20 127.0.0.1 > nul"
        bat "curl -f http://localhost:9090/-/healthy"
        echo "============================================"
        echo "Monitoring active!"
        echo "Prometheus: http://localhost:9090"
        echo "Grafana:    http://localhost:3001"
        echo "============================================"
    }
    post {
        success { echo "✅ MONITORING STAGE PASSED" }
        failure { echo "❌ MONITORING STAGE FAILED" }
    }
}

    // ─────────────────────────────────────────
    // PIPELINE RESULT
    // ─────────────────────────────────────────
    post {
        success {
            echo "============================================"
            echo "✅ PIPELINE COMPLETE"
            echo "All 7 stages passed successfully!"
            echo "Image: flask-taskmanager:${env.BUILD_NUMBER}"
            echo "============================================"
        }
        failure {
            echo "============================================"
            echo "❌ PIPELINE FAILED"
            echo "Check the stage logs above for details"
            echo "============================================"
        }
        always {
            echo "Pipeline finished - Build #${env.BUILD_NUMBER}"
        }
    }
}