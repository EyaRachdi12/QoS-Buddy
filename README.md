
![Python](https://img.shields.io/badge/Python-3.10-blue)
![Status](https://img.shields.io/badge/Status-Production-green)
![Esprit](https://img.shields.io/badge/Esprit-School_of_Engineering-red)

# QoS Buddy – Suite d’Analyse Prédictive pour l’Optimisation de la QoS Télécom

## Overview

Ce projet a été développé dans le cadre du PIDEV – 4ème année ingénierie à Esprit School of Engineering (Année académique 2025–2026).

QoS Buddy est une plateforme avancée d’analyse et de data science dédiée à l’amélioration proactive de la Qualité de Service (QoS) dans les réseaux de télécommunication.  
Le projet suit la méthodologie **TDSP (Team Data Science Process)** afin d’assurer une approche structurée, reproductible et alignée sur les objectifs métiers.

---

# 1️⃣ Introduction – Business Understanding (TDSP Phase 1)

La phase *Business Understanding* constitue l’étape fondamentale du TDSP.  
Elle définit :

- Le périmètre du projet QoS Buddy  
- Le problème métier réel  
- Les objectifs business mesurables  
- Leur traduction en objectifs data science  
- Les KPIs stratégiques  

---

## 1.1 Contexte et Problématique

Les réseaux télécom modernes doivent garantir une haute qualité de service pour :

- Voix
- Données mobiles
- Vidéo
- Services entreprise (B2B)

En pratique, des dégradations peuvent survenir rapidement :

- Congestion réseau
- Pannes radio
- Interférences
- Coupures fibre
- Saturation transport

### Observation opérationnelle clé

Il arrive fréquemment que **le client détecte la dégradation avant le NOC (Network Operations Center)**.

Conséquences :

- Augmentation des plaintes et tickets
- Risques de pénalités SLA (B2B)
- Temps de résolution plus long
- Investissements parfois mal ciblés (CAPEX/OPEX)

### Problème central

Comment améliorer durablement la qualité réseau en :

- Détectant plus tôt les dégradations  
- Réduisant le temps de résolution  
- Prévenant les violations SLA  
- Guidant objectivement les décisions d’investissement ?

---

## 1.2 Objectifs Business et Data Science

### 🎯 Objectifs Business (BO)

- **BO1** – Optimiser la qualité réseau avant impact client  
- **BO2** – Prévenir les violations SLA (notamment B2B)  
- **BO3** – Investir aux bons endroits (smart CAPEX)  
- **BO4** – Automatiser le reporting réseau  
- **BO5** – Accélérer la prise de décision via indicateurs data-driven  

---

### 🤖 Objectifs Data Science (ODS)

- **ODS1 (BO1)** – Détection d’anomalies QoS/QoE  
- **ODS2 (BO2)** – Prédiction du risque de violation SLA  
- **ODS3 (BO3)** – Scoring CAPEX & classement des zones  
- **ODS4 (BO4)** – Génération automatique de rapports  
- **ODS5 (BO5)** – Production d’indicateurs synthétiques pour décision rapide  

---

## 1.3 Objectifs de Développement Durable (SDGs)

Le projet s’aligne avec 3 SDGs majeurs :

- **SDG 9 – Industry, Innovation and Infrastructure**  
- **SDG 11 – Sustainable Cities and Communities**  
- **SDG 12 – Responsible Consumption and Production**  

QoS Buddy contribue à une infrastructure numérique plus fiable, durable et optimisée.

---

# 2️⃣ Méthodologie – TDSP

Le projet suit la méthodologie **Team Data Science Process (TDSP)**.

### Les 5 phases TDSP :

1. Business Understanding  
2. Data Acquisition & Understanding  
3. Modeling  
4. Deployment  
5. Customer Acceptance  

Cette approche garantit :

- Alignement business ↔ analytique  
- Reproductibilité  
- Traçabilité  
- Responsabilité  

---

# 3️⃣ Architecture Fonctionnelle

Le système est structuré en 3 blocs métiers :

### 🔹 BO1 – Anomaly Detection (4G)
Classification supervisée pour détecter les anomalies réseau avant impact client.

### 🔹 BO2 – SLA Early Warning (5G)
Prédiction multi-horizon (15/30/60 min) des violations SLA.

### 🔹 BO3 – CAPEX Scoring
Scoring des zones géographiques via Deep Learning (MLP, LSTM, TabNet, Autoencoder).

---

# 4️⃣ Tech Stack

## Backend / Data Science
- Python
- Scikit-learn
- LightGBM
- PyTorch
- TabNet
- SHAP

## Data & Visualisation
- Pandas
- NumPy
- Matplotlib
- Seaborn

---

# 5️⃣ Rôles et Responsabilités (TDSP Team)

- **Project Manager** — Idi Eya  
  Planification, gestion des risques, coordination et communication.

- **Project Lead** — Rabeh Mohamed  
  Supervision technique et qualité scientifique.

- **Solution Architects** — Azzabi Eya, Trabelsi Tassnim  
  Architecture technique complète (data flow, déploiement, sécurité).

- **Data Scientists** — Rachdi Eya, Omrani Doua  
  EDA, feature engineering, modélisation, évaluation et interprétabilité.

---

## Contributors
- QoS Buddy Team – 4DS8  


---

## Academic Context

Développé à **Esprit School of Engineering – Tunisie**  
PIDEV – 4DS8 | Année académique 2025–2026  

---

## Getting Started

### Installation 
pip install -r requirements.txt
### Exécution
Ouvrir les notebooks dans Jupyter Notebook ou Google Colab.

---

## Acknowledgments

Nous remercions le corps enseignant de **Esprit School of Engineering** pour l’encadrement académique et méthodologique.
