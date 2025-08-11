# Usa imagem oficial do Python slim (leve)
FROM python:3.11-slim

# Define diretório de trabalho dentro do container
WORKDIR /app

# Copia requirements.txt (vamos criar em seguida)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo código para dentro do container
COPY . .

# Define a variável de ambiente para Python não bufferizar saída (bom para logs)
ENV PYTHONUNBUFFERED=1

# Expõe a porta da sua API (se usar Flask default 5000)
EXPOSE 5000

# Comando padrão para rodar o app (ajuste conforme o nome do seu arquivo principal)
CMD ["python", "app.py"]
