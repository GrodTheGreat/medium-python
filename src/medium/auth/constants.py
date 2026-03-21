import os
import sys

from dotenv import load_dotenv

load_dotenv()

CSRF_BYTES = 32
CSRF_KEY = "Medium-CSRF-Token"
CSRF_MAX_AGE = 60 * 5  # 5 min for testing
CSRF_SIGNING_KEY = os.getenv("CSRF_SIGNING_KEY")
SEPARATOR = "."
SESSION_BYTES = 64
SESSION_KEY = "Medium-Session-Key"
SESSION_MAX_AGE = 60 * 5  # 5 minutes for testing
XSRF_INPUT = "xsrf"
XSRF_KEY = "Medium-XSRF-Token"


if CSRF_SIGNING_KEY is None:
    print("csrf signing key env not set")
    sys.exit(1)
