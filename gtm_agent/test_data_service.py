import importlib.util
import sys
import types
from pathlib import Path


package = types.ModuleType("gtm_agent")
package.__path__ = [str(Path(__file__).parent)]
sys.modules["gtm_agent"] = package

records_spec = importlib.util.spec_from_file_location(
    "gtm_agent.gtm_records", Path(__file__).with_name("gtm_records.py")
)
records = importlib.util.module_from_spec(records_spec)
sys.modules["gtm_agent.gtm_records"] = records
records_spec.loader.exec_module(records)

data_service_spec = importlib.util.spec_from_file_location(
    "gtm_agent.data_service", Path(__file__).with_name("data_service.py")
)
data_service = importlib.util.module_from_spec(data_service_spec)
sys.modules["gtm_agent.data_service"] = data_service
data_service_spec.loader.exec_module(data_service)


def test_update_prospect_info_persists_tech_stack_and_invalidates_profile():
    prospect_id = "TEST-PROSPECT"
    data_service.PROSPECTS[prospect_id] = {"tech_stack": ["ExistingTech"]}
    data_service._PROFILES[prospect_id] = {"tech_stack": ["ExistingTech"]}

    try:
        result = data_service.update_prospect_info(prospect_id, "NewTech")

        assert result == {
            "updated": True,
            "found": True,
            "tech_stack": ["ExistingTech", "NewTech"],
        }
        assert "NewTech" in data_service.fetch_tech_stack(prospect_id)
        profile = data_service.get_profile_from_db(prospect_id)["prospect_profile"]
        assert profile is None or "NewTech" in profile["tech_stack"]
    finally:
        data_service.PROSPECTS.pop(prospect_id, None)
        data_service._PROFILES.pop(prospect_id, None)
