# WebScraper Pro

A professional Django-based web scraping application with a clean dark UI, authentication, CSS selector targeting, and CSV/JSON export.

## 🚀 Quick Start

### 1. Setup (Windows)
```batch
cd django_web_scraper
setup.bat
```

### 1. Setup (Linux / macOS)
```bash
cd django_web_scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 2. Run the server
```bash
# Activate venv first
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/macOS

python manage.py runserver
```

### 3. Open in browser
- **App**: http://127.0.0.1:8000
- **Admin**: http://127.0.0.1:8000/admin

---

## ✨ Features

| Feature | Detail |
|---|---|
| 🔐 Authentication | Django login/logout — all pages protected |
| 🎯 CSS Selectors | Target any HTML element (e.g. `h1`, `.title`, `a[href]`) |
| 📦 Attribute Extraction | Inner text, `href`, `src`, `alt`, and more |
| 🔁 Retry Logic | 3 auto-retries with exponential back-off |
| 🤖 User-Agent Rotation | 5 modern browser UA strings |
| 📊 Dashboard | Live job stats and status indicators |
| 📁 Export | Download results as **CSV** or **JSON** |
| 🗑️ Clear Results | Reset results without deleting the job |
| 🛡️ Admin Panel | Full CRUD via Django Admin |
| 📄 Pagination | 25 results per page |

---

## 🧪 Test with a Demo Site

1. Log in → **New Job**
2. Fill in:
   - **Name**: `Quotes Scraper`
   - **URL**: `https://quotes.toscrape.com`
   - **CSS Selector**: `.quote .text`
   - **Extract**: `Inner Text`
3. Click **Run Scraper**
4. View results → export as CSV

---

## 📁 Project Structure

```
django_web_scraper/
├── manage.py
├── requirements.txt
├── setup.bat
├── .env
├── web_scraper/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── scraper/
    ├── models.py          ← ScrapeJob, ScrapeResult
    ├── views.py           ← All views (login_required)
    ├── forms.py           ← ScrapeJobForm
    ├── scraper_engine.py  ← requests + BeautifulSoup4 core
    ├── admin.py
    ├── urls.py
    └── templates/scraper/
        ├── base.html
        ├── login.html
        ├── dashboard.html
        ├── job_form.html
        └── job_detail.html
```

---

## ⚠️ Ethical Usage

Always check a website's `robots.txt` and Terms of Service before scraping. This tool is intended for legal, ethical data collection only.
