"""
DOTS AI AGENT - Always-On Autonomous AI Agent Platform
Root launcher delegating to api.app
"""

import os
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from dotenv import load_dotenv

# Ensure workspace .env overrides any conflicting system-wide environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

import uvicorn
from api.app import app

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    port = 8000
    print("\n" + "=" * 72)
    print(" [*] ONE DOTS - Always-On Frontier Intelligence Platform")
    print("     - Conversational Workstation UI : http://127.0.0.1:8000")
    print("     - Live Voice Call Experience   : Hop on a real-time call directly in browser")
    print("     - Autonomous Agent Fleet API   : http://127.0.0.1:8000/api/agents")
    print("     - Integrated Google Gemini AI  : ACTIVE (gemini-3.5-flash-lite / 3.8-flash)")
    print("     - 5 Specialist Dot Archetypes  : Felipe (Blue), Todd (Green), Alfred (Yellow), Jojo (Purple), Sentry (Dev)")
    print("=" * 72 + "\n")
    uvicorn.run("api.app:app", host="127.0.0.1", port=port, reload=True)
