# استخدام الإصدار الأحدث من Debian 12 (Bookworm) لضمان دعم ChromaDB
FROM python:3.10-bookworm

# إعداد المتغيرات البيئية لتقليل حجم الكونتينر وتسريع الأداء
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1. تسطيب مكتبات النظام، أدوات C++، و ffmpeg لمعالجة الفيديوهات
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    ffmpeg \
    libsm6 \
    libxext6 \
    gcc \
    g++ \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. تسطيب تعريفات Microsoft ODBC 18 المتوافقة تماماً مع Debian 12
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# 3. تحديث أدوات بايثون الأساسية لتجنب أخطاء البناء
RUN pip install --upgrade pip setuptools wheel

# 4. تسريع البناء (Layer Caching): تسطيب PyTorch في طبقة منفصلة

RUN pip install --default-timeout=2000 --retries=20 torch==2.1.0

# 5. نسخ باقي ملف المتطلبات وتسطيب المكتبات الخفيفة
COPY requirements.txt .
RUN pip install -r requirements.txt

# 6. نسخ باقي ملفات الكود
COPY . .

# فتح البورت
EXPOSE 8000

# أمر تشغيل السيرفر
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]