"""
Data Pipeline for QoS Buddy
Transforms the unified FILLED dataset, cleans, normalizes, and prepares for ML models
"""

import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
import os
import warnings
from pathlib import Path

from core.filled_transform import apply_filled_column_mapping, finalize_pipeline_dataframe

warnings.filterwarnings('ignore')

class TelecomDataPipeline:
    def __init__(self):
        self.scaler = RobustScaler()
        self.filled_data_path = Path(__file__).resolve().parent / "unified_telecom_dataset_FILLED.csv"
        self.numerical_features = [
            'RSRP', 'SINR', 'PRB_UL', 'PRB_DL', 'throughput_DL', 'throughput_UL',
            'latency_ms', 'call_drop_rate', 'handover_success_rate', 'MOS',
            'BLER_UL', 'BLER_DL', 'CQI', 'RLC_retransmissions'
        ]

    def load_filled_data(self, path: str | Path | None = None):
        """Load the unified FILLED dataset."""
        try:
            data_path = Path(path) if path is not None else self.filled_data_path
            df = pd.read_csv(str(data_path))
            df['data_source'] = 'filled'
            print(f"[OK] Loaded filled data: {len(df)} records from {data_path}")
            return df
        except FileNotFoundError:
            print(f"⚠ Filled dataset not found at {path or self.filled_data_path}")
            return None
    
    def load_synthetic_data(self, path='../data/synthetic/network_kpis_synthetic.csv'):
        """Load synthetic dataset"""
        try:
            df = pd.read_csv(path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['data_source'] = 'synthetic'
            print(f"[OK] Loaded synthetic data: {len(df)} records")
            return df
        except FileNotFoundError:
            print(f"⚠ Synthetic data not found at {path}")
            return None
    
    def load_real_data(self, path='../data/raw/'):
        """Load real datasets from Kaggle or other sources"""
        real_dfs = []
        
        if not os.path.exists(path):
            print(f"[WARN] Real data directory not found: {path}")
            return None
        
        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
        
        if not csv_files:
            print(f"[WARN] No CSV files found in {path}")
            return None
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(os.path.join(path, csv_file))
                df['data_source'] = 'real'
                real_dfs.append(df)
                print(f"[OK] Loaded real data: {csv_file} ({len(df)} records)")
            except Exception as e:
                print(f"[ERROR] Error loading {csv_file}: {e}")
        
        if real_dfs:
            return pd.concat(real_dfs, ignore_index=True)
        return None
    
    def standardize_columns(self, df):
        """Standardize column names across datasets"""
        column_mapping = {
            'rsrp': 'RSRP',
            'RCRP': 'RSRP',
            'rcrp': 'RSRP',
            'sinr': 'SINR',
            'prb_ul': 'PRB_UL',
            'prb_dl': 'PRB_DL',
            'PRBUsageUL': 'PRB_UL',
            'PRBUsageDL': 'PRB_DL',
            'meanThr_DL': 'throughput_DL',
            'meanThr_UL': 'throughput_UL',
            'Latency': 'latency_ms',
            'mos': 'MOS',
            'bler_ul': 'BLER_UL',
            'bler_dl': 'BLER_DL',
            'cqi': 'CQI',
        }
        
        df = df.rename(columns=column_mapping)
        return df

    def transform_filled_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform FILLED CSV into pipeline KPI schema (shared core.filled_transform)."""
        df = apply_filled_column_mapping(df)
        return finalize_pipeline_dataframe(df)
    
    def handle_missing_values(self, df):
        """Handle missing values intelligently"""
        print("\nHandling missing values...")
        
        for col in self.numerical_features:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    if missing_count / len(df) > 0.3:
                        median_val = df[col].median()
                        df[col].fillna(median_val, inplace=True)
                        print(f"  {col}: {missing_count} missing → filled with median ({median_val:.2f})")
                    else:
                        df[col].fillna(df[col].ffill(), inplace=True)
                        print(f"  {col}: {missing_count} missing → forward filled")
        
        return df
    
    def add_derived_features(self, df):
        """Add engineered features with temporal dynamics (Lags & Rolling)"""
        print("\nAdding derived features...")
        
        # 1. Features temporelles de base
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            df['is_busy_hour'] = df['hour'].isin([17, 18, 19, 20, 21]).astype(int)
        
        # 2. Features de qualité globale
        if 'RSRP' in df.columns and 'SINR' in df.columns:
            df['signal_quality_score'] = (
                (df['RSRP'] + 120) / 50 +
                (df['SINR'] / 25)
            ) / 2
        
        if 'PRB_DL' in df.columns and 'PRB_UL' in df.columns:
            df['PRB_avg'] = (df['PRB_DL'] + df['PRB_UL']) / 2
            df['PRB_max'] = df[['PRB_DL', 'PRB_UL']].max(axis=1)
        
        if 'BLER_UL' in df.columns and 'BLER_DL' in df.columns:
            df['BLER_avg'] = (df['BLER_UL'] + df['BLER_DL']) / 2

        # ==========================================
        # 3. NOUVEAU : Features Temporelles Avancées
        # ==========================================
        print("  Adding temporal lags and rolling windows...")
        
        # S'assurer que les données sont triées par cellule puis par temps
        df = df.sort_values(['cell_id', 'timestamp'])
        
        # Les KPIs les plus importants à analyser dans le temps
        kpis_to_track = ['RSRP', 'SINR', 'throughput_DL', 'latency_ms', 'PRB_DL', 'call_drop_rate']
        kpis_to_track = [k for k in kpis_to_track if k in df.columns]
        
        for kpi in kpis_to_track:
            group = df.groupby('cell_id')[kpi]
            
            # LAGS : La valeur d'il y a 1 et 2 pas de temps
            df[f'{kpi}_lag1'] = group.shift(1)
            df[f'{kpi}_lag2'] = group.shift(2)
            
            # DIFFERENCE (Dérivée) : La vitesse de changement (Actuel - Précédent)
            df[f'{kpi}_diff'] = df[kpi] - df[f'{kpi}_lag1']
            
            # ROLLING MEAN : La moyenne sur les 3 dernières mesures
            df[f'{kpi}_roll_mean_3'] = group.transform(
                lambda x: x.rolling(window=3, min_periods=1).mean()
            )
            
            # ROLLING STD : La volatilité sur les 3 dernières mesures
            df[f'{kpi}_roll_std_3'] = group.transform(
                lambda x: x.rolling(window=3, min_periods=1).std()
            ).fillna(0)
        
        print(f"  Added: hour, day_of_week, signal_quality_score, PRB_avg, + 24 temporal features")
        
        return df

    def detect_outliers(self, df):
        print("\nDetecting outliers...")
        
        for col in self.numerical_features:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                
                outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
                if outliers > 0:
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                    print(f"  {col}: {outliers} outliers clipped")
        
        return df
    
    def merge_datasets(self, synthetic_df, real_df=None):
        """Merge synthetic and real datasets"""
        if real_df is None:
            print("\nUsing synthetic data only")
            return synthetic_df
        
        print("\nMerging datasets...")
        
        synthetic_df = self.standardize_columns(synthetic_df)
        real_df = self.standardize_columns(real_df)
        
        common_cols = list(set(synthetic_df.columns) & set(real_df.columns))
        synthetic_subset = synthetic_df[common_cols]
        real_subset = real_df[common_cols]
        
        merged = pd.concat([synthetic_subset, real_subset], ignore_index=True)
        print(f"  Merged dataset: {len(merged)} total records")
        print(f"    - Synthetic: {len(synthetic_df)} records")
        print(f"    - Real: {len(real_df)} records")
        
        return merged
    
    def prepare_for_modeling(self, df):
        """Prepare dataset for ML models"""
        print("\nPreparing for modeling...")
        
        df = self.handle_missing_values(df)
        df = self.add_derived_features(df)
        df = self.detect_outliers(df)
        
        df_clean = df.copy()
        
        print(f"\n✓ Final dataset shape: {df_clean.shape}")
        
        return df_clean
    
    def split_and_save(self, df, test_size=0.2, output_dir='../data/processed/'):
        """Split into train/validation and save"""
        print(f"\nSplitting dataset (test_size={test_size})...")
        
        if 'issue_type' in df.columns:
            has_issues = df[df['issue_type'] != 'Normal']
            normal = df[df['issue_type'] == 'Normal']
            
            train_issues, val_issues = train_test_split(
                has_issues, test_size=test_size, stratify=None, random_state=42
            )
            train_normal, val_normal = train_test_split(
                normal, test_size=test_size, random_state=42
            )
            
            train_df = pd.concat([train_issues, train_normal], ignore_index=True)
            val_df = pd.concat([val_issues, val_normal], ignore_index=True)
        else:
            train_df, val_df = train_test_split(df, test_size=test_size, random_state=42)
        
        train_df = train_df.sort_values('timestamp').reset_index(drop=True)
        val_df = val_df.sort_values('timestamp').reset_index(drop=True)
        
        os.makedirs(output_dir, exist_ok=True)
        
        train_path = os.path.join(output_dir, 'train.csv')
        val_path = os.path.join(output_dir, 'validation.csv')
        full_path = os.path.join(output_dir, 'network_kpis_full.csv')
        
        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        df.to_csv(full_path, index=False)
        
        print(f"  [OK] Training set: {len(train_df)} records -> {train_path}")
        print(f"  [OK] Validation set: {len(val_df)} records -> {val_path}")
        print(f"  [OK] Full dataset: {len(df)} records -> {full_path}")
        
        return train_df, val_df


def run_pipeline():
    """Execute complete data pipeline"""
    print("="*70)
    print("QoS BUDDY - DATA PIPELINE")
    print("="*70)
    
    pipeline = TelecomDataPipeline()

    # Option: use FILLED dataset only (no synthetic generator dependency).
    filled_df = pipeline.load_filled_data()
    if filled_df is None:
        print("\n[ERROR] No data available: unified_telecom_dataset_FILLED.csv not found.")
        return

    transformed_df = pipeline.transform_filled_dataset(filled_df)
    clean_df = pipeline.prepare_for_modeling(transformed_df)
    
    train_df, val_df = pipeline.split_and_save(clean_df)
    
    print("\n" + "="*70)
    print("PIPELINE COMPLETE!")
    print("="*70)
    print("\nDataset Statistics:")
    print(f"  Total records: {len(clean_df):,}")
    print(f"  Features: {len(clean_df.columns)}")
    print(f"  Date range: {clean_df['timestamp'].min()} to {clean_df['timestamp'].max()}")
    print(f"  Cells monitored: {clean_df['cell_id'].nunique()}")
    
    if 'issue_type' in clean_df.columns:
        print("\n  Issue Distribution:")
        for issue, count in clean_df['issue_type'].value_counts().items():
            pct = (count / len(clean_df)) * 100
            print(f"    - {issue}: {count:,} ({pct:.1f}%)")
    
    print("\n[OK] Ready for Agent 2 (Diagnostic Worker) and Model Training")


if __name__ == "__main__":
    run_pipeline()
