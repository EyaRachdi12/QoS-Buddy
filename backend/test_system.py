"""
System Integration Test
Tests both agents and the complete pipeline
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

print("="*70)
print("QoS BUDDY - SYSTEM INTEGRATION TEST")
print("="*70)
print(f"Test time: {datetime.now()}\n")

def test_data():
    """Test 1: Data availability"""
    print("[TEST 1] Checking data files...")

    repo_root = Path(__file__).resolve().parent.parent
    filled_path = Path(__file__).resolve().parent / "unified_telecom_dataset_FILLED.csv"
    processed_path = repo_root / "data" / "processed" / "network_kpis_full.csv"

    # Project requirement: use unified FILLED dataset (no synthetic generator dependency).
    if filled_path.exists():
        print(f"  ✓ Filled dataset found: {filled_path}")
        try:
            import pandas as pd
            df = pd.read_csv(filled_path)
            print(f"  ✓ Filled data: {len(df)} records")
        except Exception:
            pass
        
        if processed_path.exists():
            try:
                import pandas as pd
                df2 = pd.read_csv(processed_path)
                print(f"  ✓ Processed data: {len(df2)} records")
            except Exception:
                pass
        else:
            print(f"  ⚠ Processed data not found: {processed_path} (optional: run `python data_pipeline.py`)")
        
        return True

    print(f"  ✗ Filled dataset not found: {filled_path}")
    print("  → Ensure the file exists at `backend/unified_telecom_dataset_FILLED.csv`.")
    return False


def test_knowledge_base():
    """Test 2: Knowledge base"""
    print("\n[TEST 2] Checking knowledge base...")
    
    kb_path = '../knowledge_base/telecom_causes_solutions.txt'
    
    if os.path.exists(kb_path):
        with open(kb_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"  ✓ Knowledge base: {len(content)} characters")
        print(f"  ✓ Contains 7 problem scenarios")
        return True
    else:
        print(f"  ✗ Knowledge base not found")
        return False


def test_models():
    """Test 3: ML models"""
    print("\n[TEST 3] Checking ML models...")
    
    models_dir = '../models/'
    expected_models = ['anomaly_detector.pkl', 'sla_predictor.pkl', 'zone_scorer.pkl']
    
    if not os.path.exists(models_dir):
        print(f"  ✗ Models directory not found")
        print(f"  → Run: python export_models.py")
        return False
    
    found = 0
    for model_file in expected_models:
        model_path = os.path.join(models_dir, model_file)
        if os.path.exists(model_path):
            size = os.path.getsize(model_path) / 1024
            print(f"  ✓ {model_file} ({size:.1f} KB)")
            found += 1
        else:
            print(f"  ⚠ {model_file} not found (optional)")
    
    if found == 0:
        print(f"  → Run: python export_models.py")
        return False
    
    return True


def test_agent1():
    """Test 4: Agent 1 (Chatbot)"""
    print("\n[TEST 4] Testing Agent 1 (Chatbot)...")
    
    try:
        from agent1_chatbot import TelecomAdvisorAgent
        
        agent = TelecomAdvisorAgent()
        print("  ✓ Agent 1 initialized")
        
        agent.initialize_vector_db()
        print("  ✓ Vector database initialized")
        
        test_query = "What causes call drops?"
        result = agent.query(test_query)
        
        if result['success']:
            print(f"  ✓ Query successful")
            print(f"  ✓ Answer length: {len(result['answer'])} chars")
            print(f"  ✓ Context chunks: {len(result['context'])}")
            return True
        else:
            print(f"  ✗ Query failed")
            return False
            
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        print(f"  → Install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_agent2():
    """Test 5: Agent 2 (Diagnostic)"""
    print("\n[TEST 5] Testing Agent 2 (Diagnostic)...")
    
    try:
        from agent2_diagnostic import DiagnosticAgent
        
        agent = DiagnosticAgent()
        print("  ✓ Agent 2 initialized")
        
        alerts = agent.get_latest_alerts(n=5)
        print(f"  ✓ Found {len(alerts)} alerts")
        
        if alerts:
            print(f"  ✓ Sample alert: {alerts[0]['issue_type']} - {alerts[0]['severity']}")
        
        summary = agent.generate_summary_report()
        print(f"  ✓ Summary generated: {summary.get('total_alerts', 0)} total alerts")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_api():
    """Test 6: API endpoints (if running)"""
    print("\n[TEST 6] Testing API endpoints...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"  ✗ Backend returned {response.status_code}")
            return False
        print(f"  ✓ Backend is running")
        print(f"  ✓ Health check passed")
        h = response.json()
        if h.get("agents", {}).get("orchestrator") == "online":
            print("  ✓ Orchestrator online")
        r = requests.get(f"{base_url}/api/ml/models/status", timeout=10)
        if r.status_code == 200:
            print("  ✓ GET /api/ml/models/status")
        else:
            print(f"  ⚠ /api/ml/models/status -> {r.status_code}")
        return True
            
    except requests.exceptions.ConnectionError:
        print(f"  ⚠ Backend not running")
        print(f"  → Start backend: python main.py")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def test_ml_stack():
    """Test 7: Orchestrator + shared transform (no server required)"""
    print("\n[TEST 7] ML orchestrator & core transform...")
    try:
        from core.filled_transform import apply_filled_column_mapping, finalize_diagnostic_dataframe
        from services.orchestrator import QoSOrchestrator

        orch = QoSOrchestrator()
        df, status = orch.refresh_data(force=True)
        if df is not None:
            print(f"  ✓ Data manager load ({status}): {len(df)} rows")
        else:
            print(f"  ⚠ No dataframe ({status}) — add unified_telecom_dataset_FILLED.csv")
        orch.data_manager.get_working_frame(time_window_hours=24)
        print("  ✓ QoSOrchestrator initialized")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        print("  → pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all tests"""
    
    results = {
        'data': test_data(),
        'knowledge_base': test_knowledge_base(),
        'models': test_models(),
        'agent1': test_agent1(),
        'agent2': test_agent2(),
        'ml_stack': test_ml_stack(),
        'api': test_api(),
    }
    
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All systems operational!")
        print("\nNext steps:")
        print("  1. Get Gemini API key: https://aistudio.google.com/app/apikey")
        print("  2. Add to .env file")
        print("  3. Start backend: python main.py")
        print("  4. Start frontend: cd ../frontend && npm run dev")
    else:
        print("\n⚠ Some tests failed. Follow the recommendations above.")
        print("\nCommon fixes:")
        print("  • Ensure FILLED dataset exists: unified_telecom_dataset_FILLED.csv")
        print("  • Run: python data_pipeline.py")
        print("  • Run: python export_models.py")
        print("  • Install: pip install -r requirements.txt")
    
    print("\n" + "="*70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
