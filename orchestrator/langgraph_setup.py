import json
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from agents.all_agents import (
    get_data_analyst, get_pm_agent, get_marketing_agent,
    get_sre_agent, get_customer_support_agent, get_risk_agent
)
from llm.llm_provider import LLMFactory
from utils.logger import logger

class WarRoomState(TypedDict):
    scenario:str
    DataAnalystAgent_output: Dict[str, Any]
    PMAgent_output: Dict[str, Any]
    MarketingAgent_output: Dict[str, Any]
    SREAgent_output: Dict[str, Any]
    CustomerSupportAgent_output: Dict[str, Any]
    RiskCriticAgent_output: Dict[str, Any]
    final_decision: Dict[str, Any]

def data_analyst_node(state: dict):
    agent = get_data_analyst()
    print(f"[DEBUG] Before {agent.name}:", state.keys())
    updated_state = agent.run(state)
    print(f"[DEBUG] After {agent.name}:", updated_state.keys())
    return updated_state

def pm_node(state: dict):
    agent = get_pm_agent()
    print(f"[DEBUG] Before {agent.name}:", state.keys())
    updated_state = agent.run(state)
    print(f"[DEBUG] After {agent.name}:", updated_state.keys())
    return updated_state

def marketing_node(state: dict):
    agent = get_marketing_agent()
    print(f"[DEBUG] Before {agent.name}:", state.keys())
    updated_state = agent.run(state)
    print(f"[DEBUG] After {agent.name}:", updated_state.keys())
    return updated_state

def sre_node(state: dict):
    agent = get_sre_agent()
    print(f"[DEBUG] Before {agent.name}:", state.keys())
    updated_state = agent.run(state)
    print(f"[DEBUG] After {agent.name}:", updated_state.keys())
    return updated_state

def support_node(state: dict):
    agent = get_customer_support_agent()
    print(f"[DEBUG] Before {agent.name}:", state.keys())
    updated_state = agent.run(state)
    print(f"[DEBUG] After {agent.name}:", updated_state.keys())
    return updated_state

def risk_node(state: dict):
    agent = get_risk_agent()
    print(f"[DEBUG] Before {agent.name}:", state.keys())
    updated_state = agent.run(state)
    print(f"[DEBUG] After {agent.name}:", updated_state.keys())
    return updated_state

def orchestrator_node(state: dict):
    logger.info("[Orchestrator] Synthesizing final decision.")
    print("[DEBUG] STATE KEYS AT ORCHESTRATOR:", state.keys())
    
    # 🚨 ISSUE 1, 3, 4, 5, 6: Direct Access & Fail Loudly
    try:
        risk = state["RiskCriticAgent_output"]
        pm = state["PMAgent_output"]
        marketing = state["MarketingAgent_output"]
        data_agent = state["DataAnalystAgent_output"]
        sre = state["SREAgent_output"]
        support = state["CustomerSupportAgent_output"]
    except KeyError as e:
        logger.error(f"[Orchestrator] CRITICAL ERROR: Missing expected key in state: {e}")
        state["final_decision"] = {
            "decision": "PAUSE",
            "rationale": [f"Insufficient agent data: {e} missing from state."],
            "risk_register": [{"risk": "Pipeline failure", "severity": "high", "mitigation": "Review system logs"}],
            "action_plan": [{"action": "Investigate pipeline", "owner": "SRE", "timeline": "Immediate"}],
            "communication_plan": {"internal": "Halt", "external": "Monitor"},
            "confidence_score": 0.0,
            "confidence_improvement": []
        }
        return state

    try:
        risk_score = float(risk.get("composite_risk_score", risk.get("score", 0.0)) or 0.0)
    except (ValueError, TypeError):
        risk_score = 0.0

    sentiment_dist = marketing.get("sentiment_distribution", {})
    try:
        neg_sentiment = float(sentiment_dist.get("negative", 0.0) or 0.0)
    except (ValueError, TypeError):
        neg_sentiment = 0.0
        
    if 0 < neg_sentiment <= 1.0:
        neg_sentiment = neg_sentiment * 100.0

    pm_rec = str(pm.get("go_no_go_recommendation", "")).upper()

    logger.info(f"[Orchestrator] risk={risk_score}, sentiment={neg_sentiment}, pm={pm_rec}")

    #  ISSUE 6: ORCHESTRATOR DECISION STABILITY
    
    if risk_score >= 0.75 and neg_sentiment >= 60.0:
        decision = "ROLLBACK"
    elif risk_score >= 0.5:
        decision = "PAUSE"
    else:
        decision = "PROCEED"
    logger.info(f"[Orchestrator] Final decision: {decision}")

    #  ISSUE 6 & 9: Fallbacks & Rationale
    if risk_score == 0.0 and neg_sentiment == 0.0 and pm_rec == "":
        decision = "PAUSE"
        
    rationale = []
    if decision == "PAUSE" and pm_rec == "" and risk_score == 0.0:
        rationale.append("Insufficient agent data across metrics, sentiment, and risk.")
    else:
        rationale.append(f"Composite risk score assessed at {risk_score}.")
        rationale.append(f"Negative sentiment detected at {neg_sentiment}%.")
        rationale.append(f"PM structural recommendation: {pm_rec if pm_rec else 'None provided'}.")
    
    defaults = [
        f"Negative sentiment assessed at {neg_sentiment}%.",
        f"Composite risk score assessed at {risk_score}.",
        "System health degradation detected across key metrics."
    ]
    for item in defaults:
        if len(rationale) < 3 and item not in rationale:
            rationale.append(item)

    # 🚨 ISSUE 7 & 8: Risk Register & Data Handling
    anomalies = data_agent.get("anomalies", [])
    if not isinstance(anomalies, list) or not anomalies:
        risk_anoms = risk.get("anomalies", [])
        anomalies = risk_anoms if getattr(risk_anoms, "copy", None) else [{"metric": "Unknown", "pattern": "Assumed degradation."}]

    risk_register = risk.get("risk_register", [])
    if not isinstance(risk_register, list) or not risk_register:
        risk_register = []
        for anom in anomalies[:2]:
            risk_register.append({
                "risk": f"System Metrics Anomaly: {anom.get('metric', anom) if isinstance(anom, dict) else anom}",
                "severity": "high",
                "mitigation": "Awaiting engineering isolation and triage."
            })
        if neg_sentiment >= 20.0:
            risk_register.append({
                "risk": "Elevated negative user sentiment potentially signaling product flaws.",
                "severity": "medium",
                "mitigation": "Comms team to assess social perception risk."
            })
        if pm_rec == "PAUSE":
            risk_register.append({
                "risk": "Product owner flagged launch as unsafe.",
                "severity": "high",
                "mitigation": "Resolve PM blockers before proceeding."
            })
            
        while len(risk_register) < 2:
            risk_register.append({
                "risk": "Potential unmonitored failure cascade.",
                "severity": "medium",
                "mitigation": "Increase observability across all critical paths."
            })

    # 🚨 ISSUE 5: Action Plan Fix
    sre_actions = sre.get("recommended_actions", [])
    support_actions = support.get("recommended_actions", [])
    
    raw_s = sre_actions if isinstance(sre_actions, list) else []
    raw_sup = support_actions if isinstance(support_actions, list) else []
    raw_actions = raw_s + raw_sup
    
    action_plan = []
    for act in raw_actions:
        if isinstance(act, dict):
            action_plan.append({
                "action": str(act.get("action", act.get("task", act.get("description", str(act))))),
                "owner": str(act.get("owner", "Engineering")),
                "timeline": str(act.get("urgency", act.get("timeline", "24-48h")))
            })
        elif isinstance(act, str):
            action_plan.append({
                "action": act,
                "owner": "Engineering",
                "timeline": "24-48h"
            })
            
    if not action_plan:
        action_plan.append({
            "action": "Investigate critical system failures and triage data availability metrics",
            "owner": "Incident Commander",
            "timeline": "Immediate"
        })

    logger.info(f"[Orchestrator] Action plan size: {len(action_plan)}")

    comm_rec = marketing.get("communication_recommendation", {})
    comm_plan = {
        "internal": comm_rec.get("internal_stance", "Monitor system stability. No outward messaging required unless conditions deteriorate."),
        "external": comm_rec.get("external_stance", "We are currently monitoring a minor hiccup in our systems and will restore full service shortly.")
    }

    try:
        confidence_score = float(risk.get("confidence_score", 0.7) or 0.7)
    except (ValueError, TypeError):
        confidence_score = 0.7

    state["final_decision"] = {
        "decision": decision,
        "rationale": rationale,
        "risk_register": risk_register,
        "action_plan": action_plan,
        "communication_plan": comm_plan,
        "confidence_score": confidence_score,
        "confidence_improvement": risk.get("confidence_improvement_actions", [])
    }
    
    return state

def build_graph():
    workflow = StateGraph(WarRoomState)
    
    workflow.add_node("data_analyst", data_analyst_node)
    workflow.add_node("pm", pm_node)
    workflow.add_node("marketing", marketing_node)
    workflow.add_node("sre", sre_node)
    workflow.add_node("support", support_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("orchestrator", orchestrator_node)
    
    workflow.add_edge(START, "data_analyst")
    workflow.add_edge("data_analyst", "pm")
    workflow.add_edge("pm", "marketing")
    workflow.add_edge("marketing", "sre")
    workflow.add_edge("sre", "support")
    workflow.add_edge("support", "risk")
    workflow.add_edge("risk", "orchestrator")
    workflow.add_edge("orchestrator", END)
    
    return workflow.compile()
