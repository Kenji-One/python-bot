"""
PowerPlay API Inspector
Captures network requests to discover API endpoints
Run this to see what APIs PowerPlay uses
"""
import asyncio
import json
from playwright.async_api import async_playwright
from config import Config


async def inspect_api():
    """Capture all network requests to find PowerPlay APIs"""

    api_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture all requests
        async def log_request(request):
            if 'api' in request.url or 'powerplay.generac.com' in request.url:
                api_calls.append({
                    'method': request.method,
                    'url': request.url,
                    'headers': dict(request.headers),
                    'post_data': request.post_data if request.post_data else None
                })
                print(f"\n[{request.method}] {request.url}")

        # Capture all responses
        async def log_response(response):
            if 'api' in response.url or 'powerplay.generac.com' in response.url:
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = await response.text()
                        print(f"  → Response: {response.status}")
                        if len(body) < 500:
                            print(f"  → Body: {body}")
                except:
                    pass

        page.on('request', log_request)
        page.on('response', log_response)

        print("=" * 60)
        print("PowerPlay API Inspector")
        print("=" * 60)
        print("\nNavigating to PowerPlay...")
        print("Please manually log in and navigate to the dashboard")
        print("Watch the console for API calls")
        print("\nPress Ctrl+C when done inspecting\n")

        await page.goto(Config.LOGIN_URL)

        try:
            # Keep browser open for manual inspection
            await asyncio.sleep(300)  # 5 minutes to inspect
        except KeyboardInterrupt:
            print("\n\nInspection complete!")

        # Save captured API calls
        with open('api_calls.json', 'w') as f:
            json.dump(api_calls, f, indent=2)

        print(f"\nCaptured {len(api_calls)} API calls")
        print("Saved to api_calls.json")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_api())
