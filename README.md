# 📡 QoS Buddy — Suite Complète d'Analyse Télécom

**QoS Buddy** est une plateforme d'analyse et de machine learning complète dédiée à l'optimisation de la Qualité de Service (QoS) dans les réseaux de télécommunication. Elle couvre trois domaines métier critiques (BO1, BO2, BO3) avec des modèles prédictifs et des recommandations opérationnelles.

---

## 🎯 Objectif Global

Fournir une **suite de 3 modèles analytiques** qui travaillent ensemble pour :
1. **🚨 BO1** — Détecter les anomalies réseau avant qu'elles n'impactent les clients (4G LTE)
2. **📱 BO2** — Prédire les violations de contrats SLA B2B 15/30/60 minutes à l'avance (5G)
3. **🏗️ BO3** — Identifier les zones prioritaires pour l'investissement CAPEX (analyse réseau Nigeria)

---

## 📂 Structure du Projet

```
qos-buddy4DS8-main/
│
├── Anomaly_Detection.ipynb          # BO1 — Détection anomalies 4G
├── SLA_prediction.ipynb             # BO2 — Early warning violations SLA 5G
├── repartition_zones.ipynb          # BO3 — Scoring CAPEX & zone ranking
├── README.md                        # Ce fichier
└── outputs/                         # Exports et modèles sauvegardés
```

---

## 📓 Fichier 1 : **Anomaly_Detection.ipynb** (BO1)

### 🎯 Objectif Business
Détecter **automatiquement les comportements anormaux** des stations de base (eNB) dans les réseaux 4G LTE **avant qu'ils n'affectent les clients**. Les anomalies sont souvent causées par des événements externes (concerts, matchs sportifs, catastrophes) qui saturent localement le réseau.

### 📊 Dataset
- **Source** : Compétition ML-MATT 4G Cellular Networks
- **Période** : 2 semaines avec mesures toutes les 15 minutes
- **Stations de base** : 10 eNB, 33 cellules
- **Volume** : ~36 904 observations
- **Variable cible** : `Behaviour` (Normal / Anomalous)

### 🔑 Key Performance Indicators (KPIs)

| KPI | Description | Unité | Logique Anomalie |
|---|---|---|---|
| `PRBUsageUL` | % usage des ressources (Uplink) | % | Valeur élevée = saturation |
| `PRBUsageDL` | % usage des ressources (Downlink) | % | Valeur élevée = saturation |
| `meanThr_DL` | Débit moyen (Downlink) | Mbps | Débit bas = dégradation |
| `meanThr_UL` | Débit moyen (Uplink) | Mbps | Débit bas = dégradation |
| `maxThr_DL/UL` | Débit maximum (Downlink/Uplink) | Mbps | Crête basse = problème |
| `meanUE_DL/UL` | Nombre moyen d'utilisateurs actifs | count | Plus d'utilisateurs = charge ↑ |
| `maxUE_DL/UL` | Nombre maximum d'utilisateurs | count | Pics de demande |
| `maxUE_UL+DL` | Utilisateurs totaux simultanés | count | Charge aggregate |

### 📈 Étapes d'Analyse

#### **Étape 1-3 : Préparation des Données**
- Chargement du dataset train/test (séparation 70/30)
- Parsing temporel (conversion Time en datetime)
- Détection des classes : identification de la classe normale et anomale

#### **Étape 4 : Équilibre des Classes**
```
Distribution Observable :
├─ Classe Normal    : ~90-95% des observations
└─ Classe Anomaly   : ~5-10% → Déséquilibre classique
```
**Action** : Appliquer SMOTE (Synthetic Minority Over-sampling) ou pondération lors de l'entraînement.

#### **Étape 5 : Analyse Temporelle**
Extraction des patterns **temporels** d'anomalies :
- **Taux par heure** : Identifiez les pics de 7h-9h (commute matinale) et 18h-21h (soirée) où les anomalies sont + fréquentes
- **Taux par jour de semaine** : Détectez si week-end < weekday en anomalies
- **Heatmap Heure × Jour** : Matrice 24×7 montrant les zones rouges (critiques)

**Insight BO1** : Renforcer la capacité réseau en anticipation des périodes à haut risque (pre-provisioning).

#### **Étape 6-7 : Analyse des KPIs**
- **Histogrammes** : Distribution brute Normal vs Anomalous par KPI
- **Boxplots** : Comparaison des médianes et dispersions entre les deux classes

**Exemple** : Si `PRBUsageDL` affiche une médiane de 55% en Normal et 85% en Anomalous → c'est un bon prédicteur.

#### **Étape 8 : Tests Statistiques**
| Test | Métrique | Interprétation |
|---|---|---|
| **Mann-Whitney U** | p-value | H0 : distributions identiques. p < 0.05 → KPI discriminant |
| **Point-Biserial** | Corrélation | Force du lien entre KPI et classe ([-1 ; 1]) |

**Résultat** : Classement des KPIs par importance → Top 3-5 suffisent souvent pour un modèle performant.

#### **Étape 9 : Modélisation**
**Modèles testés** :
- `LogisticRegression` (baseline simple)
- `RandomForestClassifier` (robustesse)
- `LGBMClassifier` (optimisation pour données déséquilibrées)

**Métrique** : Recall (priorité : ne pas manquer les anomalies) > Precision

#### **Étape 10 : Production**
- Prédictions sur ensemble test
- Export des seuils de décision optimaux (courbe ROC/PR)
- Recommandations opérationnelles

### 💼 Utilisation Opérationnelle
- **Dashboard temps réel** : Alertes quand anomalie détectée sur une cellule
- **Pre-provisioning** : Augmenter la capacité 30 min avant une période critique
- **SLA tracking** : Corréler anomalies avec dégradations client

---

## 📓 Fichier 2 : **SLA_prediction.ipynb** (BO2)

### 🎯 Objectif Business
Prédire les **violations de contrats SLA B2B** dans les réseaux 5G avec un horizon de **15, 30, et 60 minutes**. Permet de déclencher des alertes préventives avant que les clients ne soient affectés.

### 📊 Dataset
- **Source** : `AliMaatouk/TelecomTS` (Hugging Face)
- **Type** : Séries temporelles multi-KPI 5G
- **Volume** : ~500 samples (chunks), N points temporels par chunk
- **Résolution** : Mesures à intervalle régulier (~1 min)
- **Variable cible** : Construite via règles KPI (100% NaN dans le dataset brut)

### 🔑 KPIs 5G Monitoriés

| KPI | Seuil Violation (SLA) | Logique |
|---|---|---|
| `RSRP` | < p10 (puissance signal) | Signal trop faible = déconnexion risque |
| `BLER` | > p90 (block error rate) | Trop d'erreurs = dégradation |
| `DL/UL_MCS` | < p10 (modulation) | Modulation dégradée = débit ↓ |
| `TX/RX_Bytes` | < p10 (débit) | Throughput insuffisant |
| `Estimated_UL_Buffer` | > p90 (saturation) | Buffer plein = congestion |
| `PRB_Utilization` | > p90 (ressources) | Ressources saturées |
| `DL/UL_NumberOfPackets` | < p10 (traffic) | Peu de paquets traités |
| `UL_NPRB` | < p10 (ressources) | Ressources Uplink limitées |

### 📈 Étapes d'Analyse

#### **Étape 1-3 : Extraction & Mise à Plat**
- **Chargement** : JSON/JSONL → pandas DataFrame (1 ligne = 1 instant temporel)
- **Parsing temporel** : Création index `pd.date_range(start, end, periods=N)`
- **Exploration** : Dimensions, valeurs manquantes, distributions KPIs bruts

#### **Étape 4-5 : Nettoyage Robustesse**
- Suppression doublons (série_id + timestamp)
- Valeurs négatives → NaN (impossible physiquement)
- **Winsorisation p99.5** : Cap les valeurs extrêmes (outliers bruits)
- **Imputation temporelle** : Interpolation linéaire par série (preserve trend)

#### **Étape 6 : Construction Cible SLA**
**Logique métier** :
```python
SLA_BREACH_RISK[t] = 1 si ∃ KPI ∈ violation à instant t
                   = 0 sinon
```

**Calcul des seuils** (sur données réelles) :
- KPIs "élevée = problème" (BLER, Buffer, PRB_Utilization) : violation si **> p90**
- KPIs "basse = problème" (RSRP, SNR, MCS, Bytes, NPRB) : violation si **< p10**

**Résultat** :
- `sla_breach_risk` : binaire (0/1)
- `sla_risk_level` : catégorique (OK / Risque faible / Risque élevé / Critique)
- `n_sla_violations` : nombre de KPIs simultanément hors SLA

#### **Étape 7 : Feature Engineering TS-SAFE**
**Groupé par série** (évite fuite data) :

| Groupe | Features | Détail |
|---|---|---|
| **A — Brutes** | KPIs originaux | Valeurs 1:1 |
| **B — Proximité SLA** | `sla_prox_*` | Ratio : 1 = au seuil, >1 = violation |
| **C/D — Temporelles** | `*_lag1/2/3`, `*_diff1`, `*_pct1`, `*_rmean{3,6,12}`, `*_rstd`, `*_rmax`, `*_trend` | Lags, déltas, moyennes mobiles |
| **E — Pré-alerte** | `prealert_*`, `n_prealert` | Flags si KPI entre seuil-20% et seuil |
| **F — Temporel** | `hour`, `hour_sin/cos`, `dayofweek`, `is_business` | Cyclique + business hours |

#### **Étape 8 : Corrélation avec SLA**
- **Calcul** : Pearson |corrélation| avec `sla_breach_risk`
- **Sélection** : Top 20 features
- **Filtrage** : Corr > 0.1 (signal fort)

#### **Étape 9 : Split Temporel & Preprocessing**
- **Split** : 80% train / 20% val **par série, in-chronological order**
- **Imputation** : Fit sur train uniquement (`SimpleImputer`)
- **Scaling** : `RobustScaler` fit sur train uniquement (évite fuite)

#### **Étape 10 : Early Warning Targets**
Construction de cibles multi-horizons :
```
breach_within_15min[t] = 1 si ∃ t' ∈ ]t; t+15min] avec breach
breach_within_30min[t] = 1 si ∃ t' ∈ ]t; t+30min] avec breach
breach_within_60min[t] = 1 si ∃ t' ∈ ]t; t+60min] avec breach
```

**Usage** : Prédire 60 min à l'avance pour avoir temps actionner correctifs.

#### **Étape 11 : Modélisation Baseline**
**Modèle** : `HistGradientBoostingClassifier`
- Learning rate : 0.05
- Max depth : 6
- Iterations : 300
- Sample weights : équilibrage sans SMOTE

**Métriques** (validation set) :
- ROC-AUC : score ségrégation global
- PR-AUC : score precision-recall (important pour anomalies)
- F1-optimal : seuil décision optimisé

#### **Étape 12 : Export Dashboard**
**Fichiers générés** :
1. `fact_bo2_early_warning.(parquet|csv)` : Faits consolidés
2. `dim_time.(parquet|csv)` : Dimension temps
3. `telecomts_bo2_features_full.(parquet|csv)` : Toutes features (réentraînement)
4. `bo2_ew_hgb_60min.joblib` : Modèle sérialisé

### 💼 Utilisation Opérationnelle
- **Alertes dynamiques** : Score proba breach en continu
- **BI/Dashboard** : Brancher Power BI / Qlik sur fact_bo2_early_warning
- **SLA management** : Trigger correctifs avant rupture (redirection trafic, boost ressources)

---

## 📓 Fichier 3 : **repartition_zones.ipynb** (BO3)

### 🎯 Objectif Business
Identifier les **zones géographiques prioritaires** pour l'investissement CAPEX réseau. Maximiser le ROI en concentrant les investissements sur zones à fort potentiel ou grande pénurie de capacité.

### 📊 Dataset
- **Source** : Nigerian Telecom Quality of Service Metrics (HF)
- **Scope** : Zones géographiques Nigeria
- **Features** : Latence, débit, charge utilisateurs, type réseau
- **Granularité** : Agrégation par zone / région

### 🏗️ Pipeline Deep Learning

```
┌─────────────────┐
│   Raw Data      │
└────────┬────────┘
         │
    [Step 1] EDA Rapide
         │
    [Step 2] Feature Engineering CAPEX
         │ ├─ CAPEX Score (target composite)
         │ ├─ Zone Performance Index
         │ └─ Network Gap Score
         │
    [Step 3] Preprocessing & Normalisation
         │
    ┌────┴────┐
    │          │
[Step 4]   [Step 5]
  MLP        LSTM/GRU
  Dense      Temporal
  NN         Patterns
    │          │
    └────┬─────┘
         │
    [Step 6] TabNet
    Attention-based
    Tabular DL
         │
    [Step 7] Autoencoder
    Anomaly Detection
    Zone Compression
         │
    [Step 8] CAPEX Zone Ranking
    ├─ Top zones à investir
    ├─ Heatmap priorités
    └─ Recommandations
```

### 📈 Étapes d'Analyse

#### **Étape 1 : Setup & Data Loading**
- Chargement dataset
- Installation dépendances (torch, pytorch-tabnet, shap)
- Configuration device (GPU/CPU)

#### **Étape 2 : Feature Engineering CAPEX**
**Indicateurs construits** :

| Indicateur | Formule | Interprétation |
|---|---|---|
| **CAPEX Score** | f(latence, débit, signal, utilisateurs, age_réseau) | 0-100 : urgence investissement |
| **Zone Performance Index** | Normalisation [0; 1] KPIs qualité | 1 = excellent, 0 = dégradé |
| **Network Gap Score** | Max(KPI_p90) - Actual / Max * 100 | % gap vs performance attendue |

**Logique de scoring** :
- Latence élevée → forte pénalité (→ CAPEX urgent)
- Débit bas → forte pénalité
- Signal faible → pénalité modérée
- Trop d'utilisateurs → multiplicateur (amplify urgency)
- Ancien type réseau (2G/3G) → bonus CAPEX (modernisation)

#### **Étape 3-4 : Modèle MLP**
**Architecture** :
```
Input (N features)
  ↓
Dense(128) + ReLU + BatchNorm + Dropout(0.3)
  ↓
Dense(64) + ReLU + BatchNorm + Dropout(0.2)
  ↓
Dense(32) + ReLU
  ↓
Output(1) → CAPEX Score [0-100]
```

**Entraînement** : MSE loss, Adam optimizer, Early stopping

**Output** : Score continu CAPEX par zone

#### **Étape 5 : Modèle LSTM/GRU**
**Tâche** : Prédiction temporelle (forecast QoS future)

**Architecture** :
```
Input Sequence (T timesteps × N features)
  ↓
LSTM/GRU(64 units)
  ↓
Dense(32) + ReLU
  ↓
Output(1) → QoS t+horizon
```

**Intérêt** : Identifier zones en dégradation croissante → investissement avant crise

#### **Étape 6 : Modèle TabNet**
Transformer attention-based pour données tabulaires (non-séquentielles).

**Avantage** : Explainability (importance de chaque feature visible)

#### **Étape 7 : Autoencoder**
Détection d'anomalies et compression d'information.

**Usage** : Identifier zones "atypiques" méritant analyse experte

#### **Étape 8 : CAPEX Zone Ranking**
**Output final** :
1. **Top N zones** : Priorisation d'investissement
2. **Heatmap géographique** : Visualisation urgence par région
3. **Recommandations** : Type d'investissement par zone
   - Réseau saturé → Densification cellulaire
   - Signal faible → Déploiement small-cells
   - Ancien réseau → Modernisation 4G/5G

### 💼 Utilisation Opérationnelle
- **Planification budgétaire** : Allocation CAPEX 3-5 ans
- **ROI maximization** : Prioriser zones à fort potentiel croissance
- **Strategic planning** : Alignement deployments avec objectifs expansion

---

## 🛠️ Dépendances & Environnement

### Python Packages (Common)
```bash
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=0.24.0
matplotlib>=3.4.0
seaborn>=0.11.0
scipy>=1.7.0
```

### BO1 (Anomaly Detection)
```bash
lightgbm>=3.3.0
imbalanced-learn>=0.8.0
```

### BO2 (SLA Prediction)
```bash
datasets>=2.0.0
joblib>=1.1.0
```

### BO3 (CAPEX Zones)
```bash
torch>=1.10.0
pytorch-tabnet>=3.1.0
shap>=0.40.0
```

### Installation
```bash
# Google Colab
!pip install pandas numpy scikit-learn matplotlib seaborn scipy lightgbm imbalanced-learn datasets joblib torch pytorch-tabnet shap

# Local
pip install -r requirements.txt
```

---

## 📊 Outputs & Artifacts

### BO1 Outputs
- Modèles entraînés (pkl/joblib)
- Seuils de décision optimaux
- Rapports classification (precision/recall/F1)
- Visualisations EDA

### BO2 Outputs
Directory `outputs/` :
- `fact_bo2_early_warning.parquet` — Données consolidées pour BI
- `dim_time.parquet` — Dimension temps
- `telecomts_bo2_features_full.parquet` — Toutes features complètes
- `bo2_ew_hgb_60min.joblib` — Modèle sérialisé

### BO3 Outputs
- Scoring CAPEX par zone
- Heatmap priorités géographiques
- Feature importance (SHAP)
- Recommandations investissement

---

## 🎓 Key Insights par BO

### BO1 — Anomaly Detection
- ✅ **Patterns horaires** : Anomalies concentrées 7-9h et 18-21h → pre-provisioning stratégique
- ✅ **PRB Usage** : Meilleur prédicteur d'anomalies (corrélation forte)
- ✅ **Déséquilibre classes** : SMOTE ou pondération essentiel

### BO2 — SLA Prevention
- ✅ **Early warning** : 60 min suffisent pour action corrective
- ✅ **Proximité seuils** : KPI near-SLA plus discriminant que KPI brut
- ✅ **Fuite data** : Split temporel + fit preprocessing sur train only
- ✅ **Multi-horizon** : Ensemble (15/30/60 min) meilleur que modèle unique

### BO3 — CAPEX Scoring
- ✅ **Composite targets** : CAPEX Score > single KPI
- ✅ **Deep learning** : TabNet/Autoencoder pour explainability
- ✅ **Temporal aspect** : LSTM détecte zones en dégradation croissante
- ✅ **Geography** : Heatmaps géospatiales plus actionnable que liste

---

## 🚀 Prochaines Étapes

### Court terme
1. **Validation métier** : Reviews avec équipes opérations + CAPEX planning
2. **A/B testing** : Comparer alertes BO1/BO2 vs procédures legacy
3. **Tuning hyperparamètres** : GridSearch / Bayesian optimization

### Moyen terme
1. **Intégration BI** : Dashboards temps réel (Power BI / Qlik)
2. **Monitoring** : Drift detection (données production vs train)
3. **Feedback loops** : Amélioration itérative modèles

### Long terme
1. **Multi-modal** : Intégrer données externes (météo, événements)
2. **Causal inference** : Déterminer causes anomalies (pas juste détection)
3. **Prescriptive analytics** : Recommandations actions auto (vs alertes seul)

---

## 📞 Support & Contact

**Questions / Bugs / Contributions** : Ouvrir issue ou PR sur le dépôt

---

**Dernière mise à jour** : Février 2026

**Status** : Production-Ready (BO1, BO2) | Prototype (BO3)