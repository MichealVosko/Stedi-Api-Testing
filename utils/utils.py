from pathlib import Path
import json

service_type_codes_path = Path("data/service_type_codes.json")
payers_path = Path("data/payers.json")
def load_service_type_codes():
    with open(service_type_codes_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [f"{k}: {v}" for k, v in data.items()]

def load_payers():
    with open(payers_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Only show those that support eligibility
    return [
        {
            "displayName": p["displayName"],
            "primaryPayerId": p["primaryPayerId"],
            "eligibility": p["transactionSupport"].get("eligibilityCheck") == "SUPPORTED",
        }
        for p in data["items"]
        if p["transactionSupport"].get("eligibilityCheck") == "SUPPORTED"
    ]