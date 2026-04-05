import requests
import boto3
import json
import re
from rich import print
from rich.table import Table

# -----------------------------
# CONFIG
# -----------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder"

ec2 = boto3.client('ec2')

SYSTEM_PROMPT = """
You are a DevOps AI agent for AWS EC2 management.

=====================
RULES (VERY IMPORTANT)
=====================
- ALWAYS return ONLY valid JSON
- NO explanation
- NO markdown
- NO ``` or ```json
- Output must be directly parsable

=====================
SUPPORTED ACTIONS
=====================
1. list_ec2
2. start_ec2
3. stop_ec2

=====================
INPUT HANDLING
=====================
- Fix spelling mistakes automatically
- Understand natural language
- Extract instance name or ID correctly

=====================
OUTPUT FORMAT
=====================
For list:
{"action": "list_ec2"}

For start:
{"action": "start_ec2", "instance_id": "i-123"}
OR
{"action": "start_ec2", "name": "test"}

For stop:
{"action": "stop_ec2", "instance_id": "i-123"}
OR
{"action": "stop_ec2", "name": "test"}
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

        return data.get("response", "")

    except Exception as e:
        return f"ERROR: {str(e)}"


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
# FIND INSTANCE BY NAME
# -----------------------------
def get_instance_id_by_name(name):
    instances = ec2.describe_instances()

    for r in instances["Reservations"]:
        for i in r["Instances"]:
            if "Tags" in i:
                for tag in i["Tags"]:
                    if tag["Key"] == "Name" and tag["Value"].lower() == name.lower():
                        return i["InstanceId"]

    return None


# -----------------------------
# PRINT TABLE
# -----------------------------
def print_ec2_table(instances):
    table = Table(title="EC2 Instances")

    table.add_column("Instance ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("State", style="yellow")
    table.add_column("Type")
    table.add_column("Private IP")
    table.add_column("Public IP")

    for inst in instances:
        table.add_row(
            inst.get("InstanceId", ""),
            inst.get("Name", ""),
            inst.get("State", ""),
            inst.get("InstanceType", ""),
            str(inst.get("PrivateIP", "")),
            str(inst.get("PublicIP", ""))
        )

    print(table)


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
            data = ec2.describe_instances()
            result = []

            for r in data["Reservations"]:
                for i in r["Instances"]:
                    name = "N/A"
                    if "Tags" in i:
                        for tag in i["Tags"]:
                            if tag["Key"] == "Name":
                                name = tag["Value"]

                    result.append({
                        "InstanceId": i["InstanceId"],
                        "Name": name,
                        "State": i["State"]["Name"],
                        "InstanceType": i["InstanceType"],
                        "PrivateIP": i.get("PrivateIpAddress"),
                        "PublicIP": i.get("PublicIpAddress")
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
# MAIN
# -----------------------------
def main():
    print("[bold green]🚀 AWS DevOps AI Agent Started[/bold green]\n")

    while True:
        user_input = input(">> ").strip()

        if user_input.lower() == "exit":
            break

        ai_output = ask_ai(user_input)

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

            if isinstance(result, list):
                print_ec2_table(result)
            else:
                print(f"\n[green]{result}[/green]")
        else:
            print("[yellow]❌ Cancelled[/yellow]")


if __name__ == "__main__":
    main()
