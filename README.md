# TechMarket
TechMarket is a full-stack e-commerce web application for browsing and purchasing smartphones and accessories. Built with Django Templates for the front-end and Django REST Framework for the back-end API.

## Project Description
Users can browse phones by brand and category, view detailed product pages, register/login, place orders, and manage their profile. The project demonstrates full CRUD operations, token-based authentication, and REST API integration with CORS support.

## Team Members
- Gabdrakhman Amina
- Alikul Raniya
- Amirzhan Malika

## Tech Stack
- Backend: Django, Django REST Framework
- Frontend: Django Templates, HTML/CSS
- Database: SQLite (development)
- API Testing: Postman

## Features (planned)
- User authentication (register, login, logout)
- Browse phones by brand/category
- Product detail pages
- Place and manage orders (linked to authenticated user)
- REST API endpoints (FBV + CBV) with token authentication
- Admin panel customization

## Setup Instructions
```bash
git clone <repo-url>
cd techmarket
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
