# Project Overview

Bookery is a Django-based REST API project designed to manage user authentication, reading statistics, book sessions, and comments. The project uses PostgreSQL as the database, Celery for background tasks, Redis as a message broker, and JWT (JSON Web Tokens) for authentication.

# Technologies

Django 5.x
Django Rest Framework
PostgreSQL
Celery
Redis
Docker & Docker Compose
JWT Authentication
SMTP Email (Gmail)

# Setup Instructions

## 1. Clone the Repository
Clone this repository to your local machine:
```
$ git clone https://github.com/horkaida/bookery.git
$ cd bookery
```
## 2. Environment Variables
Create a .env file in the project root to configure environment variables.
Add the following environment variables to the .env file:

```
# Django Settings
SECRET_KEY=your_secret_key
DEBUG=True

# Database Settings
DATABASE_NAME=bookery_db
DATABASE_USER=bookery_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=db
DATABASE_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Email SMTP Settings
EMAIL_HOST_USER=your_gmail_account
EMAIL_HOST_PASSWORD=your_gmail_password

# Celery Settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## 3. Docker Setup
Make sure Docker and Docker Compose are installed on your machine.

## 4. Build and Run the Application
To build and run the entire project using Docker Compose, run the following command:

```
docker-compose up -d
```
This will pull the required images (PostgreSQL, Redis, Celery) and build the Django application.

5. Running Migrations
Once the containers are up and running, you need to run database migrations. You can do this by running:

```
docker-compose exec bookery python manage.py migrate
``` 
## 6. Creating a Superuser
Create a superuser account to access the Django admin panel:

```
docker-compose exec bookery python manage.py createsuperuser
```
## 7. Accessing the Application
Django Admin: Visit http://localhost:8000/admin and log in using your superuser credentials.
API Endpoints: Access the REST API via http://localhost:8000.
## 8. Celery Tasks
Celery is configured to handle background tasks (e.g., updating user reading statistics). The following services are included in the docker-compose.yml:

Celery Worker: Handles task execution.
Celery Beat: Handles task scheduling.
These services automatically start when you run docker-compose up.

## 9. Running Tests
To run the tests for your project:

```
docker-compose exec bookery python manage.py test
```

Environment Variables

Here are the required environment variables for the project:

| Variable             | Description                                    |
|----------------------|------------------------------------------------|
| `SECRET_KEY`         | Django secret key (keep this secure!)           |
| `DEBUG`              | Debug mode (set to False in production)         |
| `DATABASE_NAME`      | PostgreSQL database name                        |
| `DATABASE_USER`      | PostgreSQL database user                        |
| `DATABASE_PASSWORD`  | PostgreSQL database password                    |
| `DATABASE_HOST`      | Host for the database (use `db` in Docker Compose) |
| `DATABASE_PORT`      | PostgreSQL port (default: 5432)                 |
| `REDIS_HOST`         | Redis host (use `redis` in Docker Compose)      |
| `REDIS_PORT`         | Redis port (default: 6379)                      |
| `EMAIL_HOST_USER`    | Your email account (used for sending emails)    |
| `EMAIL_HOST_PASSWORD`| Your email account password                     |


# Celery Tasks

Celery tasks are used to compute statistics on reading sessions for users.

Task: reading_time_statistic (Runs every day by default)
Updates reading time statistics for users over the last 7 and 30 days.
You can modify the frequency of the task in the CELERY_BEAT_SCHEDULE inside the settings.py file.

# License

This project is licensed under the MIT License.

