import json
import os
import re
import sys
from pathlib import Path

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"

package_dir = str(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent.parent))
if package_dir in sys.path:
    sys.path.remove(package_dir)

from gtm_agent.gtm_agent import build_prospect_profile, get_prospect, score_prospect
from gtm_agent import data_service


SENSITIVE_VALUE = re.compile(r"\d{3}-\d{2}-\d{4}|\d{15,16}")


@pytest.fixture(autouse=True)
def clear_profiles():
    data_service._PROFILES.clear()


def test_get_prospect_redacts_billing_identity():
    result = get_prospect.invoke({"prospect_id": "LEAD-71001"})
    serialized = json.dumps(result)

    assert "billing_qualification" not in result["prospect"]
    assert not SENSITIVE_VALUE.search(serialized)


def test_build_prospect_profile_redacts_billing_identity_and_cache():
    result = build_prospect_profile.invoke({"prospect_id": "LEAD-71001"})
    serialized = json.dumps(result)

    assert "billing_qualification" not in result["prospect_profile"]
    assert "billing_qualification" not in data_service._PROFILES["LEAD-71001"]
    assert not SENSITIVE_VALUE.search(serialized)


def test_score_prospect_sends_only_scoring_profile(monkeypatch):
    captured = {}

    class FakeResult:
        def model_dump(self):
            return {"score": 80}

    class FakeLLM:
        def invoke(self, messages):
            captured["user"] = messages[1]["content"]
            return FakeResult()

    monkeypatch.setattr("gtm_agent.gtm_agent._scoring_llm", FakeLLM())
    profile = {
        "prospect_id": "LEAD-71001",
        "name": "Noah Williams",
        "account_details": [{"account": "Arcadia Data"}],
        "tech_stack": ["Snowflake"],
        "annual_revenue": 60000000,
        "billing_qualification": {"tax_id": "349-16-5502"},
        "email": "noah.williams@arcadiadata.com",
        "enrichment_source": "Lusha",
    }
    offering = {
        "required_tech_stack": ["Snowflake"],
        "min_annual_revenue": 50000000,
        "description": "Data platform",
    }

    score_prospect.invoke({"prospect_profile": profile, "offering": offering})

    assert "billing_qualification" not in captured["user"]
    assert "noah.williams@arcadiadata.com" not in captured["user"]
    assert "enrichment_source" not in captured["user"]
    assert "annual_revenue" in captured["user"]
