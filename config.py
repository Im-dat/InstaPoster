from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator

class Config(BaseSettings):
    # Configurações Gerais
    max_workers: int = 4
    upload_dir: Path
    log_level: str = "INFO"
    
    # Limites e configurações de mídia
    allowed_image_formats: List[str] = ['.jpg', '.png']
    allowed_video_formats: List[str] = ['.mp4', '.mov']
    max_video_size: int = 100 * 1024 * 1024  # 100MB
    max_video_duration: int = 60  # segundos
    max_retries: int = 3
    retry_delay: int = 5  # segundos
    
    # Telegram
    telegram_enabled: bool = False
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Email
    email_enabled: bool = False
    smtp_server: Optional[str] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_to: Optional[str] = None
    
    @validator('upload_dir')
    def validate_upload_dir(cls, v):
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True)
        return path
    
    @validator('max_workers')
    def validate_max_workers(cls, v):
        if v < 1:
            raise ValueError("max_workers deve ser maior que 0")
        return v
    
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False)