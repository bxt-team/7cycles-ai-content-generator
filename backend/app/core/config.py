import os
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Try multiple paths to find .env file
possible_paths = [
    Path(__file__).parent.parent.parent / '.env',  # Root directory
    Path(__file__).parent.parent / '.env',         # Backend directory
    Path.cwd() / '.env',                           # Current working directory
    Path.cwd().parent / '.env',                    # Parent of CWD
]

env_loaded = False
for env_path in possible_paths:
    if env_path.exists():
        print(f"[CONFIG] Found .env at: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        break
    else:
        print(f"[CONFIG] .env not found at: {env_path}")

if not env_loaded:
    print("[CONFIG] WARNING: No .env file found in any expected location")
    
print(f"[CONFIG] Current working directory: {Path.cwd()}")
print(f"[CONFIG] OPENAI_API_KEY loaded: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"[CONFIG] OPENAI_API_KEY length: {len(os.getenv('OPENAI_API_KEY', ''))}")

class Settings:
    """Application configuration settings"""
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    PEXELS_API_KEY: Optional[str] = os.getenv("PEXELS_API_KEY")
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    INSTAGRAM_BUSINESS_ACCOUNT_ID: Optional[str] = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    RUNWAY_API_KEY: Optional[str] = os.getenv("RUNWAY_API_KEY")
    ELEVENLABS_API_KEY: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    KLINGAI_API_KEY: Optional[str] = os.getenv("KLINGAI_API_KEY")
    KLINGAI_PROVIDER: str = os.getenv("KLINGAI_PROVIDER", "piapi")  # piapi, appypie, or segmind
    
    # Paths
    ADB_PATH: str = os.getenv("ADB_PATH", "adb")
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]  # Allow all origins
    
    # Storage Configuration
    STORAGE_ADAPTER: str = os.getenv("STORAGE_ADAPTER", "json")  # json, supabase, or dual
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_JWT_SECRET: Optional[str] = os.getenv("SUPABASE_JWT_SECRET")  # JWT secret for verifying tokens
    DUAL_WRITE_READ_FROM: str = os.getenv("DUAL_WRITE_READ_FROM", "json")  # json or supabase
    
    # File Storage Settings
    STORAGE_BASE_PATH: str = "storage"
    GENERATED_DIR: str = "generated"
    COMPOSED_DIR: str = "composed"
    INSTAGRAM_MEDIA_DIR: str = "instagram_media"
    VOICE_OVERS_DIR: str = "voice_overs"
    VIDEO_DIR: str = "videos"
    ANDROID_RESULTS_DIR: str = "android_test_results"
    
    @classmethod
    def get_storage_path(cls, *paths) -> str:
        """Get full storage path"""
        return os.path.join(cls.STORAGE_BASE_PATH, *paths)

settings = Settings()
print(f"[CONFIG] Settings.OPENAI_API_KEY is set: {bool(settings.OPENAI_API_KEY)}")
print(f"[CONFIG] Settings.OPENAI_API_KEY length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")