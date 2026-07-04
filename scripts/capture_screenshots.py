"""Capture dashboard screenshots for README documentation."""

from pathlib import Path

from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
BASE_URL = "http://localhost:8501"

PAGES = [
    {
        "file": "01-executive-dashboard",
        "label": "Executive Dashboard",
        "wait_for": "Active Users Trend",
    },
    {
        "file": "02-product-analytics",
        "label": "Product Analytics",
        "wait_for": "Growth & Engagement",
    },
    {
        "file": "03-experimentation-center",
        "label": "Experimentation Center",
        "wait_for": "Experiment Dashboard",
    },
    {
        "file": "04-predictive-analytics",
        "label": "Predictive Analytics",
        "wait_for": "Churn Prediction",
        "setup": "predictive",
    },
    {
        "file": "05-ai-product-analyst",
        "label": "AI Product Analyst",
        "wait_for": "Chat with Product Analyst",
    },
]


def _click_nav(page, label: str) -> None:
    """Click a sidebar navigation item reliably."""
    sidebar = page.locator('[data-testid="stSidebar"]')
    option = sidebar.locator("label").filter(has_text=label).first
    option.wait_for(state="visible", timeout=30000)
    option.click()
    page.wait_for_timeout(2000)


def _assert_no_errors(page) -> None:
    """Fail fast if Streamlit rendered an error block."""
    error_box = page.locator('[data-testid="stException"]')
    if error_box.count() > 0:
        message = error_box.first.inner_text()
        raise RuntimeError(f"Page has visible error: {message[:200]}")


def _setup_predictive(page) -> None:
    """Ensure churn charts are visible for screenshots (no retrain)."""
    page.get_by_text("High Risk Users", exact=False).wait_for(timeout=60000)
    page.get_by_text("Churn Probability Distribution", exact=False).wait_for(timeout=60000)
    page.evaluate("window.scrollTo(0, 450)")
    page.wait_for_timeout(1500)


def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE_URL, wait_until="networkidle", timeout=120000)
        page.wait_for_timeout(4000)

        for item in PAGES:
            _click_nav(page, item["label"])
            page.get_by_text(item["wait_for"], exact=False).first.wait_for(timeout=60000)
            if item.get("setup") == "predictive":
                _setup_predictive(page)
            page.wait_for_timeout(2000)
            _assert_no_errors(page)

            path = SCREENSHOTS_DIR / f"{item['file']}.png"
            page.screenshot(path=str(path), full_page=True)
            print(f"Saved {path}")

        browser.close()


if __name__ == "__main__":
    main()
