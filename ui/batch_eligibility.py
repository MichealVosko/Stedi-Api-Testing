import pandas as pd
import streamlit as st
import uuid
from utils.utils import load_payers
from services.eligibility_service import submit_batch


def render_batch_form():
    st.info("Upload an Excel file with subscriber demographics to check eligibility in batch.")

    template_df = pd.DataFrame(columns=[
        "MemberID", "FirstName", "LastName", "DOB",
        "ProviderName", "ProviderNPI", "ServiceCode",
        "PayerName", "PayerID"
    ])

    template_file = "batch_template.xlsx"
    template_df.to_excel(template_file, index=False)

    st.download_button(
        label="Download template Excel",
        data=open(template_file, "rb"),
        file_name="batch_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

    if not uploaded_file:
        return

    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Failed to read uploaded file: {e}")
        return

    required_columns = [
        "MemberID", "FirstName", "LastName", "DOB",
        "ProviderName", "ProviderNPI", "ServiceCode",
        "PayerName", "PayerID"
    ]

    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        return

    if len(df) > 1000:
        st.error("Maximum batch size is 1000 rows.")
        return

    st.success(f"File uploaded: {uploaded_file.name}")
    st.dataframe(df.head(10))

    payers = load_payers()

    if st.button("Send Batch Request"):
        items = []
        for _, row in df.iterrows():
            payer_id = str(row.get("PayerID", "")).strip()
            payer_name = str(row.get("PayerName", "")).strip().lower()

            if not payer_id:
                match = next((p for p in payers if p["displayName"].lower() == payer_name), None)
                if match:
                    payer_id = match["primaryPayerId"]

            if not payer_id:
                st.warning(f"No valid PayerID for payer '{row.get('PayerName')}', skipping.")
                continue

            first_name = str(row["FirstName"]).replace("`", "'")
            last_name = str(row["LastName"]).replace("`", "'")
            dob_str = pd.to_datetime(row["DOB"]).strftime("%Y%m%d")

            items.append({
                "encounter": {"serviceTypeCodes": [str(row["ServiceCode"])]},
                "provider": {
                    "npi": str(row["ProviderNPI"]),
                    "organizationName": row["ProviderName"],
                },
                "submitterTransactionIdentifier": str(uuid.uuid4()),
                "subscriber": {
                    "dateOfBirth": dob_str,
                    "firstName": first_name,
                    "lastName": last_name,
                    "memberId": str(row["MemberID"]),
                },
                "tradingPartnerServiceId": payer_id,
            })

        if not items:
            st.error("No valid rows to send.")
            return

        with st.spinner("Submitting batch to Stedi..."):
            response = submit_batch(items)

        if "error" in response:
            st.error(f"Batch submission failed: {response['error']}")
            return

        batch_id = response.get("batchId", "N/A")
        st.success(f"Batch submitted successfully. Batch ID: {batch_id}")
        st.info("Results will be available asynchronously. Retrieve them later using the Poll Batch Results section.")
