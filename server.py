#!/usr/bin/env python3
"""
Lightweight Inbound Webhook Ingestion Server for RailCall Lead Governance Airlock
Accepts live HTTP POST webhooks from landing pages/forms, executes the Airlock, and returns signed receipts.
"""

import http.server
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from handlers.validate import validate_lead, parse_inbound_payload
from handlers.dedup import check_existing_lead
from handlers.enrich import score_lead
from handlers.airlock import stage_airlock_preview
from handlers.hubspot import create_deal
from handlers.slack import post_lead_alert
from handlers.airtable import log_event
from handlers.crypto_receipt import mint_signed_receipt, verify_receipt
from handlers.budget import BudgetLedger

PORT = int(os.getenv("PORT", 8899))


class LeadWebhookHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "lead-governance-airlock", "version": "1.0.0"}).encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>RailCall Lead Governance Airlock</title></head>
        <body style="font-family: monospace; padding: 2rem; background: #0f172a; color: #f8fafc;">
            <h2>RailCall Lead Governance Airlock — Webhook Receiver</h2>
            <p>POST JSON lead payloads to <code>/webhook/lead</code></p>
            <p>Status: <strong>Active & Governed</strong></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        if self.path != "/webhook/lead":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Endpoint not found"}')
            return

        content_length = int(self.headers.get("Content-Length", 0))
        content_type = self.headers.get("Content-Type", "application/json")
        raw_body = self.rfile.read(content_length)

        try:
            parsed_payload = parse_inbound_payload(raw_body, content_type=content_type)
        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Failed to parse payload: {str(e)}"}).encode())
            return

        # Execute Airlock Pipeline
        budget = BudgetLedger(max_spend_cents=500)
        val = validate_lead(parsed_payload)

        if val["status"] != "ok":
            self.send_response(422)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "rejected", "error": val["error"]}).encode())
            return

        dedup = check_existing_lead(val)
        if dedup.get("action") == "duplicate_skipped":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "duplicate_skipped", "summary": dedup["summary"]}).encode())
            return

        enrich = score_lead(dedup)
        profile = enrich["data"]
        airlock = stage_airlock_preview(enrich)

        dry_run = os.getenv("RC_DRY_RUN", "true").lower() in {"true", "1", "yes"}

        hub_res = create_deal(enrich, context={"dry_run": dry_run})
        slack_res = post_lead_alert(hub_res, context={"dry_run": dry_run})
        airtable_res = log_event(slack_res, context={"dry_run": dry_run})

        mutations = {
            "hubspot_deal": hub_res["action"],
            "slack_alert": slack_res["action"],
            "airtable_log": airtable_res["action"],
        }

        receipt = mint_signed_receipt(
            workflow_slug="leultew/lead-governance-airlock",
            version="1.0.0",
            lead_data=profile,
            mutations=mutations,
            spend_cents=budget.current_spend_cents,
            max_spend_cents=budget.max_spend_cents,
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "receipt": receipt}, indent=2).encode())


def run_server(port: int = PORT):
    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), LeadWebhookHandler)
    print(f"[*] RailCall Lead Governance Webhook Server listening on http://0.0.0.0:{port}")
    print(f"[*] Health endpoint: http://localhost:{port}/health")
    print(f"[*] Inbound lead webhook: POST http://localhost:{port}/webhook/lead")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server.")
        server.server_close()


if __name__ == "__main__":
    run_server()
