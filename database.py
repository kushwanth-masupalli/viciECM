import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL is missing")

if not SUPABASE_PUBLISHABLE_KEY:
    raise Exception("SUPABASE_PUBLISHABLE_KEY is missing")

if not SUPABASE_SECRET_KEY:
    raise Exception("SUPABASE_SECRET_KEY is missing")

# Used only for signup / signin (anon/publishable key)
supabase_auth = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)

# Used for all DB operations (service-role/secret key)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)