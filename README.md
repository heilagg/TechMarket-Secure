# TechMarket-Secure

A secure-by-design e-commerce web application for browsing and buying smartphones and accessories. Built for the Software Security and Secure Development (SSSD) course. The goal is not only the application, but a secure end-to-end development process: threat modeling, defensive coding, a DevSecOps pipeline, and runtime security.

## Overview

TechMarket is a Django and Django REST Framework store. Users can browse phones by brand and category, view product pages, register, log in, place orders, and manage their profile. Around this app the team builds a Secure Development Lifecycle.

## Tech stack

Backend: Django 5.2, Django REST Framework. Frontend: Django Templates, HTML, CSS. Database: SQLite (development). Authentication: Argon2id password hashing, JWT (SimpleJWT), role-based authorization. Identity provider (planned for endterm): Keycloak over OpenID Connect. Security tooling: gitleaks, Bandit, Semgrep, pip-audit, Dependabot, GitHub Actions.

## Team and roles

Amirzhan Malika (@heilagg) - AppSec and Authentication: defensive coding, cryptography (Argon2id), JWT auth, role-based authorization.

Karatayeva Ayazhan (@sunriseparalellum) - DevSecOps and Automation: local security setup, CI/CD security gates (SAST, SCA, secret scanning), secrets management, review process.

Bolegenova Ayaulym (@ayekaa06) - Offensive Validation and Runtime: architecture, threat model (STRIDE), vulnerability validation, runtime defense (endterm).

## Security features (midterm)

Passwords hashed with Argon2id. JWT access and refresh tokens with short lifetimes (access 15 minutes, refresh 1 day). Role-based authorization enforced on the server (admin-only endpoints). Secrets kept out of code and loaded from environment variables. Hardened settings: DEBUG off by default, CORS allow-list, HTTPS redirect, secure cookies. DevSecOps pipeline: secret scanning, SAST, SCA, security tests, and required review on a protected main branch.

## Local setup

Create and activate a Python virtual environment, then run pip install -r requirements.txt. Copy .env.example to .env and set DJANGO_SECRET_KEY. Then run python manage.py migrate and python manage.py runserver. The app refuses to start without DJANGO_SECRET_KEY by design. Full setup steps are in docs/DEVSECOPS.md.

## Documentation

Threat model: docs/THREAT_MODEL.md. DevSecOps and developer guide: docs/DEVSECOPS.md.
