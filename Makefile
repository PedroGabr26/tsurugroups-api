# Makefile for Tsuru Groups

.PHONY: help install migrate run test clean docker-build docker-up docker-down setup lint format

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies with Poetry"
	@echo "  setup        - Setup project (install, migrate, create superuser)"
	@echo "  migrate      - Run Django migrations"
	@echo "  run          - Run Django development server"
	@echo "  worker       - Run RQ worker"
	@echo "  scheduler    - Run RQ scheduler"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting (flake8)"
	@echo "  format       - Format code (black, isort)"
	@echo "  clean        - Clean Python cache files"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start Docker services"
	@echo "  docker-down  - Stop Docker services"

# Install dependencies
install:
	@echo "Installing dependencies..."
	poetry install

# Setup project
setup: install
	@echo "Setting up project..."
	poetry run python manage.py migrate
	poetry run python manage.py setup_initial_data
	@echo "Create a superuser account:"
	poetry run python manage.py createsuperuser

# Run migrations
migrate:
	@echo "Running migrations..."
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate

# Run development server
run:
	@echo "Starting Django development server..."
	poetry run python manage.py runserver

# Run RQ worker
worker:
	@echo "Starting RQ worker..."
	poetry run python manage.py rqworker default scheduling

# Run RQ scheduler
scheduler:
	@echo "Starting RQ scheduler..."
	poetry run python manage.py rqscheduler

# Run tests
test:
	@echo "Running tests..."
	poetry run python manage.py test
	@echo "Running coverage..."
	poetry run pytest --cov=apps --cov-report=html --cov-report=term

# Lint code
lint:
	@echo "Running linting..."
	poetry run flake8 apps/ tsuru_groups/ --max-line-length=88 --extend-ignore=E203,W503

# Format code
format:
	@echo "Formatting code..."
	poetry run black apps/ tsuru_groups/
	poetry run isort apps/ tsuru_groups/

# Clean cache files
clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/ htmlcov/ .coverage

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

# Production commands
deploy-prod:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d --build

# Database operations
db-reset:
	@echo "Resetting database..."
	poetry run python manage.py flush --noinput
	poetry run python manage.py migrate
	poetry run python manage.py setup_initial_data

db-backup:
	@echo "Creating database backup..."
	docker-compose exec db pg_dump -U postgres tsuru_groups > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Collect static files
collectstatic:
	@echo "Collecting static files..."
	poetry run python manage.py collectstatic --noinput

# Create Django app
create-app:
	@read -p "Enter app name: " app_name; \
	poetry run python manage.py startapp $$app_name apps/$$app_name

# Generate requirements.txt from Poetry
requirements:
	@echo "Generating requirements.txt..."
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# Check Django deployment
check-deploy:
	@echo "Checking Django deployment..."
	poetry run python manage.py check --deploy

# Load test data
loaddata:
	@echo "Loading test data..."
	poetry run python manage.py setup_initial_data --force

# Shell
shell:
	@echo "Starting Django shell..."
	poetry run python manage.py shell_plus

# Show URLs
urls:
	@echo "Showing URL patterns..."
	poetry run python manage.py show_urls

# Monitor logs
logs:
	@echo "Monitoring logs..."
	tail -f logs/django.log