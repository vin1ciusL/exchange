# Exchange API

API para obtenção de cotações de câmbio em tempo real, desenvolvida com FastAPI.

## Recursos

- ✅ Obtenção de taxas de câmbio em tempo real
- ✅ Autenticação via JWT Bearer token
- ✅ Integração com ExchangeRate-API
- ✅ Health checks
- ✅ Logging estruturado
- ✅ Suporte a Docker

## Tecnologias

- **FastAPI** 0.115.3 - Framework web assíncrono
- **HTTPX** 0.28.1 - Cliente HTTP assíncrono
- **Python** 3.11
- **Docker** - Containerização

## Requisitos

- Python 3.11+
- pip ou conda

## Instalação Local

### 1. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Editar .env com suas configurações
```

### 4. Executar a aplicação

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

A API estará disponível em `http://localhost:8080`

Documentação interativa (Swagger): `http://localhost:8080/docs`

## Endpoints

### GET `/exchange/{from_currency}/{to_currency}`

Obtém a taxa de câmbio entre duas moedas.

**Parâmetros:**
- `from_currency` (path): Código da moeda de origem (ex: USD)
- `to_currency` (path): Código da moeda de destino (ex: BRL)

**Headers:**
- `Authorization: Bearer {token}` - Token JWT válido

**Response (200):**
```json
{
  "sell": 5.2500,
  "buy": 5.1500,
  "date": "2026-04-29 15:30:45",
  "id_account": "user-123"
}
```

**Erros:**
- `400` - Moeda inválida ou não encontrada
- `401` - Token inválido ou expirado
- `502` - Erro na API de câmbio
- `503` - Serviço de autenticação indisponível

### GET `/health`

Verifica se o serviço está operacional.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "exchange",
  "timestamp": "2026-04-29T15:30:45.123456"
}
```

### GET `/`

Informações básicas da API.

## Docker

### Build da imagem

```bash
docker build -t exchange-api:latest .
```

### Executar container

```bash
docker run -d \
  --name exchange-api \
  -p 8080:8080 \
  -e EXCHANGE_API_KEY=your-key \
  -e AUTH_SERVICE_URL=http://auth:8080 \
  --network microservices \
  exchange-api:latest
```

### Docker Compose

Adicione ao seu `docker-compose.yml`:

```yaml
exchange:
  build: ./api/exchange
  container_name: exchange-api
  ports:
    - "8080:8080"
  environment:
    - EXCHANGE_API_KEY=${EXCHANGE_API_KEY}
    - AUTH_SERVICE_URL=http://auth:8080
    - REQUEST_TIMEOUT=6.0
  networks:
    - microservices
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 5s
```

## Exemplos de Uso

### Com curl

```bash
curl -X GET "http://localhost:8080/exchange/USD/BRL" \
  -H "Authorization: Bearer your-jwt-token"
```

### Com Python

```python
import requests

headers = {"Authorization": "Bearer your-jwt-token"}
response = requests.get(
    "http://localhost:8080/exchange/USD/BRL",
    headers=headers
)
print(response.json())
```

### Com JavaScript

```javascript
const token = "your-jwt-token";
const response = await fetch(
  "http://localhost:8080/exchange/USD/BRL",
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);
const data = await response.json();
console.log(data);
```

## Configurações

As seguintes variáveis de ambiente podem ser configuradas:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `EXCHANGE_API_KEY` | Chave da API ExchangeRate | `6da6d6433dce806f39b5f292` |
| `AUTH_SERVICE_URL` | URL do serviço de autenticação | `http://auth:8080` |
| `EXCHANGE_API_BASE_URL` | URL base da API de câmbio | Gerada automaticamente |
| `REQUEST_TIMEOUT` | Timeout para requisições HTTP | `6.0` |

## Spread (Margem)

A API aplica um spread realista:
- **Venda (sell)**: +2% sobre a taxa
- **Compra (buy)**: -2% sobre a taxa

Isso simula o comportamento de uma corretora real.

## Tratamento de Erros

A API retorna respostas de erro estruturadas:

```json
{
  "detail": "Descrição do erro"
}
```

Códigos HTTP utilizados:
- `200` - Sucesso
- `400` - Requisição inválida
- `401` - Não autenticado
- `502` - Gateway indisponível
- `503` - Serviço indisponível

## Logging

A aplicação registra:
- Requisições de verificação de token
- Taxas de câmbio obtidas
- Erros e exceções

Visualize os logs:

```bash
docker logs -f exchange-api
```

## Desenvolvido por

Tim de Desenvolvimento - Microsserviços 2026

## Licença

MIT
