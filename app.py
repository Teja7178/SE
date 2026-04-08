import os
from flask import Flask
from models import db, Hobby
from routes import main, socketio

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

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ultra_pro_max_secret')
    # Using Render's ephemeral filesystem for sqlite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialization
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Registering Blueprint
    app.register_blueprint(main)
    
    # Ensure the instance folder exists (crucial for Render since it's not in GitHub)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Initialize the database here so it works on Render
    with app.app_context():
        db.create_all()
        seed_hobbies()
        
    return app

app = create_app()

if __name__ == "__main__":
    print("🚀 Campus Hobby Connector is running!")
    port = int(os.environ.get("PORT", 5000))
    # Turn off debug mode on Render to prevent the reloader from crashing
    debug_mode = os.environ.get("RENDER") is None
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port)
