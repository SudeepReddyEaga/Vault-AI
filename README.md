# 🌾 GraminUdyam AI & VaultAI: Unified Rural Advisory & Personal Budgeting Platform

An institutional-grade, cloud-native microservice architecture that combines:
1. **Hyper-Local Rural Business Feasibility & Government Concessional Credit Router** (State Channelizing Agencies - SCAs / CAs)
2. **Rural Equipment & Raw Materials Marketplace** (with Redis Cache for sub-millisecond retrieval)
3. **Personal Budget Assistant & Financial AI Copilot (VaultAI)** running as an independent ReAct agent microservice synchronized with user JWT credentials.

---

## 📁 Repository Directory Structure

```
d:\Downloads\agenticproject\
├── docker-compose.yml               # Master Docker Compose running all 9 containers (Postgres, Redis, 6 Services, Frontend)
├── run_ecosystem.py                 # 1-Click Python concurrent launcher for native Windows development
├── README.md                        # Master Architecture, Verification, and User Guide
├── database/                        # Amazon-Grade Relational Database Engine
│   ├── customers.json               # Customer Profiles (Aadhaar KYC, Gram Panchayat shipping, Margin Capital, SCA Scheme)
│   ├── sellers.json                 # Seller Central Profiles (GSTIN, SCA license, FBA logistics, Warehouse hubs, Ratings)
│   ├── schema.sql                   # Amazon-style PostgreSQL Relational DDL (users, customer_profiles, seller_profiles, products, orders)
│   └── seed_db.py                   # Automated JSON -> PostgreSQL/SQLite Seeder and Query Verification script
├── docs/                            # Course Specifications, IIT Bombay Spec, and Rubric PDFs
│   ├── CSE476_CA1_Project.pdf
│   ├── Personal_Budget_Assistant_Target_Architecture_IITB_Specification.pdf
│   ├── Personal_Budget_Assistant_IITB_Spec.html
│   └── pdf_content.txt
├── services/                        # The 6 Modular Family Microservices (FastAPI)
│   ├── auth_service/                # Port 8001: JWT Token Auth, RBAC, Customer & Seller Profiles (PostgreSQL)
│   ├── advisory_service/            # Port 8002: Module 1 Feasibility (5-10km reach, SWOT) & Module 2 Concessional Loan Router
│   ├── marketplace_service/         # Port 8003: Equipment Catalog, Orders, & Redis In-Memory Caching
│   ├── recommendation_service/      # Port 8004: ML Vector Cosine Recommender for Customer & Seller
│   ├── analytics_service/           # Port 8005: ML 90-Day Sales Regression & Customer DSCR Analytics
│   └── personal_budget_service/     # Port 8006: VaultAI ReAct Agent Copilot, BudgetMemory, & Scikit-Learn ML Forecaster
├── frontend/                        # Unified React 18 Dual-Portal + Personal Budget Assistant UI
│   ├── index.html                   # Interactive React App with 3 Portals + Database Explorer Modal
│   ├── styles.css                   # Dark Glassmorphism Design System
│   ├── nginx.conf                   # Reverse proxy routing
│   └── Dockerfile
├── k8s/                             # Production Kubernetes Manifests with Autoscaling (HPA)
│   ├── config-and-secrets.yaml      # Namespace, ConfigMaps, and Secrets
│   ├── data-services.yaml           # PostgreSQL & Redis Deployments & Services
│   ├── microservices-hpa.yaml       # All 6 Microservices + HorizontalPodAutoscaler (HPA: 2 to 10 pods)
│   └── ingress.yaml                 # Unified Ingress Controller routing
```

---

## 🏛️ Microservice Family Architecture & Ports

| Port | Service Name | Family Responsibility | Key Endpoints |
| :--- | :--- | :--- | :--- |
| **8001** | **`auth-service`** | JWT Authentication, Registration, and RBAC (`customer` vs `seller`) | `POST /register`<br>`POST /login`<br>`GET /me`<br>`GET /customers`<br>`GET /sellers` |
| **8002** | **`advisory-service`** | Concessional Loan Router (10% Margin $\to$ 90% Loan, Micro $\le$ 1.4L vs Term Loan 1.4L-50L, Moratorium, Quarterly Amortization) & 6-Dimension Feasibility Studio | `POST /calculate-scheme`<br>`POST /generate-feasibility`<br>`POST /evaluate-full-proposal` |
| **8003** | **`marketplace-service`** | Enterprise equipment catalog, orders, and **Redis Cache** for top-selling goods | `GET /products/top-selling` *(Redis)*<br>`GET /products`<br>`POST /orders` |
| **8004** | **`recommendation-service`** | ML Recommender (TF-IDF & Cosine Similarity) for applicant equipment and seller high-demand inventory gaps | `POST /recommend/customer`<br>`POST /recommend/seller` |
| **8005** | **`analytics-service`** | ML Analytics (DSCR coverage, monthly runway, Scikit-Learn Linear Regression 90-day sales forecast) | `POST /analytics/customer-spending`<br>`POST /analytics/seller-sales` |
| **8006** | **`personal-budget-service`** | **VaultAI ReAct Agent Copilot**, `BudgetMemory`, undo stack, missing fields detection & report generator, affordability checker | `GET /api/budget/state`<br>`POST /api/budget/generate-report`<br>`POST /api/budget/chat`<br>`POST /api/budget/affordability` |
| **3000** | **`frontend`** | Unified React 18 Application (Customer, Personal Budget, and Seller Portals) | Accessible at `http://localhost:3000` |

---

## 🗄️ Amazon-Grade Relational Schema & PostgreSQL Database (`database/`)

The platform separates **Customers (Beneficiaries)** and **Sellers (Merchants)** using an Amazon-like enterprise database architecture:

1. **`database/customers.json`**:
   - Consumer profile modeled after Amazon Buyer & Concessional Lending beneficiaries.
   - Includes: `kyc_status` (Aadhaar verification), `shipping_address` (Panchayat, Block, District, Postal code), `enterprise_financials` (10% available margin capital, target sector, eligible 90% loan ceiling), and `customer_tier` (Prime Rural Beneficiary).
2. **`database/sellers.json`**:
   - Merchant profile modeled after Amazon Seller Central.
   - Includes: `legal_company_name`, `gstin`, `sca_vendor_license`, `seller_tier` (Platinum Rural Hub), `fulfillment_logistics` (FBA & Rural Direct hubs, return SLAs), and `merchant_performance` (positive feedback %, seller rating, total orders fulfilled).
3. **`database/schema.sql`**:
   - Complete PostgreSQL relational schema with foreign key constraints, indexes, and cascades across:
     - `users` (central auth & credentials)
     - `customer_profiles` (1-to-1 with `users`)
     - `seller_profiles` (1-to-1 with `users`)
     - `products` (Amazon ASIN/SKU catalog with FK to `seller_profiles`)
     - `orders` (Escrow disbursals with FK to `customer_profiles` and `products`)
4. **`database/seed_db.py`**:
   - Script to load JSON files, create the tables in PostgreSQL, and seed the profiles.
   - Includes automated query verification functions (`get_customer_by_id`, `get_seller_by_id`).
   - Run independently: `python database/seed_db.py`.

---

## 🔐 JWT Synchronization & Missing Fields Auto-Report Workflow


When a user logs in (or switches to the **Personal Budget Assistant** tab):
1. **JWT Extraction**: The frontend transmits the Bearer JWT token to `GET /api/budget/state`.
2. **Profile Syncing**: The microservice decodes the user identity (`sub`, `name`, `margin_capital`, `business_category`).
3. **Missing Fields Detection**: The service analyzes the user's personal financial state:
   - Is monthly income unconfigured?
   - Are category budgets (Food, Housing, Utilities, Travel) missing?
   - Is the target savings goal unset?
   - Are recent expense logs empty?
4. **Interactive Report Prompt**:
   - If missing fields are found, the UI displays an **Amber Alert Banner**:
     > *"Welcome Ramesh Patil! Your monthly budget parameters are uninitialized (Missing: Category Budgets, Savings Goal). Would you like VaultAI to auto-generate a recommended 50-30-20 budget plan synced with your enterprise profile (₹1,00,000 margin)?"*
5. **1-Click Generation**: Clicking **"⚡ Generate Budget Plan & Sync Profile"** sends `POST /api/budget/generate-report`:
   - Configures monthly income from enterprise drawings.
   - Allocates 5 category budget limits (50-30-20 rule).
   - Establishes a 20% liquid savings target.
   - Populates initial baseline expenses and executes a Scikit-Learn spending trend forecast!

---

## 🚀 How to Run & Verify Everything

### Option 1: Native Windows Execution (Single Command - Recommended)
Run the master ecosystem launcher from the root directory:
```bash
cd d:\Downloads\agenticproject
python run_ecosystem.py
```
This automatically boots all 6 FastAPI microservices and launches the React Dual-Portal on **`http://localhost:3000`**!

### Option 2: Docker Compose (All 9 Containers)
```bash
cd d:\Downloads\agenticproject
docker compose up --build
```
- Open `http://localhost:3000` for the React application.
- All 6 microservice APIs are available on ports 8001 through 8006.

### Option 3: Kubernetes Deployment with HPA (Horizontal Pod Autoscaler)
```bash
cd d:\Downloads\agenticproject
kubectl apply -f k8s/config-and-secrets.yaml
kubectl apply -f k8s/data-services.yaml
kubectl apply -f k8s/microservices-hpa.yaml
kubectl apply -f k8s/ingress.yaml
```
All microservices are configured with HPA:
- **Target CPU**: 70%
- **Min Replicas**: 2
- **Max Replicas**: 10

---

## 🛡️ DevOps Pre-Submission Architecture (DEVOPSPRESUB.pdf Aligned)

In strict accordance with `DEVOPSPRESUB.pdf`, this repository implements the full enterprise DevOps, Observability, and DevSecOps stack:

### 1. Canonical Enterprise Port Allocation Registry (Table 3.1.1)

| Canonical Port | Protocol | Subnet Placement | Service / Architectural Responsibility |
| :--- | :--- | :--- | :--- |
| **80** | TCP / HTTP | Public Subnet | Inbound HTTP traffic / Ingress Gateway |
| **443** | TCP / HTTPS | Public Subnet | TLS-terminated Public Gateway & SSL Offload |
| **5000** | TCP / HTTP | Private App Subnet | `budget-api-service` (Central ReAct REST Controller & State Engine) |
| **5001** | TCP / HTTP | Private App Subnet | `ai-agent-copilot` (Plan-Act ReAct Agent & Semantic Math Evaluator) |
| **5002** | TCP / HTTP | Private App Subnet | `ml-forecast-engine` (Scikit-Learn OLS Linear Regression & Health Index) |
| **5432** | TCP / PostgreSQL | Private DB Subnet | Amazon-grade PostgreSQL Relational Storage Engine |
| **6379** | TCP / RESP | Private DB Subnet | ElastiCache Redis Sub-millisecond Caching Mesh |
| **8080** | TCP / HTTP | Ops / CI Subnet | Jenkins Automation Master Controller |
| **8200** | TCP / HTTP | Security Mesh | HashiCorp Vault Secrets Management Engine |
| **9090** | TCP / HTTP | Monitoring Mesh | Prometheus Server Metrics Collector & Alerting Rules |
| **3000** | TCP / HTTP | Monitoring Mesh | Grafana Telemetry Dashboard & Financial Intelligence Visualizer |

---

### 2. Dual Deployment Flexibility: Cloud (AWS) & Offline Local

The entire platform is designed to operate seamlessly in two interchangeable execution modes:

#### Mode A: 100% Offline / Local Execution (Zero Cloud Dependency)
Run the full 11-container DevOps ecosystem locally using Docker Compose or native scripts:
```powershell
# Windows PowerShell
.\scripts\deploy_local.ps1
```
```bash
# Linux / macOS Bash
./scripts/deploy_local.sh
```
Or directly with Docker Compose:
```bash
docker compose -f docker-compose.devops.yml up --build -d
```

#### Mode B: Enterprise AWS Cloud Deployment via Terraform
Deploy the complete multi-AZ VPC, ECS Fargate cluster, RDS Postgres, ElastiCache Redis, ALB, and CloudWatch stack on AWS:
```powershell
# Windows PowerShell
.\scripts\deploy_aws.ps1 -DockerHubUser "your_username" -DockerHubPass "your_password"
```
```bash
# Linux / macOS Bash
./scripts/deploy_aws.sh your_username your_password
```
Or directly with Terraform:
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply -auto-approve
```
*Note: Set `enable_aws = false` in `terraform.tfvars` if you want Terraform to build and test Docker images locally without provisioning cloud resources!*

---

### 3. Automated CI/CD & DevSecOps Pipeline

#### Jenkins Automated Pipeline (`Jenkinsfile`)
Triggers automatically on GitHub commits or manually via the Jenkins dashboard:
1. **Stage 1: Checkout & Verification** - Pulls code from GitHub repository.
2. **Stage 2: Static Analysis (SAST) & Linting** - Flake8 style audit & Bandit AST security analysis (`bandit.yaml`).
3. **Stage 3: Automated Pytest Suite** - Runs 8 enterprise tests validating zero hallucination, mathematical affordability $A(X, k)$, ML forecasting ($R^2 \ge 0.92$), and agent semantic accuracy.
4. **Stage 4: Container Build & Trivy CVE Scan** - Builds microservice Docker images and scans with Trivy (`trivy.yaml`) enforcing 0 CRITICAL CVEs.
5. **Stage 5: Docker Hub Registry Push** - Automatically tags and pushes versioned images to Docker Hub registry (`image_tag`).
6. **Stage 6: Zero-Downtime Deployment** - Applies Kubernetes manifests (`k8s/vaultai-devops-complete.yaml`) or updates AWS ECS Fargate services.

#### Local DevSecOps Pipeline Runner:
```bash
python scripts/run_devsecops_pipeline.py
```
Outputs complete color-coded audit results for all 5 security and test stages.

#### Ecosystem Scorecard Audit:
```bash
python scripts/verify_ecosystem.py
```
Validates port socket bindings, Prometheus metric exporters (`/metrics`), Bandit report findings, and Table 11.1 benchmarks.

---

### 4. Telemetry, Observability & Automated Alerting

- **Prometheus Metrics Collector (Port 9090)**:
  - Scrapes `/metrics` across all microservices every 15 seconds.
  - Custom metrics: `pba_http_requests_total`, `pba_http_request_duration_seconds`, `pba_agent_tool_executions_total`, `pba_financial_health_index`.
  - Configured alert rules (`prometheus/alert_rules.yml`): `MicroserviceDown`, `HighHttp5xxErrorRate`, `HighRequestLatency`, `LowBudgetBalanceWarning`.
- **Grafana Enterprise Dashboard (Port 3000)**:
  - Auto-provisioned datasource pointing to Prometheus (`grafana/provisioning/datasources/prometheus.yml`).
  - Pre-loaded executive dashboard (`grafana/dashboards/vaultai_overview.json`) with request volume, latency p95/p99, agent tool executions, and Financial Health Index gauge.
- **AWS Lambda Budget Alert Handler (`aws_lambda/aws_lambda_alert.py`)**:
  - CloudWatch / SNS triggered serverless alert dispatcher.
  - Automatically posts critical Slack / Webhook notifications when category expenditures exceed budget limits.

