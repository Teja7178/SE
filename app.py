import os
from flask import Flask
from models import db, Hobby
from routes import main, socketio

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ultra_pro_max_secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialization
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Registering Blueprint
    app.register_blueprint(main)
    
    return app

app = create_app()

def seed_hobbies():
    """Seed initial hobbies if they do not exist."""
    initial_hobbies = [
        "Photography", "Coding", "Reading", "Gaming", 
        "Traveling", "Music", "Cooking", "Sports", 
        "Art & Design", "Fitness", "Movies", "Writing"
    ]
    
    existing_hobbies = [h.name for h in Hobby.query.all()]
    for h_name in initial_hobbies:
        if h_name not in existing_hobbies:
            new_hobby = Hobby(name=h_name)
            db.session.add(new_hobby)
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_hobbies()
        
    print("🚀 Campus Hobby Connector is running!")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)