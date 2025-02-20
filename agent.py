from langchain_openai import ChatOpenAI
import asyncio
from dotenv import load_dotenv
import sys
import os

load_dotenv()

print("Current working directory:", os.getcwd())

browser_use_path = os.path.join(os.path.dirname(__file__), 'browser-use')
print("Appending to sys.path:", browser_use_path)
sys.path.append(browser_use_path)

print("sys.path:", sys.path)

from browser_use import Agent

URL = "https://www.amazon.com"

async def main():
    try:
        agent = Agent(
            task=f"Navigate to {URL}, enable network monitoring, and capture all network requests while the page fully loads. Once all necessary network activity is recorded, export the collected network traffic as a HAR file and save it as network_traffic.har. Return the file location once the process is complete.",
            llm=ChatOpenAI(model="gpt-4o"),
        )
        result = await agent.run()
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")

asyncio.run(main())