# Usa imagem oficial do Python slim (leve)
FROM python:3.11-slim

# Define diretório de trabalho dentro do container
WORKDIR /app

# Copia requirements.txt primeiro para aproveitar cache de build
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo código para dentro do container
COPY . .

# Variável de ambiente para logs saírem imediatamente
ENV PYTHONUNBUFFERED=1

# Expõe a porta que o Flask usa
EXPOSE 5000

# --- CORREÇÃO AQUI ---
# Comando para rodar o Flask como um módulo, respeitando FLASK_APP e PYTHONPATH
CMD ["flask", "run", "--host=0.0.0.0"]
