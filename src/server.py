
#!/usr/bin/env python3
"""Server script to run the FastAPI application."""

from bookingagent_api import start_server

if __name__ == "__main__":
    print("Starting Booking Assistant API server on port 5000...")
    start_server(host="0.0.0.0", port=5000)
