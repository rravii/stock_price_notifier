# Import necessary modules
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
import time
import threading
import smtplib
from twilio.rest import Client

# Initialize Flask app and database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alerts.db' # specifies the database URI for SQLAlchemy to use
db = SQLAlchemy(app) # creates a SQLAlchemy object that connects to the database

# Define the Alert database model
class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True) # unique identifier for the alert
    ticker = db.Column(db.String(10), nullable=False) # stock ticker symbol to monitor
    threshold = db.Column(db.Float, nullable=False) # price threshold for the alert
    frequency = db.Column(db.String(20), nullable=False) # frequency to check the stock price
    notification_type = db.Column(db.String(20), nullable=False) # method of notification (email or text)
    email = db.Column(db.String(50), nullable=False) # email address to send notifications to
    phone_number = db.Column(db.String(15), nullable=False) # phone number to send notifications to

    def __repr__(self):
        return f"Alert(ticker={self.ticker}, threshold={self.threshold}, frequency={self.frequency}, notification_type={self.notification_type}, email={self.email}, phone_number={self.phone_number})"

# Define the Flask route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    # If a user submits the alert form
    if request.method == 'POST':
        # Get the alert details from the form
        ticker = request.form['ticker']
        threshold = request.form['threshold']
        frequency = request.form['frequency']
        notification_type = request.form['notification_type']
        email = request.form['email']
        phone_number = request.form['phone']

        # Create a new Alert object with the form data and add it to the database
        alert = Alert(ticker=ticker, threshold=threshold, frequency=frequency, notification_type=notification_type, email=email, phone_number=phone_number)
        db.session.add(alert)
        db.session.commit()

        # Start checking the stock price for the new alert in a new thread
        start_alerts()

        # Return a success message to the user
        return '''
        <div id="alert" style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
          <h3>Alert created successfully!</h3>
        </div>
        <script>
          setTimeout(function() {
            window.location.href = "/";
          }, 3000);
        </script>
        '''

    # If the user navigates to the home page
    return render_template('index.html') # render the index.html template

# Define a function to get the current stock price for a given ticker
def get_stock_price(ticker):
    stock = yf.Ticker(ticker).history(period='1d')
    return stock['Close'].iloc[-1]

# Define a dictionary to convert frequency strings to seconds
FREQUENCY_TO_SECONDS = {
    'minute':60,
    'hourly': 3600,
    'daily': 86400
}

# Define a function to check the stock price for a given alert
def check_stock_price(alert):
    while True:
        ticker = alert.ticker
        threshold = alert.threshold
        price = get_stock_price(ticker)
        if price >= float(threshold):
            send_notification(alert.notification_type, alert.email, alert.phone_number, ticker, price)
        frequency_seconds = FREQUENCY_TO_SECONDS[alert.frequency]
        time.sleep(frequency_seconds)

def start_alerts():
    alerts = Alert.query.all()
    for alert in alerts:
        thread = threading.Thread(target=check_stock_price, args=(alert,))
        thread.start()

import smtplib

def send_email_notification(email, ticker, price):
    # Set up the email message
    message = f"Subject: Stock Alert: {ticker}\n\nThe price of {ticker} has reached {price}."

    # Replace the placeholders with your email and password
    from_email = 'your_email'
    from_password = 'your_email_password'

    # Connect to the SMTP server and log in
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(from_email, from_password)

        # Send the email
        server.sendmail(from_email, email, message)

def send_notification(notification_type, user_email, phone_number, ticker, price):
    if notification_type == 'email':
        send_email_notification(user_email, ticker, price)
    elif notification_type == 'text':
        send_sms_notification(phone_number, ticker, price)
    else:
        raise ValueError(f"Invalid notification type: {notification_type}")
    
from twilio.rest import Client

def send_sms_notification(phone_number, ticker, price):
    account_sid = 'your_account_sid'
    auth_token = 'your_auth_token'
    client = Client(account_sid, auth_token)

    message = f"ALERT: {ticker} is now at {price}!"
    message = client.messages.create(
        to=phone_number,
        from_='your_twilio_number',  # Replace with your Twilio phone number
        body=message)

    print(f"Sent SMS notification to {phone_number}: {message.sid}")
