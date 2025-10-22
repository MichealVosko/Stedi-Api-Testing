import streamlit as st
import json
import datetime
from services.eligibility_service import check_eligibility, build_request_body
from utils.utils import load_service_type_codes, load_payers


def render_form():
    st.header("Payer Information")

    payers = load_payers()
    payer_names = sorted([p["displayName"] for p in payers])
    payer_name = st.selectbox("Payer *", ["Select a Payer"] + payer_names)

    # Automatically fill payer_id when payer is selected
    auto_payer_id = ""
    if payer_name != "Select a Payer":
        auto_payer_id = next(
            (p["primaryPayerId"] for p in payers if p["displayName"] == payer_name),
            ""
        )

    # Allow manual override (user can still type their own)
    payer_id = st.text_input(
        "Payer ID",
        value=auto_payer_id,
        placeholder="Enter or confirm Payer ID",
    )

    st.header("Encounter")
    options = load_service_type_codes()
    service_type_code = st.selectbox(
        "Service type code *",
        options,
        index = options.index("30: Health Benefit Plan Coverage")
    )

    st.header("Subscriber")
    member_id = st.text_input("Member ID *")
    c1, c2, c3 = st.columns(3)
    with c1:
        first_name = st.text_input("First name *")
    with c2:
        middle_name = st.text_input("Middle name")
    with c3:
        last_name = st.text_input("Last name *")

    c1, c2 = st.columns(2)
    with c1:
        dob = st.date_input("Date of birth *", min_value=datetime.date(1900, 1, 1)).strftime("%Y-%m-%d")
    with c2:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    st.header("Provider")
    c1, c2 = st.columns(2)
    with c1:
        provider_name = st.text_input("Provider name *", placeholder="Enter Provider Name")
    with c2:
        provider_npi = st.text_input("Provider NPI *")

    if st.button("Check Eligibility"):
        if not payer_id:
            st.error("Payer ID is required.")
            return

        # Prepare form data
        form_data = {
            "payer_id": payer_id.strip(),
            "service_type_code": service_type_code.split(":")[0].strip(),
            "member_id": member_id.strip(),
            "first_name": first_name.strip(),
            "middle_name": middle_name.strip(),
            "last_name": last_name.strip(),
            "dob": dob,
            "gender": gender,
            "provider_name": provider_name.strip(),
            "provider_npi": provider_npi.strip(),
        }

        st.subheader("Request Body")
        st.json(build_request_body(form_data))
        print(build_request_body(form_data))

        with st.spinner("Checking eligibility..."):
            response = check_eligibility(form_data)

        st.subheader("Response Summary")

        try:
            if isinstance(response, str):
                response = json.loads(response)

            # === Meta Section ===
            with st.expander("Meta Information", expanded=False):
                meta = response.get("meta", {})
                st.write(f"**Sender ID:** {meta.get('senderId')}")
                st.write(f"**Submitter ID:** {meta.get('submitterId')}")
                st.write(f"**Trace ID:** {meta.get('traceId')}")

            # === Provider Information ===
            with st.expander("Provider Information", expanded=False):
                provider = response.get("provider", {})
                st.write(f"**Provider Name:** {provider.get('providerName')}")
                st.write(f"**Organization:** {provider.get('providerOrgName')}")
                st.write(f"**NPI:** {provider.get('npi')}")

            # === Subscriber Information ===
            with st.expander("Subscriber Information", expanded=False):
                sub = response.get("subscriber", {})
                cols = st.columns(2)
                cols[0].write(f"**Name:** {sub.get('firstName')} {sub.get('lastName')}")
                cols[0].write(f"**Gender:** {sub.get('gender')}")
                cols[0].write(f"**DOB:** {sub.get('dateOfBirth')}")
                cols[1].write(f"**Member ID:** {sub.get('memberId')}")
                cols[1].write(f"**Group #:** {sub.get('groupNumber')}")
                address = sub.get("address", {})
                st.write(f"**Address:** {address.get('address1')}, {address.get('city')}, {address.get('state')} {address.get('postalCode')}")

            # === Payer Information ===
            with st.expander("Payer Information", expanded=False):
                payer = response.get("payer", {})
                st.write(f"**Name:** {payer.get('name')}")
                st.write(f"**Tax ID:** {payer.get('federalTaxpayersIdNumber')}")
                contacts = payer.get("contactInformation", {}).get("contacts", [])
                if contacts:
                    st.subheader("Contacts")
                    for c in contacts:
                        st.write(f"- {c.get('communicationMode')}: {c.get('communicationNumber')}")

            # === Plan Information ===
            with st.expander("Plan Information", expanded=False):
                plan = response.get("planInformation", {})
                plan_dates = response.get("planDateInformation", {})
                st.write(f"**Group #:** {plan.get('groupNumber')}")
                st.write(f"**Description:** {plan.get('groupDescription')}")
                st.write(f"**Plan Start:** {plan_dates.get('planBegin')}")
                st.write(f"**Plan End:** {plan_dates.get('planEnd')}")
                st.write(f"**Eligibility Start:** {plan_dates.get('eligibilityBegin')}")

            # === Plan Status ===
            import pandas as pd
            with st.expander("Plan Status Details", expanded=False):
                plan_status = response.get("planStatus", [])
                if plan_status:
                    st.dataframe(pd.DataFrame(plan_status))

            # === Benefits Information ===
            with st.expander("Benefits Information", expanded=True):
                benefits = response.get("benefitsInformation", [])
                if benefits:
                    df = pd.DataFrame(benefits)
                    df["serviceTypeCodes"] = df["serviceTypeCodes"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
                    df["serviceTypes"] = df["serviceTypes"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
                    st.dataframe(df[["name", "coverageLevel", "benefitAmount", "benefitPercent", "inPlanNetworkIndicator", "serviceTypes"]].fillna(""))

            # === Errors ===
            errors = response.get("errors", [])
            if errors:
                st.error("Errors found in response:")
                st.json(errors)

        except Exception as e:
            st.error(f"Failed to parse or display response: {e}")
            st.json(response)


