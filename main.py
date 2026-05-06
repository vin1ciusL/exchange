import os
import logging
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator, Field

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Exchange API",
    description="API para obtenção de cotações de câmbio em tempo real",
    version="1.0.0"
)

security = HTTPBearer()

# Configurações via variáveis de ambiente
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "6da6d6433dce806f39b5f292")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8080")
EXCHANGE_API_BASE_URL = os.getenv(
    "EXCHANGE_API_BASE_URL",
    f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest"
)
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "6.0"))


class ExchangeResponse(BaseModel):
    """Modelo de resposta para cotação de câmbio"""
    sell: float
    buy: float
    date: str
    id_account: str = Field(..., alias="id-account")

    class Config:
        populate_by_name = True

    @field_validator("date", mode="before")
    @classmethod
    def format_date(cls, v) -> str:
        """Formata data para string ISO"""
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verifica o token JWT com o serviço de autenticação.
    
    Args:
        credentials: Credenciais do Bearer token
        
    Returns:
        ID da conta autenticada
        
    Raises:
        HTTPException: Se o token for inválido ou o serviço estiver indisponível
    """
    token = credentials.credentials
    logger.info("Verificando token de autenticação")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/auth/solve",
                json={"jwt": token},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                id_account = data.get("idAccount")
                if id_account:
                    logger.info(f"Token validado para conta: {id_account}")
                    return id_account
                raise HTTPException(
                    status_code=401,
                    detail="ID da conta não encontrado na resposta"
                )
            
            logger.warning(f"Falha na validação do token: {response.status_code}")
            raise HTTPException(
                status_code=401,
                detail=f"Token inválido (Status: {response.status_code})"
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Erro ao conectar com serviço de autenticação: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Serviço de autenticação indisponível"
            )


async def get_exchange_rate_from_api(
    from_currency: str,
    to_currency: str
) -> dict:
    """
    Obtém a taxa de câmbio de uma API externa.
    
    Args:
        from_currency: Moeda de origem
        to_currency: Moeda de destino
        
    Returns:
        Dicionário com as taxas de câmbio
        
    Raises:
        HTTPException: Se houver erro na API
    """
    logger.info(f"Obtendo taxa de câmbio: {from_currency} -> {to_currency}")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            url = f"{EXCHANGE_API_BASE_URL.rsplit('/', 1)[0]}/{from_currency.upper()}"
            response = await client.get(url)
        except httpx.HTTPError as exc:
            logger.error(f"Erro ao chamar API de câmbio: {str(exc)}")
            raise HTTPException(
                status_code=502,
                detail="Erro ao conectar com API de câmbio"
            )

    if response.status_code != 200:
        logger.error(f"API retornou status: {response.status_code}")
        raise HTTPException(
            status_code=502,
            detail="Erro ao obter taxa de câmbio"
        )

    data = response.json()
    
    if data.get("result") != "success":
        error_type = data.get("error-type", "Erro desconhecido")
        logger.error(f"Erro na API: {error_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Erro na API de câmbio: {error_type}"
        )

    return data


@app.get(
    "/exchanges/{from_currency}/{to_currency}",
    response_model=ExchangeResponse,
    summary="Obter taxa de câmbio",
    tags=["Exchange"]
)
async def get_exchange(
    from_currency: str,
    to_currency: str,
    id_account: str = Depends(verify_token)
) -> ExchangeResponse:
    """
    Obtém a taxa de câmbio entre duas moedas.
    
    - **from_currency**: Moeda de origem (ex: USD, BRL)
    - **to_currency**: Moeda de destino (ex: EUR, JPY)
    
    Requer autenticação via Bearer token.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # Validação básica
    if len(from_currency) != 3 or len(to_currency) != 3:
        raise HTTPException(
            status_code=400,
            detail="Códigos de moeda devem ter 3 caracteres"
        )
    
    if from_currency == to_currency:
        return ExchangeResponse(
            sell=1.0,
            buy=1.0,
            date=datetime.utcnow(),
            id_account=id_account,
        )

    data = await get_exchange_rate_from_api(from_currency, to_currency)
    
    rates = data.get("conversion_rates", {})
    
    if to_currency not in rates:
        logger.warning(f"Moeda não encontrada: {to_currency}")
        raise HTTPException(
            status_code=400,
            detail=f"Moeda {to_currency} não encontrada"
        )

    rate = float(rates[to_currency])
    
    # Aplicar spread (margem) realista
    sell_rate = round(rate * 1.02, 4)  # Venda com 2% de margem
    buy_rate = round(rate * 0.98, 4)   # Compra com 2% de margem

    logger.info(f"Taxa de câmbio obtida: {from_currency}/{to_currency} = {rate}")
    
    return ExchangeResponse(
        sell=sell_rate,
        buy=buy_rate,
        date=datetime.utcnow(),
        id_account=id_account,
    )


@app.get(
    "/health",
    summary="Health Check",
    tags=["Health"]
)
async def health_check() -> dict:
    """Verifica se o serviço está operacional"""
    return {
        "status": "healthy",
        "service": "exchange",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(
    "/",
    summary="Informações da API",
    tags=["Info"]
)
async def root() -> dict:
    """Retorna informações básicas da API"""
    return {
        "service": "Exchange API",
        "version": "1.0.0",
        "description": "API para obtenção de cotações de câmbio",
        "endpoints": {
            "exchange": "/exchange/{from_currency}/{to_currency}",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
