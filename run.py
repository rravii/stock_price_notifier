from app import app, db, start_alerts

if __name__ == '__main__':
     with app.app_context():
        db.create_all()
        start_alerts()
        app.run(debug=True)