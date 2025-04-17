from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import random
from datetime import datetime
from collections import Counter

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Paths
base_path = os.path.dirname(os.path.abspath(__file__))
login_file = os.path.join(base_path, 'login_data.csv')
login_stats_file = os.path.join(base_path, 'login_stats.csv')

# Create login file if it doesn't exist
if not os.path.exists(login_file):
    pd.DataFrame(columns=["email", "password"]).to_csv(login_file, index=False)

# Create login stats file if it doesn't exist
if not os.path.exists(login_stats_file):
    pd.DataFrame(columns=["timestamp"]).to_csv(login_stats_file, index=False)

# Career tiers and mappings
career_map = {
    "low": ["Artist", "Photographer", "Game Developer", "Content Creator", "Event Planner", "Animator", "Blogger", "Social Media Manager"],
    "medium": ["Teacher", "Graphic Designer", "Writer", "Journalist", "Marketing Executive", "Public Relations Officer", "Accountant", "Interior Designer"],
    "high": ["Software Engineer", "Civil Engineer", "Data Scientist", "Economist", "Mechanical Engineer", "Electrical Engineer", "UX/UI Designer", "Product Manager"],
    "top": ["Doctor", "Lawyer", "Pilot", "Researcher", "Scientist", "Cybersecurity Specialist", "Architect", "Financial Analyst"]
}

college_map = {
    "Doctor": ["top : AIIMS Nagpur", "BJMC Pune","gmc latur"],
    "Lawyer": ["GLC Mumbai", "ILS Pune"],
    "Pilot": ["IGIA Pune"],
    "Researcher": ["IIT Bombay", "TIFR"],
    "Scientist": ["IIT Bombay", "TIFR Mumbai"],
    "Cybersecurity Specialist": ["MIT Pune", "VJTI Mumbai"],
    "Architect": ["JJ School of Architecture Mumbai"],
    "Financial Analyst": ["NMIMS Mumbai", "Symbiosis Pune"],
    "Software Engineer": ["IIT Bombay", "COEP Pune"],
    "Civil Engineer": ["IIT Bombay", "VJTI Mumbai"],
    "Data Scientist": ["IIT Bombay", "NMIMS"],
    "Economist": ["Gokhale Institute"],
    "Mechanical Engineer": ["COEP Pune", "VJTI Mumbai"],
    "Electrical Engineer": ["VJTI Mumbai", "IIT Bombay"],
    "UX/UI Designer": ["MIT ID Pune"],
    "Product Manager": ["IIM Nagpur", "SP Jain Mumbai"],
    "Teacher": ["TISS", "St. Xavier's"],
    "Graphic Designer": ["MIT ID Pune"],
    "Writer": ["Flame University", "Mumbai University"],
    "Journalist": ["XIC", "Symbiosis Pune"],
    "Marketing Executive": ["NMIMS Mumbai", "Symbiosis Pune"],
    "Public Relations Officer": ["XIC Mumbai", "MIT WPU"],
    "Accountant": ["NM College Mumbai", "BMCC Pune"],
    "Interior Designer": ["Rachana Sansad Mumbai", "MIT ID Pune"],
    "Artist": ["JJ School of Art"],
    "Photographer": ["MIT ID Pune"],
    "Game Developer": ["Seamedu Pune"],
    "Content Creator": ["Whistling Woods Mumbai"],
    "Event Planner": ["NIEM Pune"],
    "Animator": ["MAAC Pune", "Arena Animation Mumbai"],
    "Blogger": ["Flame University"],
    "Social Media Manager": ["Symbiosis Pune", "XIC Mumbai"]
}

def predict_profession(total):
    if total >= 630:
        tier = "top"
    elif total >= 560:
        tier = "high"
    elif total >= 490:
        tier = "medium"
    else:
        tier = "low"

    seed = total * 17
    random.seed(seed)
    professions = random.sample(career_map[tier], min(7, len(career_map[tier])))

    profession_college_map = {
        prof: [{"name": college, "url": f"https://www.google.com/search?q={college.replace(' ', '+')}"} for college in college_map.get(prof, [])]
        for prof in professions
    }

    return professions, profession_college_map

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    message = None
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        action = request.form['action']
        login_data = pd.read_csv(login_file)

        if action == 'login':
            user = login_data[(login_data['email'] == email) & (login_data['password'] == password)]
            if not user.empty:
                session['email'] = email
                pd.DataFrame([[datetime.now().strftime('%Y-%m-%d')]], columns=["timestamp"]).to_csv(login_stats_file, mode='a', header=False, index=False)
                return redirect(url_for('marks_form'))
            else:
                error = "Invalid email or password"

        elif action == 'register':
            if not login_data[login_data['email'] == email].empty:
                error = "Email already registered."
            else:
                pd.DataFrame([[email, password]], columns=['email', 'password']).to_csv(login_file, mode='a', header=False, index=False)
                session['email'] = email
                return redirect(url_for('marks_form'))

    return render_template('login.html', error=error, message=message)

@app.route('/marks', methods=['GET', 'POST'])
def marks_form():
    if request.method == 'POST':
        try:
            scores = [int(request.form[subject]) for subject in ['math', 'history', 'physics', 'chemistry', 'biology', 'english', 'geography']]
            gender = request.form['gender']
            job = request.form['job']
            absences = int(request.form['absences'])
            activities = request.form['activities']
            study_hours = int(request.form['study_hours'])

            total = sum(scores)
            average = total / len(scores)

            professions, profession_college_map = predict_profession(total)

            session['result'] = {
                "total": total,
                "average": average,
                "professions": professions,
                "profession_college_map": profession_college_map
            }

            return redirect(url_for('result'))
        except ValueError:
            return "⚠️ Invalid input. Please enter valid numbers."
    return render_template('marks_form.html')

@app.route('/result')
def result():
    if 'result' not in session:
        return redirect(url_for('marks_form'))
    return render_template('result.html', **session['result'])

@app.route('/logout')
def logout():
    if 'email' in session:
        email = session['email']
        df = pd.read_csv(login_file)
        df = df[df['email'] != email]
        df.to_csv(login_file, index=False)
    session.clear()
    return redirect(url_for('login'))

@app.route('/user-stats')
def user_stats():
    if not os.path.exists(login_stats_file):
        return "No login stats available."

    df = pd.read_csv(login_stats_file)
    date_counts = dict(Counter(df['timestamp']))
    sorted_dates = sorted(date_counts.items())
    dates = [item[0] for item in sorted_dates]
    counts = [item[1] for item in sorted_dates]

    average_logins = round(sum(counts) / len(counts), 2) if counts else 0
    peak_day = dates[counts.index(max(counts))] if counts else "N/A"
    peak_count = max(counts) if counts else 0

    return render_template(
        'user_stats.html',
        dates=dates,
        counts=counts,
        average_logins=average_logins,
        peak_day=peak_day,
        peak_count=peak_count
    )

if __name__ == '__main__':
    app.run(debug=True)
