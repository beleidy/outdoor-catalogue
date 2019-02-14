import requests


def get_jwks_keys():
    GOOGLE_DISCOVERY_URI = "https://accounts.google.com/.well-known/openid-configuration"
    response = requests.get(GOOGLE_DISCOVERY_URI)
    response_json = response.json()
    jwks_uri = response_json.get("jwks_uri", None)
    if jwks_uri is not None:
        response = requests.get(jwks_uri)
        response_json = response.json()
    keys = response_json.get("keys", None)
    return keys
