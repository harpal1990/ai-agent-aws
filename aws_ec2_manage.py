import requests
import boto3
import json
import re
from rich import print

# -----------------------------
# CONFIG
# -----------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder"

ec2 = boto3.client('ec2')

SYSTEM_PROMPT = """
You are a DevOps AI agent.

STRICT RULES:
- ONLY return valid JSON
- DO NOT use markdown
- DO NOT use ```json
- NO explanation text
- Fix spelling mistakes automatically

Supported actions:
1. list_ec2
2. start_ec2
3. stop_ec2

User can refer instance by:
- instance_id
- name

Examples:

User: show ec2
Response:
{"action": "list_ec2"}

User: start test server
Response:
{"action": "start_ec2", "name": "test"}

User: stop instance i-123
Response:
{"action": "stop_ec2", "instance_id": "i-123"}
"""

# -----------------------------
# AI CALL
# -----------------------------
def ask_ai(prompt):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": SYSTEM_PROMPT + "\nUser: " + prompt,
            "stream": False
        })

        data = response.json()

        print("[blue]RAW AI RESPONSE:[/blue]", data)

        if "response" not in data:
            return f"ERROR: Invalid API response -> {data}"

        return data["response"]

    except Exception as e:
        return f"ERROR: Request failed -> {str(e)}"


# -----------------------------
# CLEAN JSON
# -----------------------------
def extract_json(text):
    if not text:
        return None

    text = re.sub(r"```json|```", "", text)
    match = re.search(r'\{.*\}', text, re.DOTALL)

    return match.group(0).strip() if match else None


# -----------------------------
# HELPER: FIND INSTANCE BY NAME
# -----------------------------
def get_instance_id_by_name(name):
    instances = ec2.describe_instances()

    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            if "Tags" in instance:
                for tag in instance["Tags"]:
                    if tag["Key"] == "Name" and tag["Value"].lower() == name.lower():
                        return instance["InstanceId"]

    return None


# -----------------------------
# EXECUTE ACTION
# -----------------------------
def execute_action(action_json):
    action = action_json.get("action")

    try:
        # -----------------
        # LIST EC2
        # -----------------
        if action == "list_ec2":
            instances = ec2.describe_instances()

            result = []

            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:

                    name = "N/A"
                    if "Tags" in instance:
                        for tag in instance["Tags"]:
                            if tag["Key"] == "Name":
                                name = tag["Value"]

                    result.append({
                        "InstanceId": instance["InstanceId"],
                        "Name": name,
                        "State": instance["State"]["Name"],
                        "InstanceType": instance["InstanceType"],
                        "PrivateIP": instance.get("PrivateIpAddress"),
                        "PublicIP": instance.get("PublicIpAddress")
                    })

            return result

        # -----------------
        # START EC2
        # -----------------
        elif action == "start_ec2":
            instance_id = action_json.get("instance_id")

            if not instance_id and "name" in action_json:
                instance_id = get_instance_id_by_name(action_json["name"])

            if not instance_id:
                return "❌ Instance not found"

            ec2.start_instances(InstanceIds=[instance_id])
            return f"✅ Instance {instance_id} started"

        # -----------------
        # STOP EC2
        # -----------------
        elif action == "stop_ec2":
            instance_id = action_json.get("instance_id")

            if not instance_id and "name" in action_json:
                instance_id = get_instance_id_by_name(action_json["name"])

            if not instance_id:
                return "❌ Instance not found"

            ec2.stop_instances(InstanceIds=[instance_id])
            return f"🛑 Instance {instance_id} stopped"

        else:
            return "❌ Unknown action"

    except Exception as e:
        return f"❌ AWS Error: {str(e)}"


# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    print("[bold green]🚀 AWS DevOps AI Agent Started[/bold green]\n")

    while True:
        user_input = input(">> ").strip()

        if user_input.lower() == "exit":
            break

        ai_output = ask_ai(user_input)

        # Handle API error
        if ai_output.startswith("ERROR"):
            print(f"[red]{ai_output}[/red]")
            continue

        clean_json = extract_json(ai_output)

        if not clean_json:
            print("[red]❌ Could not extract JSON[/red]")
            print(ai_output)
            continue

        try:
            action_json = json.loads(clean_json)
        except Exception as e:
            print("[red]❌ JSON parse error[/red]", e)
            print(clean_json)
            continue

        print("\n[cyan]📌 Planned Action:[/cyan]")
        print(action_json)

        confirm = input("\nApprove? (yes/no): ")

        if confirm.lower() == "yes":
            result = execute_action(action_json)
            print(f"\n[green]{result}[/green]")
        else:
            print("[yellow]❌ Cancelled[/yellow]")


if __name__ == "__main__":
    main()
