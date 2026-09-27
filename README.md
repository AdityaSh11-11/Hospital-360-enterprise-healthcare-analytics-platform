# 🏥 Hospital 360

### Enterprise Healthcare Analytics & Intelligence Platform

Hospital 360 is an end-to-end healthcare analytics platform designed to transform hospital operational, clinical, financial, claims, risk, and administrative data into structured decision intelligence.

The project combines **Python, Streamlit, PostgreSQL, ETL pipelines, analytical SQL, interactive visualizations, MIS reporting, data-quality monitoring, and AI-assisted analytics** within a unified healthcare intelligence application.

The platform is designed around a simple principle:

> **One hospital. One analytical platform. A complete 360° view of performance.**

---

## 📌 Project Overview

Healthcare organizations generate data across patients, admissions, doctors, departments, billing, insurance claims, laboratory tests, medications, operational workflows, and administrative systems.

When these datasets remain isolated, decision-makers struggle to answer even basic questions quickly.

Hospital 360 brings these analytical areas together into a centralized platform that supports:

- Executive decision-making
- Patient analytics
- Hospital operations monitoring
- Financial performance analysis
- Clinical and operational risk analysis
- Insurance claims intelligence
- Doctor performance analytics
- MIS reporting
- Data exploration
- ETL monitoring
- Data-quality management
- AI-assisted analytical querying
- Administrative exports and reporting

---

# 🎯 Project Objectives

Hospital 360 was developed to demonstrate how a modern healthcare analytics system can integrate the complete analytics lifecycle:

```text
Raw Healthcare Data
        ↓
Data Validation
        ↓
ETL / Data Processing
        ↓
PostgreSQL Data Warehouse
        ↓
Analytical Views
        ↓
Python Analytics Layer
        ↓
Interactive Dashboards
        ↓
MIS & Administrative Reporting
        ↓
AI-Assisted Analysis
        ↓
Management Decision Support
```

The goal is not simply to display charts.

The goal is to create a structured analytical environment where hospital data can be transformed into understandable, actionable information.

---

# ✨ Core Capabilities

## 🧭 Executive Command Center

Provides senior management with a high-level view of hospital performance.

Key areas include:

- Hospital activity overview
- Patient and admission indicators
- Operational KPIs
- Financial indicators
- Claims indicators
- Risk indicators
- Management-level performance summaries

---

## 👥 Patient Analytics

Provides analytical visibility into patient activity and hospital utilization.

Analysis may include:

- Patient population
- Admission trends
- Patient demographics
- Department utilization
- Length of stay
- Patient segmentation
- Admission patterns
- Clinical utilization indicators

---

## 🏥 Operations Analytics

Focuses on hospital operational performance.

Key areas include:

- Department workload
- Admission activity
- Bed utilization
- Length-of-stay analysis
- Operational throughput
- Department comparisons
- Capacity indicators
- Hospital activity trends

---

## 💰 Financial Intelligence

Provides visibility into the hospital's financial performance.

Key areas include:

- Billing performance
- Revenue trends
- Outstanding balances
- Payment analysis
- Department-level financial performance
- Payer contribution
- Financial KPIs
- Revenue distribution

---

## ⚠️ Risk Analytics

Supports identification and monitoring of operational and patient-related risk indicators.

Analysis includes:

- High-risk patient identification
- Risk segmentation
- Department risk distribution
- Risk trends
- Operational risk indicators
- Management risk summaries

---

## 🧾 Claims Intelligence

Provides analytical visibility into insurance and reimbursement workflows.

Key areas include:

- Claims submitted
- Claims approved
- Claims rejected
- Claims pending
- Claim amounts
- Approval and rejection patterns
- Insurer performance
- Outstanding claim exposure

---

## 👨‍⚕️ Doctor Performance Analytics

Provides structured performance analysis across doctors and specialties.

Possible indicators include:

- Doctor workload
- Patient volume
- Admissions handled
- Department contribution
- Revenue contribution
- Length-of-stay indicators
- Comparative performance metrics

---

## 🤖 AI Analyst

Hospital 360 includes an AI-assisted analytical layer designed to convert natural-language business questions into controlled analytical workflows.

Example questions:

```text
How many admitted patients are high risk?
```

```text
Which department has the highest admissions?
```

```text
What is the current claims rejection pattern?
```

```text
Which departments have the highest operational workload?
```

The AI analytical workflow is designed around:

```text
User Question
      ↓
Intent / Analytical Planning
      ↓
SQL Generation
      ↓
SQL Security Validation
      ↓
Read-Only Database Query
      ↓
Structured Result
      ↓
Natural-Language Explanation
```

---

# 🔐 AI SQL Security

A major part of the AI layer is controlled database access.

The SQL security layer is designed to allow analytical read operations while blocking unsafe database modifications.

Examples of blocked operations include:

```sql
DELETE
UPDATE
DROP
ALTER
TRUNCATE
INSERT
SELECT INTO
```

Additional protections include:

- Read-only analytical queries
- Multiple-statement blocking
- Restricted system-schema access
- Schema qualification requirements
- Controlled analytical database access
- SQL validation before execution

This helps separate AI-assisted analytics from unrestricted database access.

---

# 🔎 Data Explorer

The Data Explorer provides a controlled interface for exploring analytical datasets without directly accessing the database.

It supports:

- Dataset inspection
- Filtering
- Structured exploration
- Record-level investigation
- Analytical validation
- Operational troubleshooting

---

# 📑 MIS Reporting

Hospital 360 includes a Management Information System reporting workspace.

The MIS layer is intended to convert analytical results into management-friendly outputs.

Typical reporting areas include:

- Hospital performance summaries
- Patient reports
- Financial summaries
- Claims reports
- Operational summaries
- Risk reports
- Management reporting datasets

---

# 🛠 ETL Control Center

Hospital 360 contains a dedicated ETL and data-control workspace.

The control center provides visibility into:

- ETL batches
- Pipeline execution
- Records received
- Records inserted
- Records updated
- Records rejected
- Pipeline failures
- Data-quality checks
- Rejected records
- Warehouse freshness
- Audit information

This transforms the ETL layer from a hidden backend process into an observable operational component of the platform.

---

# 🛡 Data Quality Monitoring

Data quality is treated as part of the analytical architecture rather than an afterthought.

The platform supports monitoring of:

- Data-quality rules
- Validation status
- Records checked
- Failed records
- Rejected records
- Severity levels
- ETL-related data issues

---

# ⚙️ Administrative Workspace

The administrative layer acts as the centralized control area for platform-level operations.

The architecture separates analytical consumption from administrative actions.

Analytical pages focus on:

```text
Visualize
Explore
Understand
Compare
Analyze
```

Administrative functionality focuses on:

```text
Export
Download
Generate
Monitor
Control
Manage
```

This keeps operational controls separated from normal analytical dashboards.

---

# 📊 BI & Reporting Integration

The project architecture can support external business-intelligence artifacts alongside the Streamlit analytical application.

Supported or planned analytical outputs may include:

- CSV
- Excel
- PDF reports
- Power BI files
- Tableau artifacts
- Dashboard datasets

The administrative workspace acts as the logical location for centralized report and BI asset management.

---

# 🏗 System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     HOSPITAL 360                            │
│           Enterprise Healthcare Intelligence               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI LAYER                       │
│                                                             │
│ Executive │ Patients │ Operations │ Finance │ Risk          │
│ Claims │ Doctors │ AI │ Explorer │ MIS │ ETL │ Admin        │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   ANALYTICS / SERVICE LAYER                 │
│                                                             │
│ Python Analytics │ KPI Logic │ Formatting │ Reporting       │
│ Charting │ Filters │ Export Services │ AI Analyst           │
└─────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
┌────────────────────────────┐  ┌─────────────────────────────┐
│       AI ANALYTICS         │  │       DATA ACCESS           │
│                            │  │                             │
│ Natural Language           │  │ Parameterized Queries       │
│ Analytical Planning        │  │ Analytical Views            │
│ SQL Generation             │  │ Warehouse Queries           │
│ SQL Guard                  │  │ Cached Data Access          │
│ Result Explanation         │  │                             │
└────────────────────────────┘  └─────────────────────────────┘
                │                         │
                └────────────┬────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                       POSTGRESQL                            │
│                                                             │
│ warehouse.*        analytics.*        control.*             │
│                                                             │
│ Dimensions         Analytical Views    ETL Batches           │
│ Facts              KPI Views           Data Quality          │
│ Healthcare Data    Reporting Views     Rejections            │
│                                         Audit                │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌─────────────────────────────────────────────────────────────┐
│                         ETL LAYER                           │
│                                                             │
│ Source Data → Validation → Transformation → Warehouse       │
└─────────────────────────────────────────────────────────────┘
```

---

# 🗄 Data Architecture

Hospital 360 uses a structured PostgreSQL analytical architecture.

## Warehouse Layer

The warehouse contains analytical dimensions and fact tables.

Typical entities include:

```text
dim_patient
dim_doctor
dim_department
dim_date

fact_admission
fact_billing
fact_claim
fact_lab_test
fact_medication
```

---

## Analytics Layer

The analytics schema provides reporting-oriented database views used by dashboards and analytical services.

This separates:

```text
Storage Logic
     ↓
Analytical Logic
     ↓
Presentation Logic
```

and reduces duplication across dashboard pages.

---

## Control Layer

The control schema supports operational governance of the data platform.

Typical control entities include:

```text
etl_batch
data_quality_log
rejected_record
audit_log
```

---

# 🔄 ETL Architecture

```text
Source Healthcare Data
        ↓
Input Validation
        ↓
Transformation
        ↓
Business Rules
        ↓
Data Quality Checks
        ↓
Rejected Record Handling
        ↓
Warehouse Load
        ↓
Analytical Views
        ↓
Dashboard Refresh
```

ETL execution metadata is retained so pipeline performance and failures can be inspected through the application.

---

# 🎨 Application Design System

Hospital 360 uses a centralized visual design system to maintain consistency across analytical workspaces.

The interface follows an enterprise healthcare design language based on:

- Light analytical workspace
- Institutional blue navigation
- High-contrast typography
- Structured KPI cards
- Consistent chart styling
- Clear analytical sections
- Responsive dashboard layouts
- Management-friendly terminology
- Controlled use of status colors

Typical page flow:

```text
Page Identity
      ↓
Business Context
      ↓
Filters
      ↓
Executive KPIs
      ↓
Primary Analysis
      ↓
Supporting Analysis
      ↓
Management Insight
      ↓
Detailed Records
      ↓
Navigation / Next Analysis
```

---

# 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Programming | Python |
| Application UI | Streamlit |
| Database | PostgreSQL |
| Data Processing | Pandas |
| Visualization | Plotly |
| Data Access | SQL / Python |
| AI Analytics | Gemini API |
| Configuration | python-dotenv |
| Version Control | Git & GitHub |
| Architecture | Analytics + Warehouse + Control Layers |

---

# 📂 Project Structure

A simplified representation of the project:

```text
hospital-360/
│
├── app.py
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── ai/
│   ├── analyst.py
│   ├── gemini_client.py
│   └── sql_guard.py
│
├── analytics/
│   └── data_loader.py
│
├── database/
│
├── etl/
│
├── pages/
│   ├── 01_Executive_Command_Center.py
│   ├── 02_Patient_Analytics.py
│   ├── 03_Operations.py
│   ├── 04_Finance.py
│   ├── 05_Risk.py
│   ├── 06_Claims.py
│   ├── 07_Doctor_Performance_Dashboard.py
│   ├── 08_AI_Analyst.py
│   ├── 09_Data_Explorer.py
│   ├── 10_MIS_Reports.py
│   ├── 11_ETL_Control_Center.py
│   └── 12_Admin.py
│
├── utils/
│   └── app_helpers.py
│
├── data/
│   ├── exports/
│   └── incremental/
│
└── reports/
```

The exact project structure may evolve as the platform is extended.

---

# 🚀 Running the Project Locally

## 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd Hospital-360-enterprise-healthcare-analytics-platform
```

---

## 2. Create a virtual environment

### Windows

```powershell
python -m venv hospital
hospital\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv hospital
source hospital/bin/activate
```

---

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create:

```text
.env
```

using `.env.example` as the template.

Example:

```env
APP_NAME=Hospital 360
APP_VERSION=1.0.0
APP_ENV=development

DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Never commit the real `.env` file.

---

## 5. Configure PostgreSQL

Hospital 360 expects the required PostgreSQL schemas, tables, analytical views, and control objects to exist.

The analytical architecture uses schemas such as:

```text
warehouse
analytics
control
```

Configure the database using the SQL/database assets included with the project.

---

## 6. Start the application

```bash
streamlit run app.py
```

Streamlit will display the local application URL in the terminal.

---

# 🔑 Environment Variables

| Variable | Purpose |
|---|---|
| `APP_NAME` | Application name |
| `APP_VERSION` | Application release version |
| `APP_ENV` | Runtime environment |
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Gemini API authentication |

Sensitive environment variables must never be committed to source control.

---

# 🔒 Security Considerations

Hospital 360 follows several application-level security principles:

- Secrets are stored outside source control
- `.env` files are ignored by Git
- AI-generated SQL is validated before execution
- Destructive SQL operations are blocked
- Multiple SQL statements are rejected
- System-schema access can be restricted
- Analytical queries use controlled schemas
- Administrative functions are logically separated from analytical pages
- Database access is centralized

This project is an analytics demonstration and should not be treated as a production clinical system without additional security, privacy, authentication, authorization, audit, and compliance controls.

---

# 🧪 SQL Security Regression Testing

The SQL guard can be tested against safe and unsafe statements.

Example expected behavior:

```text
SAFE SELECT
Safe   : True

DELETE
Safe   : False

UPDATE
Safe   : False

DROP
Safe   : False

MULTI STATEMENT
Safe   : False

SYSTEM SCHEMA
Safe   : False

UNQUALIFIED TABLE
Safe   : False

SELECT INTO
Safe   : False
```

This provides an additional safety layer between AI-generated analytical intent and database execution.

---

# 📈 Analytical Philosophy

Hospital 360 separates information into three levels.

### Level 1 — Executive KPIs

Answers:

> What is happening?

Examples:

- Admissions
- Revenue
- Outstanding amount
- Claims
- High-risk patients

### Level 2 — Analytical Visualizations

Answers:

> Where and how is it happening?

Examples:

- Monthly trends
- Department comparisons
- Insurer analysis
- Doctor performance
- Risk distributions

### Level 3 — Management Insights

Answers:

> Why does this matter?

This structure makes the platform useful to both analytical and non-technical users.

---

# 👥 Intended Users

Hospital 360 is designed conceptually for:

- Hospital administrators
- Healthcare analysts
- Operations managers
- Finance teams
- Claims teams
- Department managers
- Data teams
- MIS teams
- Executive leadership

---

# ⚠️ Data Disclaimer

This project is intended for:

- Portfolio demonstration
- Data engineering practice
- Healthcare analytics learning
- BI development
- SQL and PostgreSQL practice
- AI-assisted analytics experimentation

The project uses **synthetic/demo healthcare data**.

It is **not intended for real clinical diagnosis, medical treatment decisions, or production patient-care workflows**.

---

# 🛣 Future Enhancements

Potential future improvements include:

- Production cloud deployment
- Authentication and role-based access control
- Advanced authorization
- Scheduled ETL orchestration
- Automated report generation
- Power BI integration
- Enhanced anomaly detection
- Forecasting
- Advanced clinical risk models
- Real-time operational monitoring
- Notification workflows
- Containerized deployment
- CI/CD pipelines
- Automated testing
- Observability and application monitoring

---

# 💡 What This Project Demonstrates

Hospital 360 demonstrates practical experience across multiple areas of modern analytics engineering:

```text
Python Development
        +
SQL Engineering
        +
PostgreSQL
        +
Data Warehousing
        +
ETL Engineering
        +
Data Quality
        +
Streamlit
        +
Plotly
        +
Healthcare Analytics
        +
Financial Analytics
        +
MIS Reporting
        +
AI-Assisted Analytics
        +
SQL Security
        +
Git / GitHub
```

It is designed as an integrated analytical system rather than a collection of disconnected dashboards.

---

# 📸 Screenshots

Add application screenshots here as the interface is finalized.

Recommended screenshots:

```text
docs/screenshots/
├── executive-command-center.png
├── patient-analytics.png
├── operations.png
├── finance.png
├── risk.png
├── claims.png
├── doctor-performance.png
├── ai-analyst.png
├── etl-control-center.png
└── admin-center.png
```

Example:

```markdown
![Hospital 360 Executive Command Center](docs/screenshots/executive-command-center.png)
```

---

# 🤝 Contributions

This repository currently represents an independently developed healthcare analytics portfolio project.

Suggestions, improvements, and technical feedback are welcome through GitHub issues or pull requests.

---

# 👨‍💻 Author

**Aditya**

GitHub: `AdityaSh11-11`

Project:

**Hospital 360 — Enterprise Healthcare Analytics & Intelligence Platform**

---

# ⭐ Support

If you find this project useful or interesting, consider starring the repository.

It helps demonstrate interest in the project and supports continued development.

---

<p align="center">
  <strong>Hospital 360</strong><br>
  Enterprise Healthcare Analytics & Intelligence Platform
</p>

<p align="center">
  Built with Python · Streamlit · PostgreSQL · Plotly · AI-assisted Analytics
</p>
