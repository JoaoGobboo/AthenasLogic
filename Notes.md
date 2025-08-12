# Notas legais sobre a aplicação

## Build do container
- docker build -t minha-api-blockchain .

## Execultar o container
- docker run --env-file .env -p 5000:5000 minha-api-blockchain
