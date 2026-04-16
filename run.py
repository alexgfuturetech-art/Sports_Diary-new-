import uvicorn
import socket
import os

# Load .env before anything else — this ensures os.getenv works correctly
# for any code that still uses it, and pydantic-settings picks it up too.
from dotenv import load_dotenv
load_dotenv()

# Import settings AFTER load_dotenv so the values are fully resolved
from app.core.config import settings


def get_network_addresses(port: int) -> list:
    """Return all non-loopback network addresses for display."""
    addresses = []
    try:
        hostname = socket.gethostname()
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        for ip in ip_addresses:
            if not ip.startswith("127."):
                addresses.append(f"http://{ip}:{port}/")
    except Exception as e:
        print(f"Could not detect network addresses: {e}")
    return addresses


def get_display_db_url(url: str) -> str:
    """
    Return a safe, human-readable version of the MongoDB URL for the
    startup banner — strips the password so it never appears in logs.
    """
    try:
        if url.startswith("mongodb+srv://"):
            rest = url[len("mongodb+srv://"):]
            proto = "mongodb+srv"
        elif url.startswith("mongodb://"):
            rest = url[len("mongodb://"):]
            proto = "mongodb"
        else:
            return url

        if "@" in rest:
            # Keep only the host part (after the last @)
            host_part = rest[rest.rfind("@") + 1:]
            # Strip query string for brevity
            host_part = host_part.split("?")[0]
            return f"{proto}://<credentials>@{host_part}"
        else:
            return url.split("?")[0]   # local, no creds to hide
    except Exception:
        return "mongodb+srv://***"


if __name__ == "__main__":
    PORT = 8003

    network_addresses = get_network_addresses(PORT)
    display_url = get_display_db_url(settings.MONGODB_URL)

    print("\n" + "=" * 60)
    print("  🚀 BACKEND API WITH MONGODB READY")
    print("=" * 60)
    print(f"\n  ->  Local:   http://localhost:{PORT}/")
    print(f"  ->  Docs:    http://localhost:{PORT}/docs")
    for addr in network_addresses:
        print(f"  ->  Network: {addr}")
    print("\n" + "=" * 60)
    print(f"  💾 Database: {display_url}")
    print(f"  📊 Database Name: {settings.DATABASE_NAME}")
    print("=" * 60 + "\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
    )