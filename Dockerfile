FROM python:3.10-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# تسطيب الأدوات الأساسية ومكتبات معالجة الفيديو وقواعد البيانات المتجهية
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# تسطيب تعريفات Microsoft ODBC 18 لـ SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]