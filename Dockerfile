FROM python:3.12-slim

# Отключаем буферизацию вывода Python
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Команда по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]