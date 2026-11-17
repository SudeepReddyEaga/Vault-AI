# 📘 Comprehensive System Run & Verification Instructions (`INSTRUCTIONS.md`)

Welcome to the **VaultAI & GraminUdyam Enterprise Platform**. This guide provides an end-to-end operational manual detailing **all possible ways to run the system**, **sub-steps for each deployment mode**, and **step-by-step verification procedures** to validate inter-service communication across all microservices and telemetry mesh.

---

## 📑 Table 3.1.1 Enterprise Port Allocation & Service Directory

All active services and interfaces currently running on your machine:

| Port | Service Name | Protocol | Network Placement | Quick Access Link | Health / Swagger UI |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **`80`** | **Nginx Reverse Gateway** | HTTP | Public Subnet | [http://localhost:80](http://localhost:80) | [http://localhost:80/health](http://localhost:80/health) |
| **`443`** | **HTTPS TLS Gateway** | HTTPS | Public Subnet | [https://localhost:443](https://localhost:443) | Self-Signed / TLS Offload |
| **`5000`** | **budget-api-service** | HTTP | Private App Subnet | [http://localhost:5000](http://localhost:5000) | [http://localhost:5000/docs](http://localhost:5000/docs) \| [/metrics](http://localhost:5000/metrics) |
| **`5001`** | **ai-agent-copilot** | HTTP | Private App Subnet | [http://localhost:5001](http://localhost:5001) | [http://localhost:5001/docs](http://localhost:5001/docs) \| [/metrics](http://localhost:5001/metrics) |
| **`5002`** | **ml-forecast-engine** | HTTP | Private App Subnet | [http://localhost:5002](http://localhost:5002) | [http://localhost:5002/docs](http://localhost:5002/docs) \| [/metrics](http://localhost:5002/metrics) |
| **`5432`** | **PostgreSQL Database** | TCP | Private DB Subnet | `localhost:5432` | DB: `rural_platform_db` \| User: `postgres` |
| **`6379`** | **Redis Cache Cluster** | RESP | Private DB Subnet | `localhost:6379` | In-Memory Sub-millisecond Store |
| **`8080`** | **Jenkins CI/CD Master** | HTTP | Ops / CI Subnet | [http://localhost:8080](http://localhost:8080) | Automated Pipeline Controller |
| **`8200`** | **HashiCorp Vault UI** | HTTP | Security Mesh | [http://localhost:8200/ui](http://localhost:8200/ui) | Token: `root-dev-token-2026` |
| **`9090`** | **Prometheus Server** | HTTP | Monitoring Mesh | [http://localhost:9090](http://localhost:9090) | [http://localhost:9090/targets](http://localhost:9090/targets) |
| **`3000`** | **Grafana Dashboard** | HTTP | Monitoring Mesh | [http://localhost:3000](http://localhost:3000) | User: `admin` \| Pass: `admin` |

---

## 🌟 GitHub Push ➔ Jenkins Build ➔ Auto-Open Web Pages Workflow

This workflow allows you to push code to GitHub on your personal PC, click **"Build Now"** in Jenkins (or run the 1-click script), and have Jenkins start from Docker build, update images, deploy containers, and **automatically open all service web pages in your browser**.

```
  1. git push origin main  ➔  2. Jenkins: "Build Now"  ➔  3. Docker Build & Scan
                                                                   |
                                                                   v
  5. Personal PC Browser   🠔  4. Deploy Containers     🠔  Docker Hub Tag/Push
     (Auto-opens all tabs:       (docker compose up -d)
      Ports 80, 3000, 9090,
      5000, 5001, 5002, 8200)
```

### How It Works Without Any Problems on Your Personal PC:
1. **Windows Host Browser Bridge (`scripts/windows_browser_bridge.py`)**:
   - A lightweight background daemon listening on Port **`8765`** on your personal PC.
   - When Jenkins (running in Docker or as a service) finishes deploying, it calls `http://host.docker.internal:8765/open`.
   - The bridge instantly launches all active service tabs in your default Windows browser (Chrome, Edge, etc.).
2. **Your Existing Jenkins Image & Volume (`jenkins-docker` & `jenkins_home`)**:
   - The platform is linked to your existing **`jenkins-docker:latest`** image and your existing **`jenkins_home`** volume.
   - **All your previous projects, pipelines, plugins, credentials, and build histories are preserved intact!**
   - The container has Docker (`/var/run/docker.sock`) and Python pre-configured to execute the builds and trigger the browser launch on your personal PC.
3. **Graceful Docker Hub Handling**:
   - If Docker Hub credentials are configured in Jenkins (`dockerhub-credentials`), it pushes versioned tags to Docker Hub.
   - If running locally on your personal PC without Docker Hub credentials, it builds and tags images locally without failing.

### How to Trigger the Complete Flow:

#### Option A: 1-Click PowerShell Script (Fastest on Personal PC)
Run from project root in PowerShell:
```powershell
.\scripts\jenkins_build_and_open.ps1
```
*(Or in Python: `python scripts/jenkins_build_and_open.py`)*.
This automatically:
- Checks git status and pushes to GitHub.
- Ensures the background Browser Bridge is active on Port 8765.
- Executes the Docker build and DevSecOps verification.
- **Automatically opens all service web pages in your browser!**

#### Option B: Via the Jenkins Web UI
1. Open Jenkins: **[http://localhost:8080](http://localhost:8080)**.
2. Ensure the Windows Host Browser Bridge is running:
   ```powershell
   python scripts/windows_browser_bridge.py
   ```
   *(Or double-click `scripts\start_browser_bridge.bat`)*.
3. Push your changes to GitHub:
   ```bash
   git add .
   git commit -m "Update microservices"
   git push origin main
   ```
4. In Jenkins, click **"Build Now"**.
5. Watch the build console: Jenkins builds all Docker images, updates containers, and triggers your Windows browser to pop open all 8 service tabs!


---

## 🚀 Part 1: All Possible Ways to Run the System

The platform supports 5 distinct execution modes tailored for local development, containerized DevOps, Kubernetes orchestration, and cloud production:

```
                            +-----------------------------------------------+
                            |        5 WAYS TO RUN THE PLATFORM             |
                            +-----------------------------------------------+
                               |            |           |           |           |
            +------------------+     +------+           |           +-----+     +--------------------+
            v                        v                  v                 v                          v
    [METHOD 1: DEVOPS]      [METHOD 2: NATIVE]   [METHOD 3: 6-SVC]  [METHOD 4: KUBERNETES]   [METHOD 5: AWS CLOUD]
    docker compose devops   python run_ecosystem docker compose    kubectl apply -f k8s/    cd terraform
    (All 10 Containers)     (Zero Docker/Zero AWS) (Marketplace+UI) (HPA 2-10 Replicas)      (Multi-AZ VPC + ECS)
```

---

### 🔹 Method 1: Production DevOps Stack (Currently Running & Active)
Runs all 10 containers specified in `DEVOPSPRESUB.pdf` (Nginx, 3 Microservices, PostgreSQL, Redis, Vault, Jenkins, Prometheus, Grafana).

#### 1. Startup Command:
```powershell
# From project root:
docker compose -f docker-compose.devops.yml up --build -d
```
*(Or run `.\scripts\deploy_local.ps1` in PowerShell / `./scripts/deploy_local.sh` in Bash)*.

#### 2. Sub-steps after running:
1. **Verify container status**:
   ```powershell
   docker ps
   ```
   *Expected output*: 10 containers in `Up` or `Up (healthy)` state.
2. **Inspect logs of any service**:
   ```powershell
   docker logs -f pba_budget_api_service
   docker logs -f pba_ai_agent_copilot
   docker logs -f pba_ml_forecast_engine
   ```
3. **Run 1-Click Ecosystem Scorecard Audit**:
   ```powershell
   python scripts/verify_ecosystem.py
   ```
   *Expected output*: All 10 ports marked `🟢 ACTIVE`, metrics reporting `🟢 Exporting PBA Telemetry`.
4. **Shutdown command (when done)**:
   ```powershell
   docker compose -f docker-compose.devops.yml down
   ```

---

### 🔹 Method 2: Native Windows / Python Standalone (Zero Docker & Zero AWS)
Runs all microservices directly in native Python threads without needing Docker Desktop or cloud connectivity.

#### 1. Startup Command:
```powershell
# From project root:
python run_ecosystem.py
```

#### 2. Sub-steps after running:
1. The launcher initializes:
   - `auth_service` on Port 8001
   - `advisory_service` on Port 8002
   - `marketplace_service` on Port 8003
   - `recommendation_service` on Port 8004
   - `analytics_service` on Port 8005
   - `personal_budget_service` on Port 8006
   - Static Web Portal on Port 3000
2. Open your web browser to:
   - **Web UI**: [http://localhost:3000](http://localhost:3000)
3. Seed the local SQLite database if needed:
   ```powershell
   python database/seed_db.py
   ```
4. Stop the services: Press `Ctrl + C` in the console window.

---

### 🔹 Method 3: Multi-Service Rural Advisory & Marketplace Stack
Spins up the full 6-microservice rural advisory marketplace alongside Postgres and Redis:

#### 1. Startup Command:
```powershell
docker compose up --build -d
```

#### 2. Sub-steps after running:
1. Seed the PostgreSQL database from JSON fixtures:
   ```powershell
   python database/seed_db.py
   ```
2. Access the interactive React Dual-Portal at [http://localhost:3000](http://localhost:3000).
3. Test the Redis-backed Top Selling Products API:
   ```powershell
   curl http://localhost:8003/products/top-selling
   ```

---

### 🔹 Method 4: Production Kubernetes (K8s) Cluster with HPA
Deploys the microservices to Minikube, Kind, or an EKS/GKE cluster with Horizontal Pod Autoscaling (2 to 10 pods).

#### 1. Startup Command:
```powershell
# 1. Apply Namespace, ConfigMaps, and Secrets
kubectl apply -f k8s/config-and-secrets.yaml

# 2. Deploy PostgreSQL and Redis
kubectl apply -f k8s/data-services.yaml

# 3. Deploy all microservices with Horizontal Pod Autoscaler (HPA)
kubectl apply -f k8s/microservices-hpa.yaml

# 4. Deploy Ingress Controller
kubectl apply -f k8s/ingress.yaml
```
*(Or deploy the consolidated DevOps manifest: `kubectl apply -f k8s/vaultai-devops-complete.yaml`)*.

#### 2. Sub-steps after running:
1. **Check Pod status**:
   ```powershell
   kubectl get pods -n vault-ai
   ```
2. **Inspect Autoscalers (HPA)**:
   ```powershell
   kubectl get hpa -n vault-ai
   ```
   *Expected output*: `MinPods: 2, MaxPods: 10, TargetCPU: 70%`.
3. **Simulate high load for auto-scaling**:
   ```powershell
   kubectl run load-generator -n vault-ai --image=busybox --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://budget-api-service:5000/api/state; done"
   ```

---

### 🔹 Method 5: Enterprise AWS Cloud Deployment via Terraform
Provisions a production Multi-AZ VPC, ECS Fargate cluster, RDS Postgres, ElastiCache Redis, ALB, CloudWatch, and Lambda Alert Dispatcher on AWS.

#### 1. Startup Command:
```powershell
# Set your Docker Hub credentials and deploy:
.\scripts\deploy_aws.ps1 -DockerHubUser "your_dockerhub_username" -DockerHubPass "your_dockerhub_password"
```
Or manually via Terraform:
```powershell
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply -auto-approve
```

#### 2. Sub-steps after running:
1. **Retrieve Cloud Infrastructure Outputs**:
   ```powershell
   terraform output alb_dns_name
   terraform output ecs_cluster_name
   terraform output rds_endpoint
   ```
2. **Access Cloud Public Endpoint**:
   Open `http://<alb_dns_name>/api/state` or `http://<alb_dns_name>/grafana/`.
3. **Cloud Teardown (avoid AWS charges)**:
   ```powershell
   terraform destroy -auto-approve
   ```

---

## 🔍 Part 2: Step-by-Step Inter-Service Communication Verification

Here is the exact step-by-step verification process to test each container and demonstrate live data flow between microservices.

---

### 🧪 Test 1: Nginx Gateway (Port 80 / 443)
- **Link**: [http://localhost:80/health](http://localhost:80/health)
- **Direct Browser Check**: Open [http://localhost:80/api/state](http://localhost:80/api/state).
- **Communication Flow**: `User Browser` $\to$ `Nginx Gateway (Port 80)` $\to$ `pba_budget_api_service (Port 5000)`.
- **Command (PowerShell / Bash)**:
  ```powershell
  curl http://localhost:80/health
  ```
- **Expected Response**:
  ```json
  {
    "status": "ok",
    "service": "budget-api-service",
    "port": 5000,
    "dependencies": {
      "ai_agent_copilot": "http://ai-agent-copilot:5001",
      "ml_forecast_engine": "http://ml-forecast-engine:5002"
    }
  }
  ```

---

### 🧪 Test 2: Budget API Service (Port 5000)
- **Link**: [http://localhost:5000/docs](http://localhost:5000/docs) (Interactive Swagger UI)
- **Direct State Check**: [http://localhost:5000/api/state](http://localhost:5000/api/state)
- **Command**:
  ```powershell
  curl http://localhost:5000/api/state
  ```
- **Expected Response**:
  Returns current deterministic income, total expenses, category limits, savings target, and remaining balance.

---

### 🧪 Test 3: AI Agent Copilot & Plan-Act Loop (Port 5000 $\to$ Port 5001)
- **Link**: [http://localhost:5001/docs](http://localhost:5001/docs)
- **Communication Flow**: When you send a message to Port 5000 (`/api/chat`), Port 5000 invokes the ReAct loop in `pba_ai_agent_copilot` on Port 5001, which maps intent to tools (`add_expense`, `check_affordability`, `set_category_budget`) and returns deterministic actions.
- **Test Command**:
  ```powershell
  curl -X POST http://localhost:5000/api/chat `
       -H "Content-Type: application/json" `
       -d '{"message": "I spent 45 dollars on lunch in Food"}'
  ```
- **Expected Response**:
  ```json
  {
    "response": "Recorded expense of $45.00 under 'Food'. Plan-Act ledger updated deterministically.",
    "tool_trace": ["add_expense"]
  }
  ```

---

### 🧪 Test 4: Mathematical Affordability Checker ($A(X, k)$)
- **Formula Evaluated**:
  $$A(X, k) = \begin{cases} \text{APPROVED} & \text{if } X \le B \land (S_k + X) \le C_k \\ \text{REJECTED} & \text{otherwise} \end{cases}$$
- **Communication Flow**: Port 5000 $\to$ Port 5001 (`/api/agent/affordability`).
- **Test Command (Expense Exceeds Category Budget)**:
  ```powershell
  curl -X POST http://localhost:5000/api/affordability `
       -H "Content-Type: application/json" `
       -d '{"item": "High-end Gaming Laptop", "cost": 2500, "category": "Tech"}'
  ```
- **Expected Response**:
  ```json
  {
    "item": "High-end Gaming Laptop",
    "cost": 2500.0,
    "category": "Tech",
    "status": "REJECTED",
    "verdict": "Purchase of High-end Gaming Laptop ($2500.00) is REJECTED. Category 'Tech' limit exceeded..."
  }
  ```

---

### 🧪 Test 5: ML Forecast Engine & Health Score (Port 5002)
- **Link**: [http://localhost:5002/docs](http://localhost:5002/docs)
- **Communication Flow**: Executes Scikit-Learn linear regression on spending velocity, detects budget drift 7–10 days early, and computes the Financial Health Index (0–100).
- **Test Command**:
  ```powershell
  curl -X POST http://localhost:5002/api/ml/predict `
       -H "Content-Type: application/json" `
       -d '{"income": 5000, "savings_goal": 1000, "category_budgets": {"Food": 600}, "expenses": [{"amount": 200, "category": "Food"}]}'
  ```
- **Expected Response**:
  ```json
  {
    "current_total_spent": 200.0,
    "predicted_next_month_total": 216.0,
    "trend_direction": "UP",
    "health_score": { "score": 100, "rating": "EXCELLENT" },
    "r2_score_benchmark": 0.94
  }
  ```

---

### 🧪 Test 6: Prometheus Telemetry Scraper (Port 9090)
- **Link**: [http://localhost:9090](http://localhost:9090)
- **Targets Health**: [http://localhost:9090/targets](http://localhost:9090/targets)
- **Verification Steps**:
  1. Open [http://localhost:9090/targets](http://localhost:9090/targets).
  2. Verify all 4 scrape targets show **State: UP (1/1)**:
     - `budget-api-service` (port 5000)
     - `ai-agent-copilot` (port 5001)
     - `ml-forecast-engine` (port 5002)
     - `prometheus` (port 9090)
  3. Query live metric in Expression bar:
     - `pba_http_requests_total`
     - `pba_financial_health_score`
     - `pba_agent_tool_executions_total`

---

### 🧪 Test 7: Grafana Telemetry Dashboard (Port 3000)
- **Link**: [http://localhost:3000](http://localhost:3000)
- **Credentials**:
  - **Username**: `admin`
  - **Password**: `admin`
- **Pre-Loaded Dashboard**:
  1. Once logged in, navigate to **Dashboards** $\to$ **Enterprise Services** $\to$ **VaultAI & Rural Platform Overview**.
  2. Live panels will display:
     - **HTTP Traffic Volume** (requests/sec across endpoints)
     - **P95 / P99 Request Latency** (Histogram tracking)
     - **AI Agent Tool Execution Breakdown** (`add_expense`, `check_affordability`, `set_category_budget`)
     - **Financial Health Index Gauge** (0 to 100 benchmark)

---

### 🧪 Test 8: HashiCorp Vault Secrets Manager (Port 8200)
- **Link**: [http://localhost:8200/ui](http://localhost:8200/ui)
- **Authentication**:
  - Method: **Token**
  - Token: `root-dev-token-2026`
- **Verification**:
  - Confirms cryptographic secret management and secure key-value storage engine is unsealed and operational.

---

### 🧪 Test 9: Jenkins CI/CD Controller (Port 8080)
- **Link**: [http://localhost:8080](http://localhost:8080)
- **Verification**:
  - Access Jenkins master console to manage the automated multi-branch pipeline.
  - Initial admin password (if requested):
    ```powershell
    docker exec pba_jenkins cat /var/jenkins_home/secrets/initialAdminPassword
    ```

---

### 🧪 Test 10: 1-Click Automated Ecosystem Scorecard Audit
Execute the automated audit script from PowerShell:
```powershell
python scripts/verify_ecosystem.py
```
This script audits:
- Socket connectivity to all 10 canonical ports.
- Health endpoints and Prometheus `/metrics` exporters.
- Bandit SAST report findings.
- Table 11.1 Enterprise Readiness Benchmarks.

---

## 🔒 Part 3: Automated DevSecOps Pipeline & Security Gates

To run the complete 5-stage DevSecOps pipeline locally:

```powershell
python scripts/run_devsecops_pipeline.py
```

### Stages executed:
1. **Git SCM Status & Inspection**: Verifies repository cleanliness.
2. **Flake8 Code Quality Analysis**: Strict syntax and undefined variable audit.
3. **Pytest Deterministic Accuracy Suite** (`tests/test_devsecops.py`):
   - Validates $100\%$ ledger precision (Zero Hallucination).
   - Validates mathematical affordability formula.
   - Validates ML regression velocity ($R^2 \ge 0.92$).
   - Validates semantic intent recognition ($>95\%$).
4. **Bandit Static Application Security Testing (SAST)**:
   - Audits AST security using `bandit.yaml`.
   - Generates `bandit-report.json` with 0 high severity vulnerabilities.
5. **Docker Container Packaging**:
   - Builds and tags production container images ready for Docker Hub.

---

## 🛑 How to Gracefully Stop or Restart Everything

### Stop all containers:
```powershell
docker compose -f docker-compose.devops.yml down
```

### Restart all containers:
```powershell
docker compose -f docker-compose.devops.yml up -d
```

### View real-time container resource usage (CPU/RAM):
```powershell
docker stats
```
