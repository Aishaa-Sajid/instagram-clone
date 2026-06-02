# Instagram Clone (Full Stack Web Application)

A full-stack Instagram-like social media application built using **FastAPI, React, PostgreSQL, Celery, and Cloudinary**.  
It supports authentication, posts, stories, likes, comments, follow system, and search functionality with background processing.

---

## Tech Stack

### Frontend
- React

### Backend
- FastAPI (Python)
- JWT Authentication
- Celery (Background Tasks)

### Database
- PostgreSQL

### Storage
- Cloudinary (Media Storage)

### Background Services
- Celery + Redis

---

## Features

### Authentication
- User registration with email & username
- JWT-based login system (Access + Refresh tokens)
- Email verification system
- Secure password hashing (bcrypt)

### Posts
- Create posts with captions
- Upload 1–10 images per post
- Edit and delete own posts
- Images stored in Cloudinary (URLs stored in DB)

### Likes & Comments
- Like / Unlike posts (one like per user per post)
- Add, edit, delete comments
- Post owner can delete any comment on their post

### Follow System
- Follow / Unfollow users
- Public accounts → direct follow
- Private accounts → follow request system
- Accept / reject follow requests
- No duplicate or self-follow allowed

### Stories
- Upload image/video stories
- Stories expire after 24 hours
- Automatic deletion using Celery background worker

### Search
- Search users by username
- PostgreSQL trigram / full-text search indexing
- Optimized response time ≤ 2 seconds

---

## Architecture

- Client: React Web App
- Backend: FastAPI REST APIs
- Database: PostgreSQL
- Media Storage: Cloudinary
- Background Processing: Celery + Redis Queue

---

## Project Structure (Backend)

```bash
src/
│
├── routes/          # API endpoints (auth, posts, users, etc.)
├── repositories/    # Database queries layer
├── schemas/         # Pydantic models
├── utils/           # Helper functions
├── core/            # Configurations & settings
├── database/        # DB connection & session
├── celery/          # Background tasks setup
├── main.py          # FastAPI entry point


```
## Setup Instructions
```bash

## Backend Setup
uvicorn src.main:app --reload

```
## Celery Worker
```bash
celery -A src.celery.celery_app worker --loglevel=info --pool=solo

```
## Celery Beat Scheduler
```bash
celery -A src.celery.celery_app beat --loglevel=info

```
## Frontend Setup
```bash
npm install
npm run dev## API Overview


```
## API Overview

### Authentication
- `POST /auth/register`
- `POST /auth/login`

---

### Posts
- `POST /posts`

---

### Comments
- `POST /comments`

---

### Likes
- `POST /likes`

---

### Follow System
- `POST /follow/{user_id}`

---

### Search
- `GET /search/users?q=username`

---


---

## Database Design

### Users
- id
- email
- username
- password_hash
- is_private
- bio
- profile_picture
- created_at

---

### Posts
- id
- user_id
- caption
- created_at

---

### Post Images
- id
- post_id
- image_url

---

### Comments
- id
- post_id
- user_id
- content

---

### Likes
- user_id
- post_id (composite key)

---

### Followers
- follower_id
- followee_id
- status (pending / accepted)

---

### Stories
- id
- user_id
- media_url
- created_at
- expires_at

---

## Background Jobs
```bash


- Story auto-deletion after 24 hours
- Email verification handling
- Async processing via Celery

---
```
## Non-Functional Requirements
```bash

- JWT authentication with expiry control
- Password hashing using bcrypt
- Rate limiting on login attempts
- Stateless backend architecture
- Cloud-based media storage
- Scalable async processing system

---
```
## Future Improvements
```bash
- Direct messaging system
- Reels / video feed
- Notifications system
- AI-based recommendations

---
```
## Requirements
```bash
- Python 3.10+
- Node.js 16+
- PostgreSQL
- Redis

```
