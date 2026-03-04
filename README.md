# 📡 QoS Buddy — BO2: SLA Breach Prevention (B2B)

<p align="center">
  <img src="https://img.shields.io/badge/Project-QoSBuddy-blue?style=for-the-badge&logo=wifi" />
  <img src="https://img.shields.io/badge/Domain-Telecom%205G-green?style=for-the-badge&logo=antenna" />
  <img src="https://img.shields.io/badge/ML-Early%20Warning%20System-orange?style=for-the-badge&logo=tensorflow" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" />
</p>

---

## 🎯 Objective

**QoS Buddy — BO2** is a machine learning pipeline designed to **predict SLA violations in advance** for B2B telecom clients using real 5G network time-series KPIs.

> The `label` column is 100% NaN in the raw dataset → the SLA target is **entirely constructed** from KPI-based rules (p10/p90 percentile thresholds).

---

## 📦 Dataset

| Field | Value |
|---|---|
| **Source** | [`AliMaatouk/TelecomTS`](https://huggingface.co/datasets/AliMaatouk/TelecomTS) |
| **Type** | 5G multi-KPI time series |
| **Format** | Chunked JSONL |

### 📶 KPIs Used

| Category | KPIs |
|---|---|
| **Radio** | `RSRP`, `UL_SNR`, `DL_MCS`, `UL_MCS`, `UL_NPRB` |
| **Error Rates** | `DL_BLER`, `UL_BLER` |
| **Throughput** | `TX_Bytes`, `RX_Bytes`, `DL_NumberOfPackets`, `UL_NumberOfPackets` |
| **Resources** | `PRBs_DL_Current`, `PRBs_UL_Current`, `PRB_Utilization_DL`, `PRB_Utilization_UL`, `Estimated_UL_Buffer` |

---

## 🏗️ Pipeline Overview

```
TelecomTS Dataset
      │
      ▼
① Imports & Setup
      │
      ▼
② Dataset Loading (HuggingFace)
      │
      ▼
③ Series Extraction & Flattening
      │
      ▼
④ Exploratory Data Analysis
      │
      ▼
⑤ Cleaning & Imputation
      │
      ▼
⑥ SLA Target Construction (p10/p90 thresholds)
      │
      ▼
⑦ Feature Engineering (TS-safe, per series_id)
      │
      ▼
⑧ Feature Matrix & SLA Correlation
      │
      ▼
⑨ Temporal Split & Scaling (RobustScaler)
      │
      ▼
⑩ Early Warning Targets (15 / 30 / 60 min)
      │
      ▼
⑪ Multi-Model Training & Comparison
      │
      ▼
⑫ Dashboard Export
```

---

## 🏷️ SLA Target Construction

Since labels are unavailable, `sla_breach_risk` is built from KPI thresholds:

| KPI Type | Business Logic | Threshold |
|---|---|---|
| `BLER`, `Buffer`, `PRB_Utilization` | High value = problem | > p90 |
| `RSRP`, `SNR`, `MCS`, `Bytes`, `Packets`, `NPRB`, `PRBs` | Low value = problem | < p10 |

---

## 🤖 Models Compared

| Model | Notes |
|---|---|
| **HistGradientBoostingClassifier** | Baseline — handles NaN natively |
| **RandomForestClassifier** | Ensemble, robust to outliers |
| **LogisticRegression** | Linear baseline, interpretable |
| **XGBClassifier** | Gradient boosting (if xgboost installed) |
| **LGBMClassifier** | Lightweight boosting (if lightgbm installed) |

**Metrics**: ROC-AUC · PR-AUC · Optimal F1 · Training time

---

## ⏰ Early Warning Horizons

| Horizon | Target Column |
|---|---|
| 15 minutes | `breach_15min` |
| 30 minutes | `breach_30min` |
| 60 minutes | `breach_60min` |

---

## ⚙️ Feature Engineering

All features are computed **per series** (`groupby series_id`) to **prevent data leakage**:

- Rolling statistics (mean, std, min, max)
- `sla_proximity` — how close current KPIs are to SLA thresholds
- `prealert` — binary flag triggered before a breach window

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install pandas numpy matplotlib seaborn scikit-learn datasets joblib
pip install xgboost lightgbm  # optional
```

### Run the Notebook

```bash
jupyter notebook QoSBuddy_TelecomTS_BO2_MULTI_MODELS.ipynb
```

---

## 📁 Project Structure

```
📦 QoS-Buddy
 ┣ 📓 QoSBuddy_TelecomTS_BO2_MULTI_MODELS.ipynb   # Main pipeline notebook
 ┣ 📄 README.md                                     # This file
 ┗ 📊 outputs/                                      # Dashboard exports (generated)
```

---

## 🏫 Academic Context

This project is developed as part of the **Esprit School of Engineering** final-year engineering program (4DS8 — 2026).

**Team**: QoS-Buddy-Team  
**Organization**: [github.com/orgs/QoS-Buddy-Team](https://github.com/orgs/QoS-Buddy-Team)

---

## 📜 License

This project is for academic and research purposes.
