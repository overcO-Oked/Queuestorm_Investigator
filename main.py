import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel

# ===========================
# Load environment variables
# ===========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

class Transaction(BaseModel):
    transaction_id: str
    timestamp: str
    type: str
    amount: float
    counterparty: str
    status: str


class Ticket(BaseModel):
    ticket_id: str
    complaint: str

    language: str
    channel: str
    user_type: str
    campaign_context: str

    transaction_history: list[Transaction]


@app.get("/")
def root():
    return {"message": "Hello, SUST Hackathon!"}


@app.post("/analyze-ticket")
def analyze(ticket: Ticket):

    prompt = f"""
You are an AI fintech complaint investigation assistant.

Analyze ONE customer complaint.

RULES:
- Only use the complaint and transaction history.
- Never invent transactions.
- Never ask for OTP, PIN, password, or CVV.
- Never promise refunds.
- Never claim the investigation is complete.
- If evidence is weak, use "insufficient_data".
- Return ONLY JSON.
- No markdown.
- No explanations.

IMPORTANT SAFETY RULES:

- Never ask the customer for OTP, PIN, password, CVV, secret code or verification code.
- Never ask the customer to reveal bank credentials.
- Never promise refunds.
- Never promise reversals.
- Never promise account recovery.
- Never promise account unblocking.
- Never claim that funds will definitely be returned.
- Never say the investigation is complete.
- If uncertain, recommend human review.

ALLOWED VALUES

case_type:
- wrong_transfer
- payment_failed
- refund_request
- duplicate_payment
- merchant_settlement_delay
- agent_cash_in_issue
- phishing_or_social_engineering
- other

evidence_verdict:
- consistent
- inconsistent
- insufficient_data

severity:
- low
- medium
- high
- critical

department:
- customer_support
- dispute_resolution
- payments_ops
- merchant_operations
- agent_operations
- fraud_risk

Ticket ID:
{ticket.ticket_id}

Language:
{ticket.language}

Channel:
{ticket.channel}

User Type:
{ticket.user_type}

Campaign Context:
{ticket.campaign_context}

Complaint:
{ticket.complaint}

Transaction History:
{json.dumps([tx.model_dump() for tx in ticket.transaction_history], indent=2,)}

Return EXACTLY this JSON:

{{
  "ticket_id": "{ticket.ticket_id}",
  "relevant_transaction_id": "",
  "evidence_verdict": "",
  "case_type": "",
  "severity": "",
  "department": "",
  "agent_summary": "",
  "recommended_next_action": "",
  "customer_reply": "",
  "human_review_required": false,
  "confidence": 0.0,
  "reason_codes": []
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        text = response.text.strip()

        # Remove markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

            if text.startswith("json"):
                text = text[4:].strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("Gemini returned invalid JSON.")

        if not isinstance(result, dict):
            raise ValueError("Gemini did not return a JSON object.")

        # ----------------------------
        # Force correct ticket ID
        # ----------------------------
        result["ticket_id"] = ticket.ticket_id

        # ----------------------------
        # Allowed values
        # ----------------------------

        allowed_case_types = {
            "wrong_transfer",
            "payment_failed",
            "refund_request",
            "duplicate_payment",
            "merchant_settlement_delay",
            "agent_cash_in_issue",
            "phishing_or_social_engineering",
            "other",
        }

        allowed_evidence = {
            "consistent",
            "inconsistent",
            "insufficient_data",
        }

        allowed_severity = {
            "low",
            "medium",
            "high",
            "critical",
        }

        allowed_departments = {
            "customer_support",
            "dispute_resolution",
            "payments_ops",
            "merchant_operations",
            "agent_operations",
            "fraud_risk",
        }

        if result.get("case_type") not in allowed_case_types:
            result["case_type"] = "other"

        if result.get("evidence_verdict") not in allowed_evidence:
            result["evidence_verdict"] = "insufficient_data"

        if result.get("severity") not in allowed_severity:
            result["severity"] = "medium"

        if result.get("department") not in allowed_departments:
            result["department"] = "customer_support"

        # ----------------------------
        # Default values
        # ----------------------------

        defaults = {
            "relevant_transaction_id": None,
            "agent_summary": "",
            "recommended_next_action": "Manual review recommended.",
            "customer_reply": "Thank you for contacting us. We are reviewing your complaint.",
            "human_review_required": True,
            "confidence": 0.5,
            "reason_codes": [],
        }

        required_fields = {
            "ticket_id",
            "relevant_transaction_id",
            "evidence_verdict",
            "case_type",
            "severity",
            "department",
            "agent_summary",
            "recommended_next_action",
            "customer_reply",
            "human_review_required",
            "confidence",
            "reason_codes",
        }

        for key, value in defaults.items():
            result.setdefault(key, value)

        # SAFETY CHECKS

        forbidden_words = {
            "otp",
            "pin",
            "password",
            "cvv",
            "verification code",
            "secret code",
            "ওটিপি",
            "পিন",
            "পাসওয়ার্ড",
            "গোপন পিন",
        }

        forbidden_promises = {
            "refund approved",
            "refund guaranteed",
            "refund will be processed",
            "money will be returned",
            "your money will be returned",
            "funds will be returned",
            "we will recover your money",
            "account unblocked",
            "account has been unblocked",
            "your account is unblocked",
            "reversal completed",
            "transaction reversed",
            "ফেরত",
            "রিফান্ড",
            "আপনার টাকা ফেরত",
            "অ্যাকাউন্ট আনব্লক",
        }

        # Customer reply safety
        reply = result.get("customer_reply", "")
        reply_lower = reply.lower()

        if any(word in reply_lower for word in forbidden_words) or \
           any(phrase in reply_lower for phrase in forbidden_promises):
            result["customer_reply"] = (
                "Thank you for contacting us. "
                "For your security, never share your OTP, PIN, CVV, password, or any verification code. "
                "Our support team is reviewing your complaint. "
                "Any resolution will follow the organization's policies after review."
            )

        # Recommended action safety
        action = result.get("recommended_next_action", "")
        action_lower = action.lower()

        if any(phrase in action_lower for phrase in forbidden_promises):
            result["recommended_next_action"] = (
                "Review the complaint according to company policy and escalate to the appropriate department if necessary."
            )

        # Force human review for high-risk cases
        value = result.get("human_review_required", True)

        if isinstance(value, str):
            result["human_review_required"] = value.lower() == "true"
        else:
            result["human_review_required"] = bool(value)

        if result["case_type"] in {
            "phishing_or_social_engineering",
            "wrong_transfer",
            "payment_failed",
        }:
            result["human_review_required"] = True

        # Clamp confidence to [0, 1]
        try:
            result["confidence"] = max(
                0.0,
                min(1.0, float(result.get("confidence", 0.5)))
            )
        except Exception:
            result["confidence"] = 0.5
        
        reason_codes = result.get("reason_codes", [])

        if not isinstance(reason_codes, list):
            reason_codes = []

        result["reason_codes"] = reason_codes

        return result

    except Exception as e:
        print(f"Gemini error: {e}")

        return {
                "ticket_id": ticket.ticket_id,
                "relevant_transaction_id": None,
                "evidence_verdict": "insufficient_data",
                "case_type": "other",
                "severity": "medium",
                "department": "customer_support",
                "agent_summary": "Unable to analyze the complaint automatically.",
                "recommended_next_action": "Manual review required.",
                "customer_reply": "Thank you for contacting us. We are reviewing your complaint.",
                "human_review_required": True,
                "confidence": 0.0,
                "reason_codes": ["GEMINI_ERROR"],
            }
