# Notas legais sobre a aplicação

## Comandos em relação ao container de docker
- **Comando para realizar a build**: docker build -t minha-api-blockchain .
- **Comando para execultar o container**: docker run --env-file .env -p 5000:5000 minha-api-blockchain

## Comandos no cache
- docker build --cache-from minha-api-blockchain -t minha-api-blockchain .
- docker build --no-cache -t minha-api-blockchain .

