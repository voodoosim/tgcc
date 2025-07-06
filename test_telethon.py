import asyncio

from adapters.telethon_adapter import TelethonAdapter


async def test():
    adapter = TelethonAdapter()
    phone = "+1234567890"  # Replace with your phone number
    api_id = 12345  # Replace with your API ID
    api_hash = "your_api_hash"  # Replace with your API Hash

    try:
        # Step 1: Create session and request code
        print("Requesting code...")
        result = await adapter.create_session(phone, api_id, api_hash)
        print(f"Code request sent. Result: {result}")

        phone_code_hash = str(result["phone_code_hash"])
        session_string = str(result["session_string"])

        # Step 2: Complete authentication with the received code
        code = input("Please enter the code you received: ")
        print("Completing authentication...")
        auth_result = await adapter.complete_auth(
            phone, api_id, api_hash, code, phone_code_hash, session_string
        )
        print(f"Authentication successful. Result: {auth_result}")

        # Step 3: Validate the session
        print("Validating session...")
        is_valid = await adapter.validate_session(
            auth_result["session_string"], api_id, api_hash
        )
        print(f"Session valid: {is_valid}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())