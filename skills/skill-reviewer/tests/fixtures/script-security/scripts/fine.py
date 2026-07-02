"""Fixture script: reads an environment variable but never makes a network
call -- must NOT trip the script-security env+network check."""
import os

token = os.environ.get("API_TOKEN")
print("token loaded, no network call")
