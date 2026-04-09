# The Birthday Times

A full-stack web application that takes your date of birth and generates a vintage newspaper-style dashboard showing what the world looked like on the exact day you were born.

## Features
- **Vintage Newspaper UI:** Raw HTML and Vanilla CSS design with sepia paper background and columns.
- **Historical Events:** Fetches historical events and famous births happening on your exact birthdate.
- **Real-Time Assembly:** Pulls aggregated information in parallel using multiple data sources.
- **Compare:** Compare your newspaper edition with another date side-by-side.
- **Save & Share:** Download the generated newspaper as an image or email it directly.

## Tech Stack
- **Backend:** Python + Flask
- **Data Gathering:** Wikipedia API & Muffinlabs API via Python `requests` (in parallel)
- **Email Delivery:** Flask-Mail + Gmail SMTP
- **Frontend:** Vanilla HTML, CSS, JavaScript
- **Templating:** Jinja2

## Setup Instructions

1. Clone the repository:
```bash
git clone <your-repo>
cd birthday_times
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Fill in `.env` with your secure values. For Gmail, use an App Password.

4. Run the application locally:
```bash
python app.py
```

5. Open [http://localhost:5000](http://localhost:5000) in your browser.
