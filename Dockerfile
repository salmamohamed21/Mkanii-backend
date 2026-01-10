# Base image
FROM python:3.11-slim

# Prevent python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Collect static (اختياري)
# RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run app with gunicorn
CMD ["gunicorn", "mkani.wsgi:application", "--bind", "0.0.0.0:8000"]
