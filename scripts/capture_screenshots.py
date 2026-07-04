"""Capture dashboard screenshots for README documentation."""

from pathlib import Path

from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
BASE_URL = "http://localhost:8501"

PAGES = [
    ("01-executive-dashboard", "Executive Dashboard"),
    ("02-product-analytics", "Product Analytics"),
    ("03-experimentation-center", "Experimentation Center"),
    ("04-predictive-analytics", "Predictive Analytics"),
    ("05-ai-product-analyst", "AI Product Analyst"),
]


def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE_URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(5000)

        for filename, label in PAGES:
            page.get_by_text(label, exact=True).first.click()
            page.wait_for_timeout(4000)
            path = SCREENSHOTS_DIR / f"{filename}.png"
            page.screenshot(path=str(path), full_page=True)
            print(f"Saved {path}")

        browser.close()


if __name__ == "__main__":
    main()
