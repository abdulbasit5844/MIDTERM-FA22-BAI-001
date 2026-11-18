pipeline {
    agent any

    triggers { githubPush() }

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        STUDENT_ID = 'FA22-BAI-001'
        IMAGE      = 'midterm-fa22-bai-001:latest'
        HUB_IMAGE  = 'aen8aen/midterm-fa22-bai-001:latest'
        CONTAINER  = 'midterm-api'
        DEPS_IMAGE = 'midterm-fa22-bai-001-deps'
        SENDER     = 'ab3296726@gmail.com'
        MY_EMAIL   = 'ab3296726@gmail.com'
        INSTRUCTOR = 'qasimalik@gmail.com'
        GH_USER    = 'abdulbasit5844'
        API_URL    = 'http://localhost:8000'
    }

    stages {
        stage('Fetch latest data') {
            steps {
                checkout scm
                sh 'git log -1 --oneline && wc -l dataset/train.csv'
            }
        }

        stage('Build dependency image') {
            steps {
                sh 'docker build --target deps -t $DEPS_IMAGE .'
            }
        }

        stage('Retrain model') {
            steps {
                sh '''
                  rm -rf artifacts
                  docker run --rm -u $(id -u):$(id -g) -e GIT_COMMIT=$GIT_COMMIT \
                    -v "$WORKSPACE":/app -w /app $DEPS_IMAGE python train.py
                  cat artifacts/metrics.json
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                  docker run --rm -u $(id -u):$(id -g) -e GIT_COMMIT=$GIT_COMMIT \
                    -v "$WORKSPACE":/app -w /app $DEPS_IMAGE python -m pytest -q -p no:cacheprovider tests
                '''
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build --build-arg GIT_COMMIT=$GIT_COMMIT -t $IMAGE -t $HUB_IMAGE .'
            }
        }

        stage('Deploy on EC2') {
            steps {
                sh '''
                  docker rm -f $CONTAINER || true
                  docker run -d --name $CONTAINER --restart unless-stopped -p 8000:8000 $IMAGE
                  for i in $(seq 1 30); do
                    if curl -fsS $API_URL/metrics | grep -q "$GIT_COMMIT"; then
                      echo "Deployed:"; curl -s $API_URL/metrics; exit 0
                    fi
                    sleep 2
                  done
                  echo "Deployment health check failed"; docker logs $CONTAINER; exit 1
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh 'docker push $HUB_IMAGE'
            }
        }
    }

    post {
        always {
            script {
                def metrics = fileExists('artifacts/metrics.json') ? readFile('artifacts/metrics.json') : 'n/a'
                // Own commits -> only my inbox; any other committer (e.g. the autograder) -> instructor too
                def author = sh(script: "git log -1 --format='%an|%ae' 2>/dev/null || echo unknown", returnStdout: true).trim()
                def ownCommit = author.toLowerCase().contains(env.MY_EMAIL) || author.toLowerCase().contains(env.GH_USER)
                def recipients = ownCommit ? env.MY_EMAIL : "${env.INSTRUCTOR}, ${env.MY_EMAIL}"
                echo "Commit author: ${author} -> emailing: ${recipients}"
                emailext(
                    to: recipients,
                    from: env.SENDER,
                    replyTo: env.SENDER,
                    subject: "${env.STUDENT_ID} - MIDTERM build #${env.BUILD_NUMBER} - ${currentBuild.currentResult}",
                    body: """Student Reg No: ${env.STUDENT_ID}
Job: ${env.JOB_NAME} #${env.BUILD_NUMBER}
Result: ${currentBuild.currentResult}
Commit: ${env.GIT_COMMIT}
API: http://13.51.196.90:8000/metrics
Docker image: ${env.HUB_IMAGE}
Commit author: ${author}

Model metrics:
${metrics}

Console: ${env.BUILD_URL}console
"""
                )
            }
            sh 'docker image prune -f || true'
        }
    }
}
