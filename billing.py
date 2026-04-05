import boto3
import requests
import json
from datetime import datetime, timedelta
from rich import print

# -----------------------------
# CONFIG
# -----------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder"

ce = boto3.client('ce')  # Cost Explorer

# -----------------------------
# GET COST DATA
# -----------------------------
def get_cost_data():
    end = datetime.utcnow().date()
    start = end - timedelta(days=7)

    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': str(start),
            'End': str(end)
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'SERVICE'}
        ]
    )

    return response


# -----------------------------
# FORMAT COST DATA
# -----------------------------
def format_cost_data(data):
    summary = {}

    for day in data["ResultsByTime"]:
        for group in day["Groups"]:
            service = group["Keys"][0]
            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])

            summary[service] = summary.get(service, 0) + cost

    return summary


# -----------------------------
# AI ANALYSIS
# -----------------------------
def analyze_with_ai(cost_data):
    prompt = f"""
You are a cloud cost optimization expert.

Analyze this AWS cost data and provide:
1. Top costly services
2. Optimization suggestions
3. Any anomalies

Cost Data:
{json.dumps(cost_data, indent=2)}

Give concise output.
"""

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })

    return response.json().get("response", "No response")


# -----------------------------
# MAIN
# -----------------------------
def main():
    print("[bold green]💰 AWS Billing AI Agent[/bold green]\n")

    print("Fetching cost data...\n")

    raw_data = get_cost_data()
    cost_summary = format_cost_data(raw_data)

    print("[cyan]Cost Summary (Last 7 days):[/cyan]")
    print(cost_summary)

    print("\n[cyan]AI Analysis:[/cyan]\n")

    analysis = analyze_with_ai(cost_summary)
    print(f"[magenta]{analysis}[/magenta]")


if __name__ == "__main__":
    main()
