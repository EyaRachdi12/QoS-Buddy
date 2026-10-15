"""
Background Task Scheduler for Agent 2
Runs periodic diagnostics and maintenance tasks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

from agent2_diagnostic import DiagnosticAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiagnosticScheduler:
    """
    Manages periodic background tasks for Agent 2
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.agent2 = DiagnosticAgent()
        self.alert_history = []
    
    def run_periodic_diagnostics(self):
        """Task 1: Run diagnostics every 5 minutes"""
        try:
            logger.info(f"[{datetime.now()}] Running periodic diagnostics...")
            alerts = self.agent2.run_diagnostics()
            
            if alerts:
                self.alert_history.extend(alerts)
                logger.warning(f"⚠ {len(alerts)} new alerts detected")
            else:
                logger.info("✓ No issues detected")
                
        except Exception as e:
            logger.error(f"Diagnostic task failed: {e}")
    
    def cleanup_old_alerts(self):
        """Task 2: Cleanup alerts older than 7 days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=7)
            
            initial_count = len(self.alert_history)
            self.alert_history = [
                alert for alert in self.alert_history
                if datetime.fromisoformat(alert['timestamp']) > cutoff_time
            ]
            
            cleaned = initial_count - len(self.alert_history)
            if cleaned > 0:
                logger.info(f"🗑 Cleaned {cleaned} old alerts")
                
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
    
    def start(self):
        """Start the scheduler"""
        logger.info("="*70)
        logger.info("STARTING BACKGROUND SCHEDULER")
        logger.info("="*70)
        
        self.scheduler.add_job(
            self.run_periodic_diagnostics,
            trigger=IntervalTrigger(minutes=5),
            id='diagnostic_scan',
            name='Periodic Diagnostic Scan',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Diagnostic scan (every 5 minutes)")
        
        self.scheduler.add_job(
            self.cleanup_old_alerts,
            trigger=IntervalTrigger(hours=24),
            id='alert_cleanup',
            name='Alert History Cleanup',
            replace_existing=True
        )
        logger.info("✓ Scheduled: Alert cleanup (every 24 hours)")
        
        self.scheduler.start()
        logger.info("✓ Scheduler started\n")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    scheduler = DiagnosticScheduler()
    scheduler.start()
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
        scheduler.stop()
