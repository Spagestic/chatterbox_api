def check_api_health():
    import requests
    import os
    HEALTH_ENDPOINT = os.getenv("HEALTH_ENDPOINT", "YOUR-MODAL-ENDPOINT-URL/health")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return f"✅ API Status: {data.get('status', 'Unknown')} | Model Loaded: {data.get('model_loaded', False)}"
        else:
            return f"⚠️ API returned status code: {response.status_code}"
    except Exception as e:
        return f"❌ API Health Check Failed: {str(e)}"