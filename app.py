from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecretkey")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "shivasaimoghekar@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "bnzm onws onwo gdca")

def send_email(receiver_email, asset_name, expiry_date):
    subject = f"Alert: {asset_name} is Expiring Soon"
    body = f"Dear User,\n\nYour asset '{asset_name}' is expiring on {expiry_date.date()}. Please take necessary action.\n\nBest Regards,\nIT Asset Management Team"
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            flash("File uploaded successfully!", "success")
            return redirect(url_for('view_assets', filename=file.filename))
    return render_template('upload.html')

@app.route('/assets/<filename>')
def view_assets(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path)
    df["Expiry Date"] = pd.to_datetime(df["Expiry Date"].str.split().str[0], errors='coerce')

    
    current_date = datetime.today()
    expiring_assets = df[df["Expiry Date"] <= (current_date + timedelta(days=30))]
    
    fig = px.histogram(df, x="Expiry Date", title="Asset Expiry Distribution", nbins=30)
    graph_html = pio.to_html(fig, full_html=False)
    
    return render_template('assets.html', tables=[df.to_html(classes='table table-striped', index=False)],
                           graph_html=graph_html, filename=filename, expiring_assets=expiring_assets)

@app.route('/send_alerts/<filename>')
def send_alerts(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(file_path)
    df["Expiry Date"] = pd.to_datetime(df["Expiry Date"].str.split().str[0], errors='coerce')

    
    current_date = datetime.today()
    expiring_assets = df[df["Expiry Date"] <= (current_date + timedelta(days=30))]
    
    for _, row in expiring_assets.iterrows():
        send_email(row["Owner Email"], row["Asset"], row["Expiry Date"])
    
    flash("Emails sent successfully!", "success")
    return redirect(url_for('view_assets', filename=filename))

if __name__ == '__main__':
    app.run(debug=True)
