import sys
from main import app, db, server_session
import dashboard # Import dashboard here to register its routes

if __name__ == "__main__":
    if "--setup" in sys.argv:
        with app.app_context():
            db.create_all()
            db.session.commit()
            print("Database tables created")
    else:
        app.run(host='0.0.0.0', debug=True)