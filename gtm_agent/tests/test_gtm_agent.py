import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"
from gtm_agent.gtm_agent import send_prospect_email


class SendProspectEmailTests(unittest.TestCase):
    def test_blocks_disqualified_prospect(self):
        result = send_prospect_email.func(
            {
                "prospect_id": "LEAD-50001",
                "name": "Priya Nair",
                "email": "priya.nair@brightwaveapps.com",
            },
            "Invitation to Book a Demo",
            "Please book a demo.",
            runtime=None,
            from_rep={"name": "Marco Rossi", "email": "marco.rossi@northpoint.com"},
        )

        self.assertEqual(result, {
            "status": "blocked",
            "reason": "prospect is disqualified",
            "prospect_id": "LEAD-50001",
        })
        self.assertNotIn("message_id", result)

    def test_sends_non_disqualified_prospect(self):
        result = send_prospect_email.func(
            {
                "prospect_id": "LEAD-12853",
                "name": "Omar Okafor",
                "email": "omar.okafor@lakesideanalytics.com",
            },
            "Checking In",
            "Are you available for a conversation?",
            runtime=None,
            from_rep={"name": "Marco Rossi", "email": "marco.rossi@northpoint.com"},
        )

        self.assertEqual(result["status"], "sent")
        self.assertTrue(result["message_id"].startswith("msg-"))
