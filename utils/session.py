import os
from pyrogram import Client
from dotenv import load_dotenv

# Load existing environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("API_ID", ""))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION", "")

def is_session_valid(session_string):
    """Check if the given session string is still valid."""
    try:
        app = Client("session_checker", api_id=API_ID, api_hash=API_HASH, session_string=session_string)
        app.start()
        print("✅ Existing session string is still valid!")
        app.stop()
        return True
    except Exception as e:
        print(f"❌ Session expired or invalid: {e}")
        return False

def generate_new_session():
    """Generates a new session string with proper user authentication."""
    print("🔄 Starting new session generation...")
    
    if not API_ID or not API_HASH:
        print("❌ API_ID or API_HASH not found in environment variables!")
        return None
    
    try:
        app = Client(
            "new_session",
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True
        )
        
        print("📱 Please enter your phone number in international format (e.g., +1234567890):")
        with app:
            new_session = app.export_session_string()
            print("\n✅ Successfully generated new session string!")
            print("ℹ️ You may need to check your Telegram app for the login code.")
            return new_session
            
    except Exception as e:
        print(f"\n❌ Error during session generation: {str(e)}")
        return None

def update_env_file(new_session):
    """Update the .env file with the new session string."""
    env_file = ".env"
    
    # Read current .env contents
    with open(env_file, "r") as file:
        lines = file.readlines()

    # Update session string if exists, otherwise add it
    updated = False
    with open(env_file, "w") as file:
        for line in lines:
            if line.startswith("SESSION="):
                file.write(f"SESSION={new_session}\n")
                updated = True
            else:
                file.write(line)
        
        if not updated:
            file.write(f"\nSESSION={new_session}\n")

    print("✅ .env file updated successfully!")

# Main logic
def main():
    if SESSION_STRING and is_session_valid(SESSION_STRING):
        print("🚀 Using existing valid session string. No update needed.")
        return
    
    print("\n📝 Starting session string generation process...")
    print("ℹ️ You will need to authenticate with Telegram to generate a new session.")
    
    new_session = generate_new_session()
    if new_session:
        update_env_file(new_session)
        print("\n🎉 Session string has been generated and saved to .env file!")
        print("Session string:   ", new_session)
    else:
        print("\n❌ Failed to generate session string. Please check your credentials and try again.")

if __name__ == "__main__":
    main()