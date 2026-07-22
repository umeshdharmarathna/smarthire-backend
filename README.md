# Smart Hire - Backend API 🚀

An on-demand local service marketplace backend built with **FastAPI**, **SQLAlchemy**, and **Supabase PostgreSQL**.

---

## 🌟 Tech Stack & Features

* **Framework**: FastAPI (Python 3.12)
* **Database**: Supabase Cloud PostgreSQL (with local MySQL / SQLite fallback)
* **Authentication**: JWT Bearer Tokens with `bcrypt` password hashing
* **AI Support**: OpenAI API integrated Support Chatbot
* **Deployment**: Vercel Serverless Functions

---

## 🚀 Live Links

* **Live API**: `https://backend-ashy-six-26.vercel.app`
* **Swagger API Docs**: `https://backend-ashy-six-26.vercel.app/docs`

---

## 🛠️ Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/umeshdharmarathna/smarthire-backend.git
   cd smarthire-backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

5. **Run the local server**:
   ```bash
   uvicorn main:app --reload
   ```
   Open `http://localhost:8000/docs` in your browser.

---

## 🔒 Security
Environment variables (`.env`) and database credentials are fully git-ignored and never committed to source control.
