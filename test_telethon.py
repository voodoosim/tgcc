import asyncio

from adapters.telethon_adapter import TelethonAdapter


async def test():
    adapter = TelethonAdapter()
    try:
        result = await adapter.create_session("+1234567890", 12345, "your_api_hash")
        print(result)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())
