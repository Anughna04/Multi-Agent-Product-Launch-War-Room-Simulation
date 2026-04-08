import json
import os
import sys
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv()

from orchestrator.langgraph_setup import build_graph
from utils.logger import logger

def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "scenario_1"
    logger.info("Starting Multi-Agent Product Launch War Room...")
    logger.info(f"Running scenario: {scenario}")
    
    app = build_graph()
    
    initial_state = {
        "scenario": scenario,
        "metrics_summary": {},
        "pm_analysis": {},
        "marketing_summary": {},
        "sre_health": {},
        "support_clusters": {},
        "risk_assessment": {},
        "final_decision": {}
    }
    
    final_state = app.invoke(initial_state)
    
    decision = final_state.get("final_decision", {})
    formatted_output = json.dumps(decision, indent=2)
    print("\n" + "="*50)
    print("FINAL WAR ROOM DECISION")
    print("="*50)
    print(formatted_output)
    print("="*50)
    logger.info("War room simulation completed.")
    
    # Log output (for traceability)
    logger.info("\n" + "="*50)
    logger.info("FINAL WAR ROOM DECISION")
    logger.info("="*50)
    logger.info(formatted_output)
    logger.info("="*50)
    
if __name__ == "__main__":
    main()
