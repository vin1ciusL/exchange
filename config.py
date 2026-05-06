"""
Configurações centralizadas da aplicação
"""
import os
from typing import Optional


class Settings:
    """Configurações da Exchange API"""
    
    # API Configuration
    EXCHANGE_API_KEY: str = os.getenv("EXCHANGE_API_KEY", "6da6d6433dce806f39b5f292")
    EXCHANGE_API_BASE_URL: str = os.getenv(
        "EXCHANGE_API_BASE_URL",
        f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest"
    )
    
    # Auth Service
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://auth:8080")
    
    # HTTP Configuration
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "6.0"))
    
    # API Documentation
    API_TITLE: str = "Exchange API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API para obtenção de cotações de câmbio em tempo real"
    
    # Spread (Margem aplicada nas taxas)
    SELL_SPREAD: float = 0.02  # 2% de margem na venda
    BUY_SPREAD: float = 0.02   # 2% de margem na compra
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Environment
    ENV: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()
