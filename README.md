Instructivo para levantar el backend del sistema de inventario Maestranza (Django + PostgreSQL).

- 1. Crear una variable de entorno .env

```bash

# ===========================
# ENTORNO DJANGO
# ===========================
DEBUG=True
SECRET_KEY="clave_super_secreta_para_maestranza"
ALLOWED_HOSTS=localhost,127.0.0.1

# ===========================
# BASE DE DATOS - POSTGRESQL
# ===========================
DB_ENGINE=django.db.backends.postgresql
DB_NAME=maestranza_db
DB_USER=maestranza_user
DB_PASSWORD=MaestranzaPass123
DB_HOST=localhost
DB_PORT=5432

# ===========================
# API CONFIG
# ===========================
API_PAGE_SIZE=20
STOCK_WARNING_LIMIT=10
DEFAULT_CURRENCY=CLP

# ===========================
# SEGURIDAD (ENTORNO DEV)
# ===========================
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0

# ===========================
# LOGGING
# ===========================
LOG_LEVEL=DEBUG
AUDIT_LOG_FILE=logs/audit.log
ERROR_LOG_FILE=logs/errors.log

# ===========================
# EMAIL (SOLO DESARROLLO)
# ===========================
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend


```

- 2. Instalar dependencias base

```bash

pip install django psycopg2-binary python-decouple django-filter drf-spectacular django-cors-headers


```

- 3. Modificar DATABASES en settings.py

```bash

DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE"),
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432", cast=int),
    }
}


```

```bash

```

- 4. En settings.py importa

```bash

from pathlib import Path
import os
from decouple import config

```

- 5. Agrega estas variables

```bash

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=lambda v: v.split(","))

```

- 6. Agrega todo este bloque

```bash

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "inventario",
]

AUTH_USER_MODEL = 'inventario.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8100",
    "http://127.0.0.1:8100",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": config("API_PAGE_SIZE", default=100, cast=int),
}

ROOT_URLCONF = 'maestranza_backend.urls'

```

- 7. Ubica la region geografica

```bash

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

```

- 8. Añade el logging

```bash

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "audit_file": {
            "class": "logging.FileHandler",
            "filename": config("AUDIT_LOG_FILE"),
            "level": config("LOG_LEVEL", default="INFO"),
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": config("ERROR_LOG_FILE"),
            "level": "ERROR",
        },
    },
    "loggers": {
        "audit": {
            "handlers": ["audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


```

- 9. Conéctate como usuario postgres:

--

```bash

-- psql -U postgres

```

- 10. Crear la base de datos

```bash

CREATE DATABASE maestranza_db
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'es_CL.UTF-8'
    LC_CTYPE = 'es_CL.UTF-8'
    TEMPLATE = template0;

```

- 11. Crear el usuario

```bash

CREATE USER maestranza_user WITH
    LOGIN
    PASSWORD 'MaestranzaPass123'
    CREATEDB
    VALID UNTIL 'infinity';

```

- 12. Otorgar todos los privilegios al usuario sobre la base

```bash

GRANT ALL PRIVILEGES ON DATABASE maestranza_db TO maestranza_user;

```

- 13. Otorga privilegios sobre el esquema public

```bash

GRANT ALL ON SCHEMA public TO maestranza_user;

```

- 14. Otorga privilegios para crear objetos en el esquema

```bash

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO maestranza_user;

```

- 15. Ejecutar migraciones

```bash

python manage.py makemigrations
python manage.py migrate

```

- 16. Crea un superuser

```bash

python manage.py createsuperuser

```

- 17. En tu carpeta base de proyecto en Windows (PowerShell o CMD):

```bash

mkdir logs
type nul > logs\audit.log
type nul > logs\errors.log


```

- 18. Iniciar el servidor

```bash

python manage.py runserver

```

- 19. Acceder a la aplicación desde el navegador
    * Panel de administración:

```bash

 http://127.0.0.1:8000/admin/

```