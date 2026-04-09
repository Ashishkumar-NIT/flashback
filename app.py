from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_mail import Mail, Message
from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# Flask-Mail config
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)

email_tracker = {}

def fetch_muffinlabs(month, day):
    try:
        r = requests.get(f"http://history.muffinlabs.com/date/{month}/{day}", timeout=5)
        data = r.json()["data"]
        return {"events": data["Events"][:3], "births": data["Births"][:3]}
    except:
        return {"events": [{"year": "N/A", "text": "Archives unavailable for this edition."}], "births": []}

def fetch_wiki_births(month, day):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/births/{month:02}/{day:02}"
        r = requests.get(url, headers={"User-Agent": "BirthdayApp/1.0"}, timeout=5)
        births = r.json().get("births", [])
        return [b for b in births if b.get("text")][:5]
    except:
        return [{"text": "Birth records unavailable."}]

def fetch_wiki_events(month, day):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month:02}/{day:02}"
        r = requests.get(url, headers={"User-Agent": "BirthdayApp/1.0"}, timeout=5)
        return r.json().get("events", [])[:3]
    except:
        return []

def calculate_stats(birthdate, birth_year):
    today = datetime.today()
    days_alive = (today - birthdate).days
    age = today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )
    population = 2_500_000_000 + ((birth_year - 1950) * 80_000_000)
    return {
        "days_alive": f"{days_alive:,}",
        "hours_alive": f"{days_alive * 24:,}",
        "age": age,
        "population": f"{population / 1_000_000_000:.2f} Billion"
    }

def get_birthday_data(dob_str):
    try:
        birthdate = datetime.strptime(dob_str, "%Y-%m-%d")
    except:
        return None, "Invalid date. Please try again."

    if birthdate.year < 1950 or birthdate.year > 2010:
        return None, "Please enter a date between 1950 and 2010."

    month, day, year = birthdate.month, birthdate.day, birthdate.year

    with ThreadPoolExecutor(max_workers=3) as executor:
        f1 = executor.submit(fetch_muffinlabs, month, day)
        f2 = executor.submit(fetch_wiki_births, month, day)
        f3 = executor.submit(fetch_wiki_events, month, day)
        muffin_data = f1.result()
        wiki_births = f2.result()
        wiki_events = f3.result()

    stats = calculate_stats(birthdate, year)

    return {
        "dob": dob_str,
        "formatted_date": birthdate.strftime("%B %d, %Y"),
        "events": muffin_data["events"],
        "wiki_events": wiki_events,
        "famous_births": wiki_births,
        "stats": stats
    }, None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/results", methods=["POST"])
def results():
    dob_str = request.form.get("dob")
    data, error = get_birthday_data(dob_str)
    if error:
        flash(error)
        return redirect(url_for("index"))

    return render_template("result.html",
        dob=data["dob"],
        formatted_date=data["formatted_date"],
        events=data["events"],
        wiki_events=data["wiki_events"],
        famous_births=data["famous_births"],
        stats=data["stats"]
    )

@app.route("/compare")
def compare():
    date1_str = request.args.get("date1")
    date2_str = request.args.get("date2")
    
    if not date1_str or not date2_str:
        return redirect(url_for("index"))
        
    data1, error1 = get_birthday_data(date1_str)
    data2, error2 = get_birthday_data(date2_str)
    
    if error1 or error2:
        flash("Invalid dates for comparison.")
        return redirect(url_for("index"))
        
    bd1 = datetime.strptime(date1_str, "%Y-%m-%d")
    bd2 = datetime.strptime(date2_str, "%Y-%m-%d")
    
    older = 1 if bd1 < bd2 else 2 if bd2 < bd1 else 0
    days_apart = abs((bd1 - bd2).days)
    
    return render_template("compare.html", data1=data1, data2=data2, older=older, days_apart=days_apart)

@app.route("/send-email", methods=["POST"])
def send_email():
    ip = request.remote_addr
    today = datetime.today().date().isoformat()
    key = f"{ip}_{today}"
    email_tracker[key] = email_tracker.get(key, 0) + 1
    if email_tracker[key] > 3:
        return jsonify({"success": False, "message": "Limit reached. Max 3 emails per day."})

    data = request.get_json()
    email = data.get("email")
    dob = data.get("dob")
    if not email or "@" not in email:
        return jsonify({"success": False, "message": "Invalid email."})
    try:
        msg = Message(
            subject=f"Your Birthday Times — {dob}",
            sender=("The Birthday Times", os.getenv("MAIL_USER")),
            recipients=[email]
        )
        msg.html = f"<h1>Your Birthday Times</h1><p>Born on: {dob}</p>"
        mail.send(msg)
        return jsonify({"success": True, "message": "Sent! Check your inbox."})
    except:
        return jsonify({"success": False, "message": "Failed to send email."})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=False)
