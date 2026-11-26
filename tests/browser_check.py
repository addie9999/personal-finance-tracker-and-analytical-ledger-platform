"""Browser smoke test for the demo-only ledger served on localhost."""
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:8000")
    expect(page.get_by_role("heading", name="Analytical Ledger")).to_be_visible()
    metrics = page.locator(".metrics article")
    expect(metrics.nth(0)).to_contain_text("97,698.00")
    expect(metrics.nth(1)).to_contain_text("1,53,180.00")
    expect(metrics.nth(2)).to_contain_text("55,482.00")
    page.get_by_label("View").select_option("monthly_flow")
    expect(page.locator("tbody tr")).to_have_count(3)
    page.get_by_role("button",name="Add entry").click()
    page.get_by_label("Date",exact=True).fill("2026-04-03")
    page.get_by_label("Category",exact=True).select_option("2")
    page.get_by_label("Amount").fill("50.25")
    page.get_by_label("Description").fill("Browser demo groceries")
    page.get_by_role("button",name="Save entry").click()
    expect(page.get_by_role("status")).to_have_text("Entry saved.")
    expect(metrics.nth(0)).to_contain_text("97,647.75")
    expect(page.locator("tbody tr").first).to_contain_text("Browser demo groceries")
    browser.close()
