import streamlit as st
import pandas as pd
import numpy as np
from services.eligibility_service import build_request_body, check_eligibility


def render_batch_realtime():
    st.header("Batch Eligibility Check")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("Preview of uploaded file:", df.head())

        if st.button("Run Eligibility Check"):
            results = []

            for idx, row in df.iterrows():
                try:
                    # Build request for each row
                    request_body = build_request_body(
                        member_id=row["MemberID"],
                        first_name=row["FirstName"],
                        last_name=row["LastName"],
                        dob=row["DOB"],
                        provider_name=row["ProviderName"],
                        provider_npi=row["ProviderNPI"],
                        service_code=row["ServiceCode"],
                        payer_name=row["PayerName"],
                        payer_id=row["PayerID"]
                    )

                    # Call API
                    response = check_eligibility(request_body)

                    # Parse the response safely
                    benefit_info = response.get("benefitsInformation", [])
                    deductible = np.nan
                    copay = np.nan
                    plan_name = np.nan
                    active_date = np.nan
                    termination_date = np.nan
                    eligibility_status = np.nan
                    comment = np.nan

                    for item in benefit_info:
                        if item.get("name") == "Deductible":
                            deductible = item.get("benefitAmount", np.nan)
                        if item.get("name") == "Co-Payment":
                            copay = item.get("benefitAmount", np.nan)
                        if item.get("name") == "Active Coverage":
                            eligibility_status = "Active"
                            plan_name = item.get("planCoverage", np.nan)
                        if "Active" in item.get("name", "") and "Terminated" in item.get("name", ""):
                            eligibility_status = "Inactive"

                    # Build result row
                    results.append({
                        "DOS": np.nan,
                        "Patient's Name": f"{row['FirstName']} {row['LastName']}",
                        "DOB": row["DOB"],
                        "Primary Insurance Name": row["PayerName"],
                        "Member ID": row["MemberID"],
                        "Plan Name & Type": plan_name,
                        "Remaining Deductible": deductible,
                        "Co-pay": copay,
                        "Referral Required": np.nan,
                        "Active Date": active_date,
                        "Termination Date": termination_date,
                        "Outstanding Balance": np.nan,
                        "Eligibility Status": eligibility_status,
                        "Secondary Insurance Name": np.nan,
                        "Member ID (Secondary)": np.nan,
                        "Active Date (Secondary)": np.nan,
                        "Termination Date (Secondary)": np.nan,
                        "Eligibility Status (Secondary)": np.nan,
                        "Comment": comment
                    })

                except Exception as e:
                    results.append({
                        "DOS": np.nan,
                        "Patient's Name": f"{row['FirstName']} {row['LastName']}",
                        "DOB": row["DOB"],
                        "Primary Insurance Name": row["PayerName"],
                        "Member ID": row["MemberID"],
                        "Plan Name & Type": np.nan,
                        "Remaining Deductible": np.nan,
                        "Co-pay": np.nan,
                        "Referral Required": np.nan,
                        "Active Date": np.nan,
                        "Termination Date": np.nan,
                        "Outstanding Balance": np.nan,
                        "Eligibility Status": "Error",
                        "Secondary Insurance Name": np.nan,
                        "Member ID (Secondary)": np.nan,
                        "Active Date (Secondary)": np.nan,
                        "Termination Date (Secondary)": np.nan,
                        "Eligibility Status (Secondary)": np.nan,
                        "Comment": str(e)
                    })

            # Convert results to DataFrame
            result_df = pd.DataFrame(results)

            # Display and download link
            st.write("Processed Results:", result_df)
            output_path = "batch_results.xlsx"
            result_df.to_excel(output_path, index=False)
            st.download_button("Download Results", open(output_path, "rb"), file_name="eligibility_results.xlsx")
