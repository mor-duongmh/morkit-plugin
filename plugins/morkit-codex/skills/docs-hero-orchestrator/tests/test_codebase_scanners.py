"""Tests for parse_codebase_routes.py + parse_codebase_models.py."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from parse_codebase_models import scan_models  # noqa: E402
from parse_codebase_routes import scan_routes  # noqa: E402


# --- Routes: Express ---

EXPRESS_TS = """
import express from 'express';
const app = express();

app.get('/users', (req, res) => res.json([]));
app.post('/users', (req, res) => res.status(201));
app.get('/users/:id', requireAuth, (req, res) => res.json({}));
"""


def test_routes_express_basic():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "app.ts"
        p.write_text(EXPRESS_TS)
        endpoints = scan_routes([td])
    methods_paths = {(e.method, e.path) for e in endpoints}
    assert ("GET", "/users") in methods_paths
    assert ("POST", "/users") in methods_paths
    assert ("GET", "/users/{id}") in methods_paths


def test_routes_express_auth_detected():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "app.ts"
        p.write_text(EXPRESS_TS)
        endpoints = scan_routes([td])
    auth_ep = next(e for e in endpoints if e.path == "/users/{id}")
    assert auth_ep.auth_required is True


# --- Routes: NestJS ---

NESTJS_TS = """
import { Controller, Get, Post } from '@nestjs/common';

@Controller('users')
export class UsersController {
  @Get()
  findAll() {}

  @Post()
  create() {}

  @Get(':id')
  findOne() {}
}
"""


def test_routes_nestjs_with_controller_prefix():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "users.controller.ts"
        p.write_text(NESTJS_TS)
        endpoints = scan_routes([td])
    methods_paths = {(e.method.upper(), e.path) for e in endpoints}
    assert ("GET", "/users") in methods_paths
    assert ("POST", "/users") in methods_paths
    assert ("GET", "/users/{id}") in methods_paths


# --- Routes: FastAPI ---

FASTAPI_PY = """
from fastapi import FastAPI

app = FastAPI()

@app.get('/users')
async def list_users():
    return []

@app.post('/users')
async def create_user():
    pass

@app.get('/users/{user_id}')
async def get_user(user_id: int):
    pass
"""


def test_routes_fastapi():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "main.py"
        p.write_text(FASTAPI_PY)
        endpoints = scan_routes([td])
    methods_paths = {(e.method, e.path) for e in endpoints}
    assert ("GET", "/users") in methods_paths
    assert ("POST", "/users") in methods_paths
    assert ("GET", "/users/{user_id}") in methods_paths


# --- Routes: Django ---

DJANGO_PY = """
from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_list),
    path('users/<int:pk>/', views.user_detail),
]
"""


def test_routes_django():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "urls.py"
        p.write_text(DJANGO_PY)
        endpoints = scan_routes([td])
    paths = {e.path for e in endpoints}
    assert "/users" in paths
    assert "/users/{pk}" in paths


# --- Routes: ignore directories ---


def test_routes_ignore_node_modules():
    with tempfile.TemporaryDirectory() as td:
        nm = Path(td) / "node_modules" / "lib"
        nm.mkdir(parents=True)
        (nm / "a.js").write_text("app.get('/should-be-ignored', x);")

        src = Path(td) / "src"
        src.mkdir()
        (src / "app.js").write_text("app.get('/should-find', x);")

        endpoints = scan_routes([td])
        paths = {e.path for e in endpoints}
        assert "/should-find" in paths
        assert "/should-be-ignored" not in paths


# --- Models: Prisma ---

PRISMA_SCHEMA = """
model User {
  id        String   @id @default(uuid())
  email     String   @unique
  name      String
  createdAt DateTime @default(now())
}

model Post {
  id       String @id @default(uuid())
  authorId String
  author   User   @relation(fields: [authorId], references: [id])
  title    String
}
"""


def test_models_prisma():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "schema.prisma"
        p.write_text(PRISMA_SCHEMA)
        tables = scan_models([td])
    names = {t.name for t in tables}
    assert "users" in names
    assert "posts" in names

    users = next(t for t in tables if t.name == "users")
    assert users.framework == "prisma"
    col_names = {c.name for c in users.columns}
    assert "id" in col_names
    assert "email" in col_names
    assert "created_at" in col_names

    pk_cols = [c for c in users.columns if c.is_pk]
    assert any(c.name == "id" for c in pk_cols)


def test_models_prisma_unique_detected():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "schema.prisma"
        p.write_text(PRISMA_SCHEMA)
        tables = scan_models([td])
    users = next(t for t in tables if t.name == "users")
    email_col = next(c for c in users.columns if c.name == "email")
    assert email_col.is_unique


# --- Models: Django ---

DJANGO_MODELS = """
from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
"""


def test_models_django():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "models.py"
        p.write_text(DJANGO_MODELS)
        tables = scan_models([td])
    names = {t.name for t in tables}
    assert "users" in names
    assert "posts" in names


# --- Models: Raw SQL ---

SQL_MIGRATION = """
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE posts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""


def test_models_sql_create_table():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "001_init.sql"
        p.write_text(SQL_MIGRATION)
        tables = scan_models([td])
    names = {t.name for t in tables}
    assert "users" in names
    assert "posts" in names

    users = next(t for t in tables if t.name == "users")
    pk_cols = [c for c in users.columns if c.is_pk]
    assert len(pk_cols) >= 1

    email_col = next((c for c in users.columns if c.name == "email"), None)
    assert email_col is not None
    assert email_col.is_unique
    assert email_col.nullable is False


# --- Models: SQLAlchemy ---

SQLALCHEMY_PY = """
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
"""


def test_models_sqlalchemy():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "models.py"
        p.write_text(SQLALCHEMY_PY)
        tables = scan_models([td])
    assert any(t.name == "users" for t in tables)
    users = next(t for t in tables if t.name == "users")
    pk_cols = [c for c in users.columns if c.is_pk]
    assert any(c.name == "id" for c in pk_cols)


# --- Models: ignored directories ---


def test_models_ignore_node_modules():
    with tempfile.TemporaryDirectory() as td:
        nm = Path(td) / "node_modules" / "lib"
        nm.mkdir(parents=True)
        (nm / "schema.prisma").write_text("model Ignored { id String @id }")

        prisma = Path(td) / "prisma"
        prisma.mkdir()
        (prisma / "schema.prisma").write_text("model Real { id String @id }")

        tables = scan_models([td])
        names = {t.name for t in tables}
        assert "reals" in names
        assert "ignoreds" not in names
