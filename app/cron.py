from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import os
from datetime import datetime
from .api import run_rebalance_workflow

def setup_logging():
    """Setup logging directory"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def log_rebalance_result(result: dict, log_dir: str):
    """Log rebalance result to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{log_dir}/rebalance_{timestamp}.json"
    
    try:
        with open(filename, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Rebalance result logged to {filename}")
    except Exception as e:
        print(f"Failed to log result: {e}")

def run_scheduled_rebalance():
    """Execute scheduled rebalance and log results"""
    print(f"Starting scheduled rebalance at {datetime.now()}")
    
    try:
        # Run the rebalance workflow
        result = run_rebalance_workflow()
        
        # Log the result
        log_dir = setup_logging()
        log_rebalance_result(result, log_dir)
        
        # Print summary
        if result.get("status") == "completed":
            decision = result.get("decision", {})
            action = decision.get("action", "UNKNOWN")
            print(f"Rebalance completed: {action}")
            
            if action == "REBALANCE":
                execution = result.get("execution", {})
                tx_result = execution.get("transaction_result", {})
                if tx_result.get("success"):
                    print(f"Transaction successful: {tx_result.get('tx_hash', 'N/A')}")
                else:
                    print(f"Transaction failed: {tx_result.get('error', 'Unknown error')}")
        else:
            print(f"Rebalance failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        error_result = {
            "timestamp": str(datetime.now()),
            "error": str(e),
            "status": "failed"
        }
        log_dir = setup_logging()
        log_rebalance_result(error_result, log_dir)
        print(f"Scheduled rebalance failed: {e}")

def start_scheduler():
    """Start the APScheduler with cron jobs"""
    scheduler = BlockingScheduler()
    
    # Add cron job for twice-daily runs (00:00 and 12:00 UTC)
    scheduler.add_job(
        run_scheduled_rebalance,
        CronTrigger(hour="0,12", minute="0"),
        id="rebalance_job",
        name="Daily Rebalance Job",
        replace_existing=True
    )
    
    print("Scheduler started with cron job: 0 0,12 * * * (00:00 and 12:00 UTC)")
    print("Press Ctrl+C to stop the scheduler")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped by user")
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler() 