import pandas as pd
import json
from typing import Dict, Any

def get_metrics_data(state: dict = None) -> pd.DataFrame:
    scenario = state.get("scenario", "scenario_1") if state else "scenario_1"
    df = pd.read_json(f"data/{scenario}/metrics.json")
    required_cols = {
        "signup_conversion_rate", "daily_active_users", "retention_d1", "retention_d7",
        "crash_rate", "api_latency_p95", "payment_failure_rate", "support_ticket_volume",
        "feature_adoption_rate", "churn_rate"
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required metric fields: {missing}")
    return df

def get_feedback_data(state: dict = None) -> list:
    scenario = state.get("scenario", "scenario_1") if state else "scenario_1"
    import os
    file_path = f"data/{scenario}/feedback.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Feedback data not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not data:
            raise ValueError("Feedback data is empty.")
        from utils.logger import logger
        logger.info(f"[DataLoader] Loaded feedback from {scenario}")
        return data

def analyze_metrics_tool(state: dict = None) -> Dict[str, Any]:
    try:
        df = get_metrics_data(state)
        if df.empty or len(df) < 10:
            return {"error": "Insufficient metrics data."}
            
        first_5 = df.head(5).mean()
        last_5 = df.tail(5).mean()
        
        def pct_change(first, last):
            return ((last - first) / first) * 100 if first != 0 else 0
            
        trend_analysis = {
            "conversion_change_pct": pct_change(first_5["signup_conversion_rate"], last_5["signup_conversion_rate"]),
            "dau_change_pct": pct_change(first_5["daily_active_users"], last_5["daily_active_users"]),
            "retention_change_pct": pct_change(first_5["retention_d1"], last_5["retention_d1"]),
            "churn_change_pct": pct_change(first_5["churn_rate"], last_5["churn_rate"]),
            "adoption_change_pct": pct_change(first_5["feature_adoption_rate"], last_5["feature_adoption_rate"])
        }
        
        system_health = {
            "avg_crash_rate": float(last_5["crash_rate"]),
            "avg_latency": float(last_5["api_latency_p95"]),
            "avg_payment_failure": float(last_5["payment_failure_rate"]),
            "support_ticket_growth": pct_change(first_5["support_ticket_volume"], last_5["support_ticket_volume"])
        }
        
        summary = "Severe degradation observed in core metrics during late rollout phase." if system_health["avg_crash_rate"] > 1.0 else "Stable telemetry."
        
        print("[DataAgent] Processed 10 metrics fields")
        return {
            "trend_analysis": trend_analysis,
            "system_health": system_health,
            "summary": summary
        }
    except Exception as e:
        return {"error": str(e)}

def anomaly_detection_tool(state: dict = None) -> Dict[str, Any]:
    try:
        df = get_metrics_data(state)
        spikes = []
        for _, row in df.iterrows():
            if row["crash_rate"] > 2.0:
                spikes.append({"metric": "crash_rate", "day": row["day"], "value": row["crash_rate"]})
            if row["payment_failure_rate"] > 5.0:
                spikes.append({"metric": "payment_failure_rate", "day": row["day"], "value": row["payment_failure_rate"]})
                
        degradations = []
        first_5 = df.head(5).mean()
        last_5 = df.tail(5).mean()
        
        if last_5["api_latency_p95"] > first_5["api_latency_p95"] * 1.2:
            degradations.append({"metric": "api_latency_p95", "pattern": "increasing trend"})
        if last_5["retention_d1"] < first_5["retention_d1"] * 0.9:
            degradations.append({"metric": "retention_d1", "pattern": "decreasing trend"})

        correlations = []
        if any(d["metric"] == "api_latency_p95" for d in degradations) and last_5["signup_conversion_rate"] < first_5["signup_conversion_rate"]:
            correlations.append("latency increasing + conversion decreasing")
        if any(s["metric"] == "payment_failure_rate" for s in spikes) and last_5["churn_rate"] > first_5["churn_rate"]:
            correlations.append("payment_failure spiking + churn increasing")

        print(f"[AnomalyTool] Found {len(spikes) + len(degradations)} anomalies")
        return {
            "spikes": spikes,
            "degradations": degradations,
            "correlations": correlations
        }
    except Exception as e:
        return {"error": str(e)}

def _enrich_with_sentiment(data: list):
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        for item in data:
            text = str(item.get("text", ""))
            scores = analyzer.polarity_scores(text)
            compound = scores["compound"]
            if compound >= 0.35:
                item["sentiment"] = "positive"
            else:
                item["sentiment"] = "negative"
    except Exception:
        pass # Fallback to existing hard-coded JSON sentiment if analyzer fails

def sentiment_summary_tool(state: dict = None) -> Dict[str, Any]:
    try:
        from utils.logger import logger
        data = get_feedback_data(state)
        _enrich_with_sentiment(data)
        logger.info(f"[SentimentTool] Loaded {len(data)} entries")
        
        positive = 0
        neutral = 0
        negative = 0
        for item in data:
            sentiment = str(item.get("sentiment", "")).strip().lower()
            if sentiment == "positive":
                positive += 1
            elif sentiment == "negative":
                negative += 1
            else:
                neutral += 1
                
        total = positive + neutral + negative
        logger.info(f"[SentimentTool] Positive: {positive}, Negative: {negative}")
        
        if total == 0:
            return {"error": "No feedback data available"}
        
        tags = [item.get("tag") for item in data if str(item.get("sentiment", "")).strip().lower() == "negative"]
        from collections import Counter
        top_issues = [tag for tag, _ in Counter(tags).most_common(3)]
        
        critical_examples = [item["text"] for item in data if str(item.get("sentiment", "")).strip().lower() == "negative"][:3]
        
        print(f"[MarketingAgent] Processed {total} feedback entries")
        return {
            "sentiment_distribution": {
                "positive": round((positive/total)*100, 2),
                "neutral": round((neutral/total)*100, 2),
                "negative": round((negative/total)*100, 2)
            },
            "top_issues": top_issues,
            "critical_examples": critical_examples
        }
    except Exception as e:
        return {"error": str(e)}

def risk_scoring_tool(state: dict = None) -> Dict[str, Any]:
    try:
        from utils.logger import logger
        df = get_metrics_data(state)
        last_day = df.iloc[-1]
        
        crash_risk = min(last_day["crash_rate"] / 3.0, 1.0)
        payment_risk = min(last_day["payment_failure_rate"] / 10.0, 1.0)
        churn_risk = min(last_day["churn_rate"] / 10.0, 1.0)
        latency_risk = min(last_day["api_latency_p95"] / 1000.0, 1.0)
        
        data = get_feedback_data(state)
        _enrich_with_sentiment(data)
        total = max(len(data), 1)
        negative_count = sum(1 for item in data if str(item.get("sentiment", "")).strip().lower() == "negative")
        negative_pct = negative_count / total
        sentiment_risk = min(negative_pct / 0.7, 1.0)

        logger.info(f"[RiskTool] crash: {crash_risk}, payment: {payment_risk}, churn: {churn_risk}, latency: {latency_risk}, sentiment: {sentiment_risk}")

        score = (crash_risk * 0.30) + (payment_risk * 0.25) + (churn_risk * 0.20) + (latency_risk * 0.15) + (sentiment_risk * 0.10)
        
        level = "low"
        if score > 0.7:
            level = "high"
        elif score > 0.4:
            level = "medium"
            
        print(f"[RiskTool] Risk score = {round(score, 2)} ({level.upper()})")
        return {
            "score": round(score, 2),
            "level": level,
            "drivers": [
                {"factor": "crash_rate", "contribution": round(crash_risk * 0.30, 2)},
                {"factor": "payment_failure", "contribution": round(payment_risk * 0.25, 2)},
                {"factor": "churn", "contribution": round(churn_risk * 0.20, 2)},
                {"factor": "latency", "contribution": round(latency_risk * 0.15, 2)},
                {"factor": "sentiment", "contribution": round(sentiment_risk * 0.10, 2)}
            ]
        }
    except Exception as e:
        return {"error": str(e)}
