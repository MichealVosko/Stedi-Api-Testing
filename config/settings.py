import os
from dotenv import load_dotenv

load_dotenv()

STEDI_API_KEY = os.getenv("STEDI_API_KEY")
ELIGIBILITY_URL = os.getenv("ELIGIBILITY_URL")
BATCH_ELIGIBILITY_URL = os.getenv("BATCH_ELIGIBILITY_URL")
POLL_URL = os.getenv("POLL_URL")

if not ELIGIBILITY_URL:
    raise ValueError("ELIGIBILITY_URL not found in .env")
if not STEDI_API_KEY:
    raise ValueError("STEDI_API_KEY not found in .env")
if not POLL_URL:
    raise ValueError("POLL_URL not found in .env")
