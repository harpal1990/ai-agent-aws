🚀 AWS AI DevOps & Billing Agent

This project provides a local AI-powered DevOps & SRE assistant that can:

Manage AWS resources (EC2, ECS)
Analyze CloudWatch logs
Perform basic auto-healing
Analyze AWS billing and suggest optimizations

Powered by:

Ollama (local LLM)
Python + boto3 (AWS SDK)

📦 Features
🔧 DevOps Agent
List EC2 instances
Start/Stop EC2 (by ID or Name)
Restart ECS services
Analyze logs
Basic auto-healing (e.g., 502 errors)

💰 Billing Agent
Fetch AWS cost (last 7 days)
Service-wise breakdown
AI-based cost optimization suggestions

⚙️ Prerequisites
1. System Requirements
Ubuntu 20.04 / 22.04 / 24.04
Python 3.8+
Internet access

2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

Pull model:

# ollama pull qwen2.5-coder

Verify:

# ollama list

3. Install Python Dependencies
pip install boto3 requests rich

5. Configure AWS CLI
aws configure

Provide:

AWS Access Key
AWS Secret Key
Region (e.g., eu-central-1)

5. Required IAM Permissions
✅ EC2
ec2:DescribeInstances
ec2:StartInstances
ec2:StopInstances

✅ ECS
ecs:UpdateService
ecs:DescribeServices

✅ CloudWatch Logs
logs:DescribeLogStreams
logs:GetLogEvents

✅ Billing (Cost Explorer)
ce:GetCostAndUsage
7. Enable Cost Explorer (IMPORTANT)

Go to AWS Console:

👉 Billing → Cost Explorer → Enable

📁 Project Structure
aws-ai-agent/
│── aws_agent.py        # DevOps AI agent
│── billing_agent.py    # Billing analysis agent
│── README.md

▶️ How to Run
🔹 Start Ollama (if not running)

ollama run qwen2.5-coder
🔹 Run DevOps Agent

python3 aws_agent.py
Example Commands:
>> show ec2 instances
>> start test server
>> stop instance i-123


🔹 Run Billing Agent
python3 billing_agent.py
Output:
Cost summary (last 7 days)
AI-based optimization suggestions

🧠 How It Works
User Input → AI (Ollama) → JSON Action → AWS API → Response

🔐 Safety Features
Approval required before execution
JSON validation
Error handling
No direct destructive actions

🚀 Future Enhancements
Slack/Telegram integration
Auto-healing workflows
Kubernetes support
Cost anomaly alerts
Web dashboard (Flask)

⚠️ Troubleshooting
❌ Ollama not responding
curl http://localhost:11434

❌ Model not found
ollama pull qwen2.5-coder

❌ AWS permission error
Check IAM role/user permissions

❌ Empty billing data
Ensure Cost Explorer is enabled
Wait ~24 hours after enabling

🎯 Use Cases
DevOps automation
SRE troubleshooting
Cost optimization
AWS resource management
All running offline using Ollama 🔥
