# QueueStorm Investigator

> **AI/API SupportOps Challenge for Digital Finance**
> **SUST CSE Carnival 2026 – Codex Community Hackathon**

QueueStorm Investigator is an AI-powered complaint investigation API designed for digital finance support systems. Instead of simply classifying customer complaints, it analyzes both the complaint and the customer's recent transaction history to determine the most likely issue, identify supporting evidence, route the case to the correct department, and generate safe responses for both support agents and customers.

The application is built using **FastAPI** and **Google Gemini 2.5 Flash**, with additional rule-based validation to ensure compliance with the competition's safety requirements.

---

# Features

* AI-powered complaint investigation
* Transaction history evidence matching
* Structured JSON responses
* Complaint classification
* Department routing
* Severity prediction
* Human review recommendation
* Safety guardrails against credential requests
* Prompt injection resistance
* Docker support
* FastAPI REST API

---

# Tech Stack

## Backend

* Python 3.11
* FastAPI
* Uvicorn
* Pydantic

## AI

* Google Gemini 2.5 Flash
* Google GenAI SDK

## Deployment

* Docker
* Docker Hub compatible

---

# Project Structure

```
QueueStorm_Investigator/

├── main.py
├── requirements.txt
├── Dockerfile
├── README.md
└── ...
```

---

# API Endpoints

## Health Check

```
GET /
```

Returns

```json
{
  "message": "Hello, SUST Hackathon!"
}
```

---

## Analyze Ticket

```
POST /analyze-ticket
```

Accepts a customer complaint together with recent transaction history and returns an AI-generated investigation.

---

## Example Request

```json
{
  "ticket_id": "TKT-001",
  "complaint": "I accidentally sent 5000 taka to the wrong number.",
  "language": "en",
  "channel": "in_app_chat",
  "user_type": "customer",
  "campaign_context": "boishakh_bonanza_day_1",
  "transaction_history": [
    {
      "transaction_id": "TXN-9101",
      "timestamp": "2026-04-14T14:08:22Z",
      "type": "transfer",
      "amount": 5000,
      "counterparty": "+8801719876543",
      "status": "completed"
    }
  ]
}
```

---

## Example Response

```json
{
  "ticket_id": "TKT-001",
  "relevant_transaction_id": "TXN-9101",
  "evidence_verdict": "consistent",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "...",
  "recommended_next_action": "...",
  "customer_reply": "...",
  "human_review_required": true,
  "confidence": 0.94,
  "reason_codes": [
    "wrong_transfer",
    "transaction_match"
  ]
}
```

---

# AI Investigation Workflow

For every incoming ticket, the API performs the following steps:

1. Validate the incoming request using Pydantic models.
2. Construct a structured prompt containing:

   * Complaint
   * Customer metadata
   * Transaction history
3. Send the prompt to Gemini 2.5 Flash.
4. Receive structured JSON output.
5. Validate the generated JSON.
6. Enforce allowed enum values.
7. Insert default values for missing fields.
8. Apply safety guardrails.
9. Return the final validated JSON response.

---

# Safety Guardrails

After receiving Gemini's output, QueueStorm Investigator performs additional rule-based validation.

The application automatically blocks responses that:

* Ask for OTP
* Ask for PIN
* Ask for Password
* Ask for CVV
* Ask for Verification Codes

It also prevents responses that:

* Promise refunds
* Guarantee money recovery
* Promise account unblocking
* Promise completed reversals

If any unsafe language is detected, the system replaces it with a safe customer response.

---

# Human Review Logic

Human review is automatically enforced for high-risk cases including:

* Wrong Transfer
* Payment Failed
* Phishing / Social Engineering

If Gemini returns uncertain information, the API also defaults to human review.

---

# Supported Case Types

* wrong_transfer
* payment_failed
* refund_request
* duplicate_payment
* merchant_settlement_delay
* agent_cash_in_issue
* phishing_or_social_engineering
* other

---

# Supported Departments

* customer_support
* dispute_resolution
* payments_ops
* merchant_operations
* agent_operations
* fraud_risk

---

# Installation

Clone the repository

```bash
git clone https://github.com/overcO-Oked/Queuestorm_Investigator.git
```

Enter the project directory

```bash
cd Queuestorm_Investigator
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Run the application

```bash
uvicorn main:app --reload
```

The API will start at

```
http://localhost:8000
```

---

# Running with Docker

Build the Docker image

```bash
docker build -t queuestorm-investigator .
```

Run the container

```bash
docker run \
-e GEMINI_API_KEY=YOUR_API_KEY \
-p 8000:8000 \
queuestorm-investigator
```

The service will be available at

```
http://localhost:8000
```

---

# Environment Variables

| Variable       | Description           |
| -------------- | --------------------- |
| GEMINI_API_KEY | Google Gemini API Key |

---

# Models Used

| Model            | Purpose                                                                             | Runs On           |
| ---------------- | ----------------------------------------------------------------------------------- | ----------------- |
| Gemini 2.5 Flash | Complaint reasoning, evidence analysis, case classification and response generation | Google Gemini API |

### Why Gemini 2.5 Flash?

* Fast inference
* Good structured JSON generation
* Low latency
* Cost-effective
* Strong multilingual understanding (English/Bangla)

---

# Error Handling

The API gracefully handles:

* Empty Gemini responses
* Invalid JSON
* Invalid enum values
* Missing fields
* AI failures

If Gemini cannot produce a valid response, the API returns a safe fallback response rather than failing.

---

# Assumptions

* Transaction history is trusted input.
* Gemini is available through a valid API key.
* Complaint language may be English, Bangla, or mixed.
* One complaint corresponds to one investigation.

---

# Known Limitations

* No database integration
* No authentication layer
* Depends on Gemini API availability
* Uses prompt engineering instead of a fine-tuned model
* Evidence reasoning is limited to the provided transaction history

---

# Future Improvements

* Fine-tuned fraud detection model
* Retrieval-Augmented Generation (RAG)
* Complaint history analysis
* Batch ticket processing
* Streaming responses
* Dashboard for support agents
* Persistent database
* Authentication & rate limiting
* Automatic monitoring and logging

---

# License

This project was developed for the **SUST CSE Carnival 2026 – Codex Community Hackathon** as an educational and demonstration project.
