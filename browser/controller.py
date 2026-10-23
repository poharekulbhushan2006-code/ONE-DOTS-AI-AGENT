"""
ONE: Always-On Autonomous AI Agent System
Headless Autonomous Browser Subsystem (Playwright)
"""

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from config.settings import settings


class AgentBrowser:
    """
    Dedicated autonomous browser controller for an agent.
    Maintains persistent cookies/sessions, takes visual screenshots,
    and extracts page semantic structure.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.session_dir = settings.BROWSER_SESSIONS_DIR / agent_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "storage_state.json"

    async def navigate_and_extract(
        self,
        url: str,
        take_screenshot: bool = True,
        wait_seconds: int = 2,
    ) -> Dict[str, Any]:
        """
        Navigates to URL, preserves session state, extracts markdown-ready text,
        title, links, and captures a full-page screenshot.
        """
        async with async_playwright() as p:
            # Launch Chromium with anti-bot detection flags
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            # Load existing storage state if available
            context_kwargs = {
                "viewport": {"width": 1280, "height": 800},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            }
            if self.state_file.exists():
                context_kwargs["storage_state"] = str(self.state_file)

            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()

            screenshot_filename = None
            screenshot_path = None

            try:
                # Go to URL with realistic timeout
                response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(wait_seconds)

                title = await page.title()

                # Extract cleaned text
                content_text = await page.evaluate("""
                    () => {
                        // Remove script and style elements
                        const clone = document.body.cloneNode(true);
                        const toRemove = clone.querySelectorAll('script, style, noscript, svg, iframe');
                        toRemove.forEach(el => el.remove());
                        return clone.innerText || "";
                    }
                """)

                # Extract top links
                links = await page.evaluate("""
                    () => {
                        const anchors = Array.from(document.querySelectorAll('a[href]'));
                        return anchors
                            .map(a => ({ text: a.innerText.trim(), href: a.href }))
                            .filter(a => a.text.length > 2 && a.href.startsWith('http'))
                            .slice(0, 15);
                    }
                """)

                # Capture screenshot
                if take_screenshot:
                    shot_id = f"{self.agent_id}_{int(datetime.now(timezone.utc).timestamp())}_{str(uuid.uuid4())[:4]}.png"
                    shot_dest = settings.SCREENSHOTS_DIR / shot_id
                    await page.screenshot(path=str(shot_dest), full_page=False)
                    screenshot_filename = shot_id
                    screenshot_path = str(shot_dest)

                # Persist session cookies & localStorage
                await context.storage_state(path=str(self.state_file))

                # Truncate content to avoid overwhelming context
                clean_text = " ".join(content_text.split())
                if len(clean_text) > 4000:
                    clean_text = clean_text[:4000] + "... [Content Truncated]"

                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "status_code": response.status if response else 200,
                    "content": clean_text,
                    "links": links,
                    "screenshot_filename": screenshot_filename,
                    "screenshot_path": screenshot_path,
                }

            except Exception as e:
                return {
                    "success": False,
                    "url": url,
                    "error": str(e),
                    "content": "",
                    "links": [],
                    "screenshot_filename": None,
                }
            finally:
                await context.close()
                await browser.close()


def inspect_url(agent_id: str, url: str, take_screenshot: bool = True) -> Dict[str, Any]:
    """Synchronous wrapper for inspect_url."""
    browser = AgentBrowser(agent_id)
    return asyncio.run(browser.navigate_and_extract(url, take_screenshot=take_screenshot))
