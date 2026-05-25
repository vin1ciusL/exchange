import os
import logging
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, field_validator, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Exchange API",
    description="API para obtenção de cotações de câmbio em tempo real",
    version="1.0.0"
)

EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
EXCHANGE_API_BASE_URL = os.getenv(
    "EXCHANGE_API_BASE_URL",
    f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest"
)
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "6.0"))


class ExchangeResponse(BaseModel):
    sell: float
    buy: float
    date: str
    id_account: str = Field(..., alias="id-account")

    class Config:
        populate_by_name = True

    @field_validator("date", mode="before")
    @classmethod
    def format_date(cls, v) -> str:
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return v


async def get_exchange_rate_from_api(from_currency: str, to_currency: str) -> dict:
    logger.info(f"Obtendo taxa de câmbio: {from_currency} -> {to_currency}")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            url = f"{EXCHANGE_API_BASE_URL}/{from_currency.upper()}"
            response = await client.get(url)
        except httpx.HTTPError as exc:
            logger.error(f"Erro ao chamar API de câmbio: {str(exc)}")
            raise HTTPException(status_code=502, detail="Erro ao conectar com API de câmbio")

    if response.status_code != 200:
        logger.error(f"API retornou status: {response.status_code}")
        raise HTTPException(status_code=502, detail="Erro ao obter taxa de câmbio")

    data = response.json()

    if data.get("result") != "success":
        error_type = data.get("error-type", "Erro desconhecido")
        logger.error(f"Erro na API: {error_type}")
        raise HTTPException(status_code=400, detail=f"Erro na API de câmbio: {error_type}")

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
    id_account: str = Header(..., alias="id-account")
) -> ExchangeResponse:
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if len(from_currency) != 3 or len(to_currency) != 3:
        raise HTTPException(status_code=400, detail="Códigos de moeda devem ter 3 caracteres")

    if from_currency == to_currency:
        return ExchangeResponse(
            sell=1.0,
            buy=1.0,
            date=datetime.now(timezone.utc),
            id_account=id_account,
        )

    data = await get_exchange_rate_from_api(from_currency, to_currency)
    rates = data.get("conversion_rates", {})

    if to_currency not in rates:
        logger.warning(f"Moeda não encontrada: {to_currency}")
        raise HTTPException(status_code=400, detail=f"Moeda {to_currency} não encontrada")

    rate = float(rates[to_currency])
    sell_rate = round(rate * 1.02, 4)
    buy_rate = round(rate * 0.98, 4)

    logger.info(f"Taxa de câmbio obtida: {from_currency}/{to_currency} = {rate}")

    return ExchangeResponse(
        sell=sell_rate,
        buy=buy_rate,
        date=datetime.now(timezone.utc),
        id_account=id_account,
    )


@app.get("/health", summary="Health Check", tags=["Health"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "exchange",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/", summary="Informações da API", tags=["Info"])
async def root() -> dict:
    return {
        "service": "Exchange API",
        "version": "1.0.0",
        "description": "API para obtenção de cotações de câmbio",
        "endpoints": {
            "exchange": "/exchanges/{from_currency}/{to_currency}",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
