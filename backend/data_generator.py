"""
Synthetic Telecom Network KPI Data Generator
Generates realistic network performance data covering 7 problem scenarios
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

np.random.seed(42)
random.seed(42)

class TelecomDataGenerator:
    def __init__(self, num_samples=10000):
        self.num_samples = num_samples
        self.cell_ids = [f"Cell_{i:03d}" for i in range(1, 51)]
        self.start_date = datetime(2026, 1, 1)
        # Optional real dataset to transform into the generator schema
        self.filled_data_path = Path(__file__).resolve().parent / "unified_telecom_dataset_FILLED.csv"
        
    def generate_timestamp(self, idx):
        """Generate timestamps with 15-minute intervals, ending at current time"""
        # End at current time for recent data visibility
        end_date = datetime.now()
        total_duration = timedelta(minutes=idx * 15)
        start_date = end_date - timedelta(minutes=(self.num_samples - 1) * 15)
        return start_date + timedelta(minutes=idx * 15)
    
    def get_hour_of_day(self, timestamp):
        """Extract hour for busy hour detection"""
        return timestamp.hour
    
    def generate_normal_record(self, timestamp, cell_id):
        """Generate normal network performance"""
        hour = self.get_hour_of_day(timestamp)
        
        # Normal baseline with some variation
        rsrp = np.random.uniform(-90, -70)
        sinr = np.random.uniform(15, 25)
        prb_ul = np.random.uniform(25, 45)
        prb_dl = np.random.uniform(30, 50)
        throughput_dl = np.random.uniform(50, 150)
        throughput_ul = np.random.uniform(10, 30)
        latency = np.random.uniform(10, 30)
        call_drop_rate = np.random.uniform(0, 0.8)
        ho_success_rate = np.random.uniform(95, 99.5)
        mos = np.random.uniform(3.8, 4.5)
        bler_ul = np.random.uniform(0.5, 2)
        bler_dl = np.random.uniform(0.5, 2)
        cqi = np.random.uniform(12, 15)
        rlc_retrans = np.random.uniform(0.5, 2)
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'Normal',
            'severity': 'NONE'
        }
    
    def generate_call_drop(self, timestamp, cell_id):
        """Scenario 1: Call Drop / Call Fail"""
        hour = self.get_hour_of_day(timestamp)
        
        rsrp = np.random.uniform(-120, -110)
        sinr = np.random.uniform(0, 5)
        prb_ul = np.random.uniform(40, 70)
        prb_dl = np.random.uniform(45, 75)
        throughput_dl = np.random.uniform(5, 20)
        throughput_ul = np.random.uniform(1, 5)
        latency = np.random.uniform(50, 150)
        call_drop_rate = np.random.uniform(5, 15)
        ho_success_rate = np.random.uniform(70, 84)
        mos = np.random.uniform(1.5, 2.5)
        bler_ul = np.random.uniform(5, 15)
        bler_dl = np.random.uniform(5, 15)
        cqi = np.random.uniform(3, 7)
        rlc_retrans = np.random.uniform(5, 15)
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'Call Drop',
            'severity': 'HIGH'
        }
    
    def generate_low_mos(self, timestamp, cell_id):
        """Scenario 2: Low Voice Quality (MOS faible)"""
        hour = self.get_hour_of_day(timestamp)
        
        rsrp = np.random.uniform(-105, -95)
        sinr = np.random.uniform(5, 10)
        prb_ul = np.random.uniform(75, 95)
        prb_dl = np.random.uniform(80, 95)
        throughput_dl = np.random.uniform(15, 40)
        throughput_ul = np.random.uniform(3, 10)
        latency = np.random.uniform(40, 80)
        call_drop_rate = np.random.uniform(2, 5)
        ho_success_rate = np.random.uniform(85, 92)
        mos = np.random.uniform(1.8, 2.8)
        bler_ul = np.random.uniform(8, 20)
        bler_dl = np.random.uniform(8, 20)
        cqi = np.random.uniform(5, 9)
        rlc_retrans = np.random.uniform(3, 8)
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'Low MOS',
            'severity': 'MEDIUM'
        }
    
    def generate_low_throughput(self, timestamp, cell_id):
        """Scenario 3: Low Throughput"""
        hour = self.get_hour_of_day(timestamp)
        
        rsrp = np.random.uniform(-100, -85)
        sinr = np.random.uniform(3, 9)
        prb_ul = np.random.uniform(70, 85)
        prb_dl = np.random.uniform(75, 90)
        throughput_dl = np.random.uniform(5, 25)
        throughput_ul = np.random.uniform(1, 8)
        latency = np.random.uniform(35, 70)
        call_drop_rate = np.random.uniform(1, 3)
        ho_success_rate = np.random.uniform(88, 95)
        mos = np.random.uniform(2.5, 3.5)
        bler_ul = np.random.uniform(3, 8)
        bler_dl = np.random.uniform(3, 8)
        cqi = np.random.uniform(4, 8)
        rlc_retrans = np.random.uniform(2, 6)
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'Low Throughput',
            'severity': 'MEDIUM'
        }
    
    def generate_high_latency(self, timestamp, cell_id):
        """Scenario 4: High Latency"""
        hour = self.get_hour_of_day(timestamp)
        
        rsrp = np.random.uniform(-95, -75)
        sinr = np.random.uniform(10, 18)
        prb_ul = np.random.uniform(50, 75)
        prb_dl = np.random.uniform(55, 80)
        throughput_dl = np.random.uniform(30, 60)
        throughput_ul = np.random.uniform(5, 15)
        latency = np.random.uniform(80, 200)
        call_drop_rate = np.random.uniform(0.5, 2)
        ho_success_rate = np.random.uniform(90, 96)
        mos = np.random.uniform(2.8, 3.5)
        bler_ul = np.random.uniform(2, 5)
        bler_dl = np.random.uniform(2, 5)
        cqi = np.random.uniform(8, 12)
        rlc_retrans = np.random.uniform(10, 25)
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'High Latency',
            'severity': 'MEDIUM'
        }
    
    def generate_session_drop(self, timestamp, cell_id):
        """Scenario 5: Session Data Drop"""
        hour = self.get_hour_of_day(timestamp)
        
        rsrp = np.random.uniform(-118, -110)
        sinr = np.random.uniform(2, 8)
        prb_ul = np.random.uniform(45, 70)
        prb_dl = np.random.uniform(50, 75)
        throughput_dl = np.random.uniform(8, 25)
        throughput_ul = np.random.uniform(2, 8)
        latency = np.random.uniform(45, 100)
        call_drop_rate = np.random.uniform(3, 8)
        ho_success_rate = np.random.uniform(75, 87)
        mos = np.random.uniform(2.0, 3.0)
        bler_ul = np.random.uniform(4, 10)
        bler_dl = np.random.uniform(4, 10)
        cqi = np.random.uniform(4, 8)
        rlc_retrans = np.random.uniform(4, 10)
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'Session Drop',
            'severity': 'HIGH'
        }
    
    def generate_handover_failure(self, timestamp, cell_id):
        """Scenario 6: Handover Failure"""
        hour = self.get_hour_of_day(timestamp)
        
        rsrp = np.random.uniform(-98, -80)
        sinr = np.random.uniform(8, 15)
        prb_ul = np.random.uniform(35, 60)
        prb_dl = np.random.uniform(40, 65)
        throughput_dl = np.random.uniform(25, 55)
        throughput_ul = np.random.uniform(5, 15)
        latency = np.random.uniform(30, 60)
        call_drop_rate = np.random.uniform(2, 6)
        ho_success_rate = np.random.uniform(65, 80)
        mos = np.random.uniform(2.5, 3.5)
        bler_ul = np.random.uniform(2, 6)
        bler_dl = np.random.uniform(2, 6)
        cqi = np.random.uniform(7, 11)
        rlc_retrans = np.random.uniform(3, 7)
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'Handover Failure',
            'severity': 'HIGH'
        }
    
    def generate_capacity_issue(self, timestamp, cell_id):
        """Scenario 7: Capacity Problem (busy hour)"""
        hour = self.get_hour_of_day(timestamp)
        
        # Capacity issues more severe during busy hours
        if hour in [17, 18, 19, 20, 21]:
            prb_severity = 1.2
        else:
            prb_severity = 1.0
        
        rsrp = np.random.uniform(-90, -75)
        sinr = np.random.uniform(10, 18)
        prb_ul = np.random.uniform(85, 98) * prb_severity
        prb_dl = np.random.uniform(87, 99) * prb_severity
        prb_ul = min(prb_ul, 100)
        prb_dl = min(prb_dl, 100)
        throughput_dl = np.random.uniform(10, 30)
        throughput_ul = np.random.uniform(2, 8)
        latency = np.random.uniform(40, 90)
        call_drop_rate = np.random.uniform(1.5, 4)
        ho_success_rate = np.random.uniform(85, 92)
        mos = np.random.uniform(2.5, 3.5)
        bler_ul = np.random.uniform(3, 8)
        bler_dl = np.random.uniform(3, 8)
        cqi = np.random.uniform(6, 10)
        rlc_retrans = np.random.uniform(3, 8)
        
        severity = 'CRITICAL' if hour in [17, 18, 19, 20, 21] else 'HIGH'
        
        return {
            'timestamp': timestamp,
            'cell_id': cell_id,
            'RSRP': rsrp,
            'SINR': sinr,
            'PRB_UL': prb_ul,
            'PRB_DL': prb_dl,
            'throughput_DL': throughput_dl,
            'throughput_UL': throughput_ul,
            'latency_ms': latency,
            'call_drop_rate': call_drop_rate,
            'handover_success_rate': ho_success_rate,
            'MOS': mos,
            'BLER_UL': bler_ul,
            'BLER_DL': bler_dl,
            'CQI': cqi,
            'RLC_retransmissions': rlc_retrans,
            'hour': hour,
            'issue_type': 'Capacity Problem',
            'severity': severity
        }
    
    def load_and_transform_filled_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform `unified_telecom_dataset_FILLED.csv` into the schema used by the rest of the app.
        """
        df = df.copy()
        
        # Timestamp + IDs
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        if 'cell_id' not in df.columns and 'entity_id' in df.columns:
            df['cell_id'] = df['entity_id']
        
        # Core KPIs (rename to generator schema)
        if 'RSRP_dBm' in df.columns:
            df['RSRP'] = pd.to_numeric(df['RSRP_dBm'], errors='coerce')
        elif 'signal_strength_dbm' in df.columns:
            df['RSRP'] = pd.to_numeric(df['signal_strength_dbm'], errors='coerce')
        else:
            df['RSRP'] = pd.NA
        
        if 'SINR_dB' in df.columns:
            df['SINR'] = pd.to_numeric(df['SINR_dB'], errors='coerce')
        else:
            df['SINR'] = pd.NA
        
        df['PRB_UL'] = pd.to_numeric(df.get('PRBUsageUL', pd.NA), errors='coerce')
        df['PRB_DL'] = pd.to_numeric(df.get('PRBUsageDL', pd.NA), errors='coerce')
        df['throughput_DL'] = pd.to_numeric(df.get('meanThr_DL', pd.NA), errors='coerce')
        df['throughput_UL'] = pd.to_numeric(df.get('meanThr_UL', pd.NA), errors='coerce')
        
        df['latency_ms'] = pd.to_numeric(df.get('latency_ms', pd.NA), errors='coerce')
        
        # Voice/data impairment proxies
        df['MOS'] = pd.to_numeric(df.get('sla_breach_risk', pd.NA), errors='coerce')
        # SLA breach risk is in [0, 1] -> MOS in [5, 1]
        df['MOS'] = (5 - 4 * df['MOS']).clip(1.0, 5.0)
        
        # Error/quality proxies
        df['BLER_DL'] = pd.to_numeric(df.get('error_rate', pd.NA), errors='coerce') * 5.0
        df['BLER_UL'] = pd.to_numeric(df.get('error_rate', pd.NA), errors='coerce') * 4.5
        df['BLER_DL'] = df['BLER_DL'].clip(0.5, 20.0)
        df['BLER_UL'] = df['BLER_UL'].clip(0.5, 20.0)
        
        df['CQI'] = pd.to_numeric(df.get('CQI', pd.NA), errors='coerce')
        df['RLC_retransmissions'] = pd.to_numeric(df.get('RLC_RetxRate_pct', pd.NA), errors='coerce')
        
        # Call/session/HO KPIs
        df['call_drop_rate'] = pd.to_numeric(df.get('ERAB_DropRate_pct', pd.NA), errors='coerce')
        df['handover_success_rate'] = pd.to_numeric(df.get('HO_SuccessRate_pct', pd.NA), errors='coerce')
        
        # Housekeeping
        df['hour'] = df['timestamp'].dt.hour
        
        # Assign issue_type + severity (heuristic mapping)
        risk_tier = df.get('risk_tier', pd.Series(index=df.index, data='LOW'))
        unified_risk_score = pd.to_numeric(df.get('unified_risk_score', pd.NA), errors='coerce').fillna(0)
        anomaly_flag = pd.to_numeric(df.get('anomaly_flag', 0), errors='coerce').fillna(0)
        
        is_normal = (anomaly_flag == 0) & (risk_tier == 'LOW')
        
        is_capacity = (df['PRB_DL'] >= 85) | (df['PRB_UL'] >= 85)
        is_high_latency = df['latency_ms'] >= 110
        is_call_drop = df['call_drop_rate'] >= 7
        is_handover_failure = df['handover_success_rate'] <= 80
        is_low_throughput = df['throughput_DL'] <= 12
        is_low_mos = df['MOS'] <= 2.5
        is_session_drop = (pd.to_numeric(df.get('packet_loss_rate', pd.NA), errors='coerce') >= 2.5) | (
            pd.to_numeric(df.get('jitter_ms', pd.NA), errors='coerce') >= 20
        )
        
        conditions = [
            (~is_normal) & is_capacity,
            (~is_normal) & is_high_latency,
            (~is_normal) & is_call_drop,
            (~is_normal) & is_handover_failure,
            (~is_normal) & is_low_throughput,
            (~is_normal) & is_low_mos,
            (~is_normal) & is_session_drop,
        ]
        choices = [
            'Capacity Problem',
            'High Latency',
            'Call Drop',
            'Handover Failure',
            'Low Throughput',
            'Low MOS',
            'Session Drop',
        ]
        df['issue_type'] = np.select(conditions, choices, default='Normal')
        
        df['severity'] = 'NONE'
        df.loc[risk_tier == 'CRITICAL', 'severity'] = 'CRITICAL'
        df.loc[risk_tier == 'MEDIUM', 'severity'] = 'MEDIUM'
        # Split MEDIUM into MEDIUM vs HIGH using unified score threshold
        df.loc[(risk_tier == 'MEDIUM') & (unified_risk_score >= 40), 'severity'] = 'HIGH'
        df.loc[df['issue_type'] == 'Normal', 'severity'] = 'NONE'
        
        # Keep only columns used downstream (plus a few common raw fields)
        keep_cols = [
            'timestamp', 'cell_id',
            'RSRP', 'SINR',
            'PRB_UL', 'PRB_DL',
            'throughput_DL', 'throughput_UL',
            'latency_ms', 'MOS',
            'call_drop_rate', 'handover_success_rate',
            'BLER_UL', 'BLER_DL',
            'CQI', 'RLC_retransmissions',
            'hour', 'issue_type', 'severity',
        ]
        keep_cols = [c for c in keep_cols if c in df.columns]
        df = df[keep_cols]
        
        # Sort + keep latest records if requested
        df = df.sort_values('timestamp').reset_index(drop=True)
        if self.num_samples and len(df) > self.num_samples:
            df = df.tail(self.num_samples).reset_index(drop=True)
        
        return df
    
    def generate_dataset(self):
        """Generate complete dataset with all scenarios"""
        # Prefer transforming the provided FILLED dataset if it exists.
        if self.filled_data_path.exists():
            print(f"Using filled dataset as source: {self.filled_data_path}")
            df_raw = pd.read_csv(self.filled_data_path)
            return self.load_and_transform_filled_dataset(df_raw)
        
        # Fallback: generate synthetic data if FILLED dataset is missing.
        # Distribution of scenarios (40% normal, 60% issues - for demo visibility)
        scenario_weights = {
            'normal': 0.40,
            'call_drop': 0.12,
            'low_mos': 0.10,
            'low_throughput': 0.10,
            'high_latency': 0.12,
            'session_drop': 0.08,
            'handover_failure': 0.06,
            'capacity': 0.02
        }
        
        scenarios = list(scenario_weights.keys())
        weights = list(scenario_weights.values())
        
        data = []
        
        for idx in range(self.num_samples):
            timestamp = self.generate_timestamp(idx)
            cell_id = random.choice(self.cell_ids)
            scenario = random.choices(scenarios, weights=weights)[0]
            
            if scenario == 'normal':
                record = self.generate_normal_record(timestamp, cell_id)
            elif scenario == 'call_drop':
                record = self.generate_call_drop(timestamp, cell_id)
            elif scenario == 'low_mos':
                record = self.generate_low_mos(timestamp, cell_id)
            elif scenario == 'low_throughput':
                record = self.generate_low_throughput(timestamp, cell_id)
            elif scenario == 'high_latency':
                record = self.generate_high_latency(timestamp, cell_id)
            elif scenario == 'session_drop':
                record = self.generate_session_drop(timestamp, cell_id)
            elif scenario == 'handover_failure':
                record = self.generate_handover_failure(timestamp, cell_id)
            elif scenario == 'capacity':
                record = self.generate_capacity_issue(timestamp, cell_id)
            
            data.append(record)
        
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    def generate_summary_stats(self, df):
        """Generate summary statistics"""
        print("\n" + "="*60)
        print("SYNTHETIC TELECOM DATASET GENERATION COMPLETE")
        print("="*60)
        print(f"\nTotal Records: {len(df):,}")
        print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Number of Cells: {df['cell_id'].nunique()}")
        print(f"\nIssue Type Distribution:")
        print(df['issue_type'].value_counts())
        print(f"\nSeverity Distribution:")
        print(df['severity'].value_counts())
        
        print(f"\nKPI Ranges:")
        print(f"  RSRP: {df['RSRP'].min():.1f} to {df['RSRP'].max():.1f} dBm")
        print(f"  SINR: {df['SINR'].min():.1f} to {df['SINR'].max():.1f} dB")
        print(f"  PRB_DL: {df['PRB_DL'].min():.1f}% to {df['PRB_DL'].max():.1f}%")
        print(f"  Throughput DL: {df['throughput_DL'].min():.1f} to {df['throughput_DL'].max():.1f} Mbps")
        print(f"  MOS: {df['MOS'].min():.1f} to {df['MOS'].max():.1f}")
        print(f"  Latency: {df['latency_ms'].min():.1f} to {df['latency_ms'].max():.1f} ms")
        print("="*60 + "\n")


if __name__ == "__main__":
    print("Starting Telecom KPI Data Generation (filled dataset if available)...")
    
    generator = TelecomDataGenerator(num_samples=20000)
    df = generator.generate_dataset()
    
    # Save to CSV
    output_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "network_kpis_synthetic.csv"
    df.to_csv(output_path, index=False)
    print(f"Dataset saved to: {output_path}")
    
    # Generate summary
    generator.generate_summary_stats(df)
    
    # Save sample for inspection
    sample_path = output_dir / "sample_records.csv"
    df.sample(100).to_csv(sample_path, index=False)
    print(f"Sample (100 records) saved to: {sample_path}")
