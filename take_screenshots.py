import asyncio
from playwright.async_api import async_playwright

async def take_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        base_url = "http://127.0.0.1:5000"
        
        try:
            # 1. Landing/Home
            await page.goto(base_url)
            await page.wait_for_timeout(1000)
            await page.screenshot(path="landing.png")
            
            # 2. Register User 1
            await page.goto(f"{base_url}/register")
            await page.wait_for_timeout(500)
            await page.screenshot(path="register.png")
            await page.fill('input[name="username"]', 'TestUser1')
            await page.fill('input[name="email"]', 'test1@example.com')
            await page.fill('input[name="password"]', 'password123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(1000)
            
            # 3. Hobbies
            await page.screenshot(path="hobbies.png")
            
            # We assume it goes to hobbies page after registration. Let's add hobbies and save.
            await page.check('input[value="1"]') # Select Hobby 1 if exists
            await page.check('input[value="2"]') # Select Hobby 2 if exists
            await page.fill('input[name="custom_hobbies"]', 'Surfing')
            
            # Sometimes click might need targeting. The button is submit.
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(1000)
            
            # 4. Dashboard
            await page.screenshot(path="dashboard.png")
            
            # 5. Matches
            await page.goto(f"{base_url}/matches")
            await page.wait_for_timeout(1000)
            await page.screenshot(path="matches.png")
            
            # 6. Admin
            await page.goto(f"{base_url}/admin")
            await page.wait_for_timeout(1000)
            await page.screenshot(path="admin.png")
            
            print("Successfully took screenshots")
        except Exception as e:
            print(f"Error taking screenshots: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(take_screenshots())
