FROM jenkins/jenkins:lts-jdk17

USER root

# Install Docker CLI, Docker Compose, Python3, and utilities for DevSecOps pipeline execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io \
    docker-compose \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add jenkins user to docker group if exists
RUN groupadd -g 999 docker_host || true && \
    usermod -aG docker jenkins || true

USER jenkins
