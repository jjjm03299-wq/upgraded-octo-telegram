import argparse
import json
import sys
from pathlib import Path
import requests

API_BASE_URL = "https://endearing-moxie-1c521c.netlify.app/api/vpn"
CONFIG_FILE = Path.home() / ".vpn_cli_config.json"
VERSION = "1.0.0"

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def handle_countries(args):
    try:
        res = requests.get(f"{API_BASE_URL}/countries")
        data = res.json()
        if data.get("success"):
            print(f"Total Countries: {data.get('totalCount')}\n")
            for c in data.get("countries", []):
                print(f"[{c['countryCode']}] {c['flag']} {c['countryName']} ({c['serversCount']} servers)")
        else:
            print(f"Error: {data.get('message')}")
    except Exception as e:
        print(f"Request failed: {e}")

def handle_servers(args):
    code = args.country.upper() if args.country else "US"
    try:
        res = requests.get(f"{API_BASE_URL}/servers/{code}")
        data = res.json()
        if data.get("success"):
            print(f"Servers in {data.get('countryName')} {data.get('flag')}:\n")
            for s in data.get("servers", []):
                print(f"- ID: {s['serverId']} | Name: {s['serverName']} | Load: {s['loadPercentage']}% | Latency: {s['latencyMs']}ms")
        else:
            print(f"Error: {data.get('message')}")
    except Exception as e:
        print(f"Request failed: {e}")

def handle_status(args):
    try:
        res = requests.get(f"{API_BASE_URL}/status")
        data = res.json()
        if data.get("success"):
            status = data.get("status", {})
            if status.get("isConnected"):
                target = status.get("connectedTo", {})
                print(f"Status: CONNECTED 🟢")
                print(f"Target: {target.get('countryName')} {target.get('flag')} (Node: {target.get('serverId')})")
                print(f"Assigned IP: {status.get('assignedIp')}")
                print(f"Connected At: {status.get('connectedAt')}")
            else:
                print("Status: DISCONNECTED 🔴")
        else:
            print(f"Error: {data.get('message')}")
    except Exception as e:
        print(f"Request failed: {e}")

def handle_connect(args):
    if args.fastest:
        url = f"{API_BASE_URL}/connect/fastest"
        payload = {"preferredCountries": [args.country.upper()]} if args.country else {}
    else:
        if not args.country:
            print("Error: --country is required when not using --fastest")
            return
        url = f"{API_BASE_URL}/connect"
        payload = {"countryCode": args.country.upper()}

    try:
        res = requests.post(url, json=payload)
        data = res.json()
        if data.get("success"):
            print(f"Success: {data.get('message')}")
        else:
            print(f"Error: {data.get('message')}")
    except Exception as e:
        print(f"Request failed: {e}")

def handle_disconnect(args):
    try:
        res = requests.post(f"{API_BASE_URL}/disconnect", json={})
        data = res.json()
        if data.get("success"):
            print(f"Success: {data.get('message')}")
        else:
            print(f"Error: {data.get('message')}")
    except Exception as e:
        print(f"Request failed: {e}")

def handle_auth(args):
    config = load_config()
    action = args.auth_action

    if action == "register":
        new_pin = input("Enter new PIN: ").strip()
        confirm_pin = input("Confirm new PIN: ").strip()
        if new_pin != confirm_pin:
            print("Error: PINs do not match.")
            return
        if len(new_pin) < 4:
            print("Error: PIN must be at least 4 digits.")
            return
        config["pin"] = new_pin
        config["authenticated"] = True
        save_config(config)
        print("Auth: PIN registered and logged in successfully.")

    elif action == "login":
        pin_input = input("Enter PIN: ").strip()
        if config.get("pin") and config.get("pin") == pin_input:
            config["authenticated"] = True
            save_config(config)
            print("Auth: Login successful.")
        else:
            print("Auth: Invalid PIN.")

    elif action == "logout":
        config["authenticated"] = False
        save_config(config)
        print("Auth: Logged out successfully.")

def handle_pin_login(args):
    config = load_config()
    if not config.get("pin"):
        print("No PIN registered. Please run 'vpn-cli auth register' first.")
        return
    pin_input = input("Enter PIN to continue: ").strip()
    if config.get("pin") == pin_input:
        config["authenticated"] = True
        save_config(config)
        print("Auth: PIN verified. Access granted.")
    else:
        print("Auth: Incorrect PIN.")

def main():
    parser = argparse.ArgumentParser(
        prog="vpn-cli",
        description="CLI tool to interact with the Netlify Express VPN API"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # countries
    subparsers.add_parser("countries", help="List all supported countries")

    # servers
    servers_p = subparsers.add_parser("servers", help="List servers for a country")
    servers_p.add_argument("--country", "-c", required=True, help="ISO country code (e.g. US, DE)")

    # status
    subparsers.add_parser("status", help="Get current VPN status")

    # connect
    connect_p = subparsers.add_parser("connect", help="Connect to VPN")
    connect_p.add_argument("--country", "-c", help="ISO country code")
    connect_p.add_argument("--fastest", action="store_true", help="Connect to the fastest available node")

    # disconnect
    subparsers.add_parser("disconnect", help="Disconnect from VPN")

    # auth
    auth_p = subparsers.add_parser("auth", help="User authentication management")
    auth_p.add_argument("auth_action", choices=["register", "login", "logout"], help="Auth action")

    # pin login
    subparsers.add_parser("pin-login", help="Authenticate with PIN to continue")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    handlers = {
        "countries": handle_countries,
        "servers": handle_servers,
        "status": handle_status,
        "connect": handle_connect,
        "disconnect": handle_disconnect,
        "auth": handle_auth,
        "pin-login": handle_pin_login
    }

    handlers[args.command](args)

if __name__ == "__main__":
    main()
