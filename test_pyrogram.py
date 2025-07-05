import asyncio

from pyrogram.errors import FloodWait

from adapters.pyrogram_adapter import PyrogramAdapter


async def test():
    adapter = PyrogramAdapter()
    try:
        result = await adapter.create_session("+1234567890", 12345, "your_api_hash")
        print(result)
    except (ValueError, FloodWait) as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())
