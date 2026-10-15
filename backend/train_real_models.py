"""
Train Real Models for QoS Buddy - WITH HYPERPARAMETER TUNING
Utilise GridSearchCV pour trouver la meilleure combinaison d'hyperparamètres
pour les modèles de Gradient Boosting (BO1 & BO2)
"""

import pandas as pd
import numpy as np
import joblib
import os
from pathlib import Path
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from lightgbm import LGBMClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.neural_network import MLPClassifier 
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("TRAINING & TUNING REAL MODELS ON UNIFIED DATASET")
print("="*70)

# 1. Charger les données préparées par le pipeline
train_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "train.csv"
df = pd.read_csv(train_path)
print(f"\n✅ Données chargées: {len(df)} lignes")

FEATURES = [
    'RSRP', 'SINR', 'PRB_UL', 'PRB_DL', 'throughput_DL', 'throughput_UL',
    'latency_ms', 'call_drop_rate', 'handover_success_rate', 'MOS',
    'BLER_UL', 'BLER_DL', 'CQI', 'RLC_retransmissions',
    'hour', 'is_weekend', 'is_busy_hour', 'signal_quality_score', 'PRB_avg',
    # --- NOUVELLES FEATURES TEMPORELLES ---
    'RSRP_lag1', 'RSRP_diff', 'RSRP_roll_std_3',
    'SINR_lag1', 'SINR_diff',
    'throughput_DL_diff', 'throughput_DL_roll_mean_3',
    'latency_ms_diff', 'latency_ms_roll_std_3',
    'PRB_DL_lag1', 'PRB_DL_diff'
]
FEATURES = [f for f in FEATURES if f in df.columns]
X = df[FEATURES].fillna(0)

scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)

models_dir = Path(__file__).resolve().parent.parent / "models"
os.makedirs(models_dir, exist_ok=True)


# -----------------------------------------------------------------
# BO1 : ANOMALY DETECTION (LightGBM + GridSearch)
# -----------------------------------------------------------------
print("\n" + "="*40)
print("[1/3] BO1 - ANOMALY DETECTOR (LightGBM Tuning)")
print("="*40)

if 'issue_type' in df.columns:
    y_bo1 = (df['issue_type'] != 'Normal').astype(int)
    X_tr, X_val, y_tr, y_val = train_test_split(X_scaled, y_bo1, test_size=0.2, random_state=42)
    
    # Définition de la grille d'hyperparamètres à tester
    param_grid_lgb = {
        'n_estimators': [100, 200],       # Nombre d'arbres
        'learning_rate': [0.05, 0.1],     # Vitesse d'apprentissage
        'num_leaves': [31, 50],           # Complexité de l'arbre
        'class_weight': ['balanced']       # Toujours équilibré pour les anomalies
    }
    
    print("🔍 Recherche des meilleurs hyperparamètres en cours... (peut prendre 1-2 min)")
    grid_bo1 = GridSearchCV(
        LGBMClassifier(random_state=53, verbose=-1), 
        param_grid_lgb, 
        cv=3,               # Validation croisée sur 3 parties
        scoring='roc_auc',  # On optimise pour le ROC-AUC
        n_jobs=-1           # Utilise tous les processeurs
    )
    
    grid_bo1.fit(X_tr, y_tr)
    
    print(f"\n🏆 Meilleurs paramètres trouvés pour BO1 : {grid_bo1.best_params_}")
    print(f"📊 Meilleur score CV (ROC-AUC) : {grid_bo1.best_score_:.4f}")
    
    # Évaluation finale sur le set de test (20% mis de côté)
    best_bo1 = grid_bo1.best_estimator_
    preds = best_bo1.predict(X_val)
    proba = best_bo1.predict_proba(X_val)[:, 1]
    print(f"🧪 ROC-AUC sur le jeu de test caché : {roc_auc_score(y_val, proba):.4f}")
    print(classification_report(y_val, preds, target_names=['Normal', 'Anomalie']))
    
    joblib.dump(best_bo1, models_dir / 'anomaly_detector.pkl')
    print("✅ Modèle BO1 optimisé sauvegardé !")

else:
    print("❌ Colonne 'issue_type' introuvable")


# -----------------------------------------------------------------
# BO2 : SLA EARLY WARNING (HistGradientBoosting + SMOTE + GridSearch)
# -----------------------------------------------------------------
print("\n" + "="*40)
print("[2/3] BO2 - SLA PREDICTOR (HistGradient Tuning)")
print("="*40)

if 'severity' in df.columns:
    from imblearn.over_sampling import SMOTE # AJOUTE SMOTE ICI

    y_bo2 = df['severity'].isin(['CRITICAL', 'HIGH']).astype(int)
    X_tr, X_val, y_tr, y_val = train_test_split(X_scaled, y_bo2, test_size=0.2, random_state=42)
    
    # NOUVEAU : On équilibre les données d'entraînement avec SMOTE
    print("⚖️ Application de SMOTE pour forcer le modèle à apprendre les violations SLA...")
    smote = SMOTE(random_state=42)
    X_tr_smote, y_tr_smote = smote.fit_resample(X_tr, y_tr)
    
    param_grid_hgb = {
        'max_iter': [200, 300],
        'learning_rate': [0.05, 0.1],
        'max_depth': [5, 6, 8],
        'min_samples_leaf': [20, 50]
    }
    
    print("🔍 Recherche des meilleurs hyperparamètres en cours... (peut prendre 1-2 min)")
    grid_bo2 = GridSearchCV(
        HistGradientBoostingClassifier(random_state=42), 
        param_grid_hgb, 
        cv=3, 
        scoring='roc_auc', 
        n_jobs=-1
    )
    
    # CHANGEMENT ICI : on entraîne sur les données SMOTEées (X_tr_smote)
    grid_bo2.fit(X_tr_smote, y_tr_smote)
    
    print(f"\n🏆 Meilleurs paramètres trouvés pour BO2 : {grid_bo2.best_params_}")
    print(f"📊 Meilleur score CV (ROC-AUC) : {grid_bo2.best_score_:.4f}")
    
    best_bo2 = grid_bo2.best_estimator_
    preds = best_bo2.predict(X_val)
    proba = best_bo2.predict_proba(X_val)[:, 1]
    print(f"🧪 ROC-AUC sur le jeu de test caché : {roc_auc_score(y_val, proba):.4f}")
    print(classification_report(y_val, preds, target_names=['OK', 'Violation SLA']))
    
    joblib.dump(best_bo2, models_dir / 'sla_predictor.pkl')
    print("✅ Modèle BO2 optimisé avec SMOTE sauvegardé !")

else:
    print("❌ Colonne 'severity' introuvable")


# -----------------------------------------------------------------
# BO3 : ZONE SCORING CAPEX (MLP Classifier avec Early Stopping)
# -----------------------------------------------------------------
print("\n" + "="*40)
print("[3/3] BO3 - ZONE SCORER (MLP Network)")
print("="*40)

if 'severity' in df.columns:
    y_bo3 = df['severity'].isin(['CRITICAL']).astype(int)
    X_tr, X_val, y_tr, y_val = train_test_split(X_scaled, y_bo3, test_size=0.2, random_state=42)
    
    # Pas de GridSearch pour le MLP ici, on utilise l'Early Stopping intégré
    model_bo3 = MLPClassifier(
        hidden_layer_sizes=(256, 128, 64), 
        activation='relu', 
        solver='adam', 
        max_iter=150, 
        random_state=42,
        early_stopping=True, # Le modèle s'arrête tout seul quand il commence à faire de l'overfitting
        validation_fraction=0.1 
    )
    model_bo3.fit(X_tr, y_tr)
    
    preds = model_bo3.predict(X_val)
    proba = model_bo3.predict_proba(X_val)[:, 1]
    print(f"🧪 ROC-AUC sur le jeu de test caché : {roc_auc_score(y_val, proba):.4f}")
    print(classification_report(y_val, preds, target_names=['Normal', 'Urgent CAPEX']))
    
    joblib.dump(model_bo3, models_dir / 'zone_scorer.pkl')
    print("✅ Modèle BO3 sauvegardé !")

else:
    print("❌ Colonne 'severity' introuvable")


# -----------------------------------------------------------------
# Sauvegarder le scaler et la liste des features
# -----------------------------------------------------------------
joblib.dump(scaler, models_dir / 'scaler.pkl')
joblib.dump(FEATURES, models_dir / 'features.pkl')

print("\n" + "="*70)
print("✅ TOUS LES MODÈLES SONT OPTIMISÉS ET PRÊTS !")
print("="*70)
print("Tu peux maintenant lancer 'python main.py'\n")


# Sauvegarder les métriques pour le dashboard
import json

metrics = {
    "bo1": {
        "model": "LightGBM",
        "roc_auc": round(roc_auc_score(y_val, best_bo1.predict_proba(X_val)[:, 1]), 4),
        "params": str(grid_bo1.best_params_)
    },
    "bo2": {
        "model": "HistGradientBoosting + SMOTE",
        "roc_auc": round(roc_auc_score(y_val, best_bo2.predict_proba(X_val)[:, 1]), 4),
        "params": str(grid_bo2.best_params_)
    },
    "bo3": {
        "model": "MLP Neural Network",
        "roc_auc": round(roc_auc_score(y_val, model_bo3.predict_proba(X_val)[:, 1]), 4)
    }
}

metrics_path = models_dir / 'metrics.json'
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print("✅ Métriques sauvegardées pour le dashboard !")