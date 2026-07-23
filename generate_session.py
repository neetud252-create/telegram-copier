import os
from telethon import TelegramClient
from telethon.sessions import StringSession

print("="*50)
print("🔑 TELEGRAM STRING SESSION GENERATOR")
print("="*50)

API_ID = int(input("Enter your API_ID: "))
API_HASH = input("Enter your API_HASH: ")
PHONE = input("Enter your phone number (with country code, e.g., +911234567890): ")

async def main():
    print("\n🔄 Connecting to Telegram...")
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE)
        string_session = client.session.save()
        print("\n" + "="*50)
        print("✅ YOUR STRING SESSION (Copy this exactly):")
        print("="*50)
        print(string_session)
        print("="*50)
        print("\n⚠️ SAVE THIS SECURELY! Never share it publicly!")
        print("📋 This will be used in your TELEGRAM_STRING_SESSION environment variable")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure your API_ID and API_HASH are correct")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
