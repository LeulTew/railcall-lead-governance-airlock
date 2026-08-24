"""
Lead Enrichment & ICP Scoring Transform Handler
"""

import time
from typing import Any, Dict, Optional, Tuple

EXECUTIVE_KEYWORDS = {"vp", "vice president", "director", "head", "chief", "c-level", "founder", "co-founder", "partner", "cto", "ceo", "cfo", "cro", "ciso"}
MANAGEMENT_KEYWORDS = {"manager", "lead", "principal", "staff", "senior manager", "architect"}

ENTERPRISE_DOMAINS = {
    "microsoft.com", "google.com", "amazon.com", "apple.com", "meta.com",
    "ibm.com", "oracle.com", "salesforce.com", "adobe.com", "cisco.com",
    "netflix.com", "spotify.com", "uber.com", "airbnb.com", "stripe.com"
}


def calculate_lead_score(data: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
    """
    Computes an Ideal Customer Profile (ICP) lead score from 0 to 100 with sub-score attribution.
    """
    score_breakdown = {
        "domain_authority": 0,
        "title_seniority": 0,
        "company_profile": 0,
        "intent_signal": 0,
    }

    # 1. Domain Authority Score (Max 30)
    domain = data.get("domain", "").lower()
    is_corporate = data.get("is_corporate_domain", False)
    if domain in ENTERPRISE_DOMAINS:
        score_breakdown["domain_authority"] = 30
    elif is_corporate:
        score_breakdown["domain_authority"] = 25
    else:
        score_breakdown["domain_authority"] = 5

    # 2. Seniority Score (Max 30)
    title = data.get("title", "").lower()
    if any(kw in title for kw in EXECUTIVE_KEYWORDS):
        score_breakdown["title_seniority"] = 30
    elif any(kw in title for kw in MANAGEMENT_KEYWORDS):
        score_breakdown["title_seniority"] = 20
    elif title:
        score_breakdown["title_seniority"] = 10
    else:
        score_breakdown["title_seniority"] = 5

    # 3. Company Profile Score (Max 20)
    company = data.get("company", "").strip()
    if company and company.lower() != "unknown":
        score_breakdown["company_profile"] = 20
    else:
        score_breakdown["company_profile"] = 5

    # 4. Message Intent Signal (Max 20)
    message = data.get("message", "").strip()
    if len(message) > 100 or any(intent in message.lower() for intent in ["pricing", "demo", "enterprise", "security", "contract", "seats", "teams"]):
        score_breakdown["intent_signal"] = 20
    elif len(message) > 0:
        score_breakdown["intent_signal"] = 10
    else:
        score_breakdown["intent_signal"] = 5

    total_score = sum(score_breakdown.values())
    return min(100, max(0, total_score)), score_breakdown


def determine_tier_and_routing(score: int, domain: str) -> Dict[str, Any]:
    """
    Determines account tier, estimated deal value, and AE assignment.
    """
    if score >= 80 or domain in ENTERPRISE_DOMAINS:
        return {
            "tier": "Enterprise",
            "estimated_deal_value": 25000,
            "assigned_ae": "Taylor Vance (Enterprise AE)",
            "ae_email": "taylor.vance@company.internal",
            "ae_slack_channel": "#enterprise-deals",
            "priority": "HIGH",
            "pipeline_stage": "qualifiedtobuy",
        }
    elif score >= 50:
        return {
            "tier": "Mid-Market",
            "estimated_deal_value": 10000,
            "assigned_ae": "Jordan Blake (Mid-Market AE)",
            "ae_email": "jordan.blake@company.internal",
            "ae_slack_channel": "#midmarket-leads",
            "priority": "MEDIUM",
            "pipeline_stage": "appointmentscheduled",
        }
    else:
        return {
            "tier": "Growth/SMB",
            "estimated_deal_value": 3500,
            "assigned_ae": "Alex Rivera (Inbound Specialist)",
            "ae_email": "alex.rivera@company.internal",
            "ae_slack_channel": "#inbound-triage",
            "priority": "STANDARD",
            "pipeline_stage": "decisionmakerboughtin",
        }


def score_lead(payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Transform node: Enriches lead data, calculates ICP score, assigns tier and routing AE.
    """
    lead_data = payload.get("data", payload)
    
    # If prior deduplication step marked as duplicate_skipped, pass through
    if payload.get("action") == "duplicate_skipped" or payload.get("is_duplicate"):
        return {
            "status": "ok",
            "action": "duplicate_skipped",
            "summary": "Lead skipped during deduplication; scoring bypassed.",
            "data": lead_data,
            "receipt_meta": {"timestamp": time.time(), "cost_cents": 0},
        }

    score, breakdown = calculate_lead_score(lead_data)
    routing = determine_tier_and_routing(score, lead_data.get("domain", ""))

    deal_name = f"{lead_data.get('company', 'New Lead')} - {routing['tier']} Inbound"

    enriched_profile = {
        **lead_data,
        "lead_score": score,
        "score_breakdown": breakdown,
        "tier": routing["tier"],
        "estimated_deal_value": routing["estimated_deal_value"],
        "assigned_ae": routing["assigned_ae"],
        "ae_email": routing["ae_email"],
        "ae_slack_channel": routing["ae_slack_channel"],
        "priority": routing["priority"],
        "pipeline_stage": routing["pipeline_stage"],
        "deal_name": deal_name,
    }

    return {
        "status": "ok",
        "action": "scored",
        "summary": f"Scored lead {lead_data.get('email')} -> {score}/100 ({routing['tier']}), routed to {routing['assigned_ae']}",
        "data": enriched_profile,
        "receipt_meta": {
            "lead_score": score,
            "tier": routing["tier"],
            "timestamp": time.time(),
            "cost_cents": 0,
        },
    }
