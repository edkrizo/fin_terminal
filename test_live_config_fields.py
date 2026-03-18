from google import genai
from google.genai import types

def test_live_config():
    try:
        # 🧪 Let's list all attributes in types.LiveConnectConfig
        print("Fields in types.LiveConnectConfig:")
        try:
             import pydantic
             print(types.LiveConnectConfig.__fields__.keys())
        except:
             print(dir(types.LiveConnectConfig))
             
        print("\nFields in types.SpeechConfig:")
        try:
             print(types.SpeechConfig.__fields__.keys())
        except:
             print(dir(types.SpeechConfig))
             
    except Exception as e:
        print(f"❌ Error inspecting: {e}")

if __name__ == "__main__":
    test_live_config()
