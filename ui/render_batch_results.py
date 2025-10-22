import io
import pandas as pd
import streamlit as st
from services.eligibility_service import poll_batch_results

def render_batch_results():
    st.header("Retrieve Batch Eligibility Results")

    batch_id = st.text_input("Enter Batch ID")
    auto_paginate = st.checkbox("Auto-fetch all pages", value=True)

    if st.button("Fetch Results"):
        if not batch_id:
            st.error("Batch ID is required.")
            return

        with st.spinner("Polling Stedi API for results..."):
            data = poll_batch_results(batch_id, auto_paginate, page_size=100)

        if "error" in data:
            st.error(f"Request failed: {data['error']}")
            return

        all_items = data.get("items", [])
        if not all_items:
            st.warning("No completed results found yet. Try again later.")
            return

        st.success(f"Total results retrieved: {len(all_items)}")

        flat_records = []
        for item in all_items:
            subscriber = item.get("subscriber", {})
            provider = item.get("provider", {})
            eligibility_info = item.get("benefitsInformation", [])
            first_benefit = eligibility_info[0] if eligibility_info else {}

            flat_records.append({
                "BatchID": item.get("batchId"),
                "TransactionID": item.get("submitterTransactionIdentifier"),
                "MemberID": subscriber.get("memberId"),
                "FirstName": subscriber.get("firstName"),
                "LastName": subscriber.get("lastName"),
                "DOB": subscriber.get("dateOfBirth"),
                "Provider": provider.get("organizationName"),
                "ServiceType": first_benefit.get("serviceTypeCode"),
                "CoverageStatus": first_benefit.get("code"),
                "Description": first_benefit.get("description"),
            })

        df = pd.DataFrame(flat_records)
        st.dataframe(df)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Results")
        buffer.seek(0)

        st.download_button(
            label="Download Results Excel",
            data=buffer,
            file_name=f"{batch_id}_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
