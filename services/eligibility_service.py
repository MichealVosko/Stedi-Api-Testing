import requests
import logging
from config.settings import (
    ELIGIBILITY_URL,
    BATCH_ELIGIBILITY_URL,
    POLL_URL,
    STEDI_API_KEY,
)

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": STEDI_API_KEY,
    "Content-Type": "application/json",
}


def build_request_body(form_data):
    return {
        "encounter": {"serviceTypeCodes": [form_data["service_type_code"]]},
        "provider": {
            "npi": form_data["provider_npi"],
            "organizationName": form_data["provider_name"],
        },
        "subscriber": {
            "dateOfBirth": form_data["dob"].replace("-", ""),
            "firstName": form_data["first_name"],
            "lastName": form_data["last_name"],
            "memberId": form_data["member_id"],
        },
        "tradingPartnerServiceId": form_data["payer_id"],
    }


def check_eligibility(form_data):
    body = build_request_body(form_data)
    try:
        resp = requests.post(ELIGIBILITY_URL, json=body, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"Eligibility check failed: {e}")
        return {"error": str(e)}


def submit_batch(items):
    body = {
        "items": items,
        "name": "batch-submission",
    }

    try:
        resp = requests.post(BATCH_ELIGIBILITY_URL, json=body, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.error(f"Batch submission failed: {e}")
        return {"error": str(e)}

def poll_batch_results(batch_id, auto_paginate=True, page_size=100):
    params = {"batchId": batch_id, "pageSize": page_size}
    all_items, next_token = [], None

    while True:
        if next_token:
            params["pageToken"] = next_token

        try:
            resp = requests.get(POLL_URL, headers=HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.error(f"Polling failed: {e}")
            return {"error": str(e)}

        items = data.get("items", [])
        all_items.extend(items)

        next_token = data.get("nextPageToken")
        if not auto_paginate or not next_token:
            break

    return {"items": all_items}
