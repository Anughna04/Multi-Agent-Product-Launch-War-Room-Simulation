from agents.base_agent import BaseAgent
from utils.prompts import (
    DATA_ANALYST_PROMPT,
    PM_AGENT_PROMPT,
    MARKETING_AGENT_PROMPT,
    SRE_AGENT_PROMPT,
    CUSTOMER_SUPPORT_AGENT_PROMPT,
    RISK_AGENT_PROMPT
)
from tools.all_tools import (
    analyze_metrics_tool,
    anomaly_detection_tool,
    sentiment_summary_tool,
    risk_scoring_tool
)

def get_data_analyst() -> BaseAgent:
    return BaseAgent(
        name="DataAnalystAgent",
        system_prompt=DATA_ANALYST_PROMPT,
        tools=[analyze_metrics_tool, anomaly_detection_tool],
        required_keys=["metric_summary"]
    )

def get_pm_agent() -> BaseAgent:
    return BaseAgent(
        name="PMAgent",
        system_prompt=PM_AGENT_PROMPT,
        tools=[],
        required_keys=["go_no_go_recommendation"]
    )

def get_marketing_agent() -> BaseAgent:
    return BaseAgent(
        name="MarketingAgent",
        system_prompt=MARKETING_AGENT_PROMPT,
        tools=[sentiment_summary_tool],
        required_keys=["sentiment_distribution"]
    )

def get_sre_agent() -> BaseAgent:
    return BaseAgent(
        name="SREAgent",
        system_prompt=SRE_AGENT_PROMPT,
        tools=[],
        required_keys=["system_health_score", "engineering_recommendation"]
    )

def get_customer_support_agent() -> BaseAgent:
    return BaseAgent(
        name="CustomerSupportAgent",
        system_prompt=CUSTOMER_SUPPORT_AGENT_PROMPT,
        tools=[sentiment_summary_tool],
        required_keys=["feedback_volume_assessment"]
    )

def get_risk_agent() -> BaseAgent:
    return BaseAgent(
        name="RiskCriticAgent",
        system_prompt=RISK_AGENT_PROMPT,
        tools=[risk_scoring_tool, anomaly_detection_tool],
        required_keys=["composite_risk_score", "final_recommendation"]
    )
