from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import db, User, Hobby, UserHobby, Match, Message, Report
from flask_bcrypt import Bcrypt
from datetime import datetime
from sqlalchemy import or_, and_

socketio = SocketIO()
main = Blueprint('main', __name__)
bcrypt = Bcrypt()

# Helper function to get current user
def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ---------------- HOME / LANDING ----------------
@main.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

# ---------------- AUTH ROUTES ----------------
@main.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Basic Check
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error="Email already exists.")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        # Log them in automatically
        session['user_id'] = new_user.id
        return redirect(url_for('main.hobbies'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            user.is_online = True
            db.session.commit()
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error="Invalid Credentials. Please try again.")

    return render_template('login.html')

@main.route('/logout')
def logout():
    user = get_current_user()
    if user:
        user.is_online = False
        db.session.commit()
    session.clear()
    return redirect(url_for('main.login'))

# ---------------- DASHBOARD ----------------
@main.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user: return redirect(url_for('main.login'))

    user_hobbies = [uh.hobby.name for uh in user.hobbies]
    
    # Quick Match Summary
    all_users = User.query.filter(User.id != user.id).all()
    user_hobby_ids = set([uh.hobby_id for uh in user.hobbies])
    top_matches = []
    
    for other_user in all_users:
        other_hobby_ids = set([uh.hobby_id for uh in other_user.hobbies])
        common = user_hobby_ids.intersection(other_hobby_ids)
        total = user_hobby_ids.union(other_hobby_ids)
        score = int((len(common) / len(total)) * 100) if len(total) > 0 else 0
        
        if score > 50: # Only return high matches for dashboard
            top_matches.append({'user': other_user, 'score': score})
            
    top_matches = sorted(top_matches, key=lambda x: x['score'], reverse=True)[:3]

    return render_template('dashboard.html', user=user, hobbies=user_hobbies, top_matches=top_matches)

# ---------------- PROFILE & HOBBIES ----------------
@main.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_current_user()
    if not user: return redirect(url_for('main.login'))

    if request.method == 'POST':
        user.bio = request.form.get('bio', '')
        user.username = request.form.get('username', user.username)
        db.session.commit()
        return redirect(url_for('main.profile'))

    user_hobbies = [uh.hobby.name for uh in user.hobbies]
    return render_template('profile.html', user=user, hobbies=user_hobbies)

@main.route('/hobbies', methods=['GET', 'POST'])
def hobbies():
    user = get_current_user()
    if not user: return redirect(url_for('main.login'))

    if request.method == 'POST':
        selected_hobbies = request.form.getlist('hobbies')
        custom_hobbies_input = request.form.get('custom_hobbies', '').strip()

        UserHobby.query.filter_by(user_id=user.id).delete()

        for hobby_id in selected_hobbies:
            new_entry = UserHobby(user_id=user.id, hobby_id=int(hobby_id))
            db.session.add(new_entry)

        if custom_hobbies_input:
            custom_names = [name.strip() for name in custom_hobbies_input.split(',') if name.strip()]
            for name in custom_names:
                hobby = Hobby.query.filter(Hobby.name.ilike(name)).first()
                if not hobby:
                    hobby = Hobby(name=name.title())
                    db.session.add(hobby)
                    db.session.flush() # get id before referencing it
                db.session.add(UserHobby(user_id=user.id, hobby_id=hobby.id))

        db.session.commit()
        return redirect(url_for('main.dashboard'))

    all_hobbies = Hobby.query.all()
    user_hobby_ids = [uh.hobby_id for uh in user.hobbies]
    
    return render_template('hobbies.html', hobbies=all_hobbies, user_hobby_ids=user_hobby_ids)

# ---------------- MATCHES ----------------
@main.route('/matches')
def matches():
    user = get_current_user()
    if not user: return redirect(url_for('main.login'))

    user_hobby_ids = set([uh.hobby_id for uh in user.hobbies])
    all_users = User.query.filter(User.id != user.id).all()
    match_results = []

    for other_user in all_users:
        other_hobby_ids = set([uh.hobby_id for uh in other_user.hobbies])
        if not other_hobby_ids: continue

        common = user_hobby_ids.intersection(other_hobby_ids)
        total = user_hobby_ids.union(other_hobby_ids)
        score = int((len(common) / len(total)) * 100) if len(total) > 0 else 0

        if score > 0:
            match_results.append({
                "user": other_user,
                "score": score,
                "common_hobbies": [Hobby.query.get(h_id).name for h_id in common]
            })

    match_results = sorted(match_results, key=lambda x: x['score'], reverse=True)
    return render_template('matches.html', matches=match_results, user=user)

# ---------------- CHAT ----------------
@main.route('/chat')
def chat_list():
    user = get_current_user()
    if not user: return redirect(url_for('main.login'))
    
    # Get all users the current user has messaged or received messages from
    sent_msgs = db.session.query(Message.receiver_id).filter_by(sender_id=user.id).distinct()
    recv_msgs = db.session.query(Message.sender_id).filter_by(receiver_id=user.id).distinct()
    
    chatted_user_ids = set([m[0] for m in sent_msgs] + [m[0] for m in recv_msgs])
    chatted_users = User.query.filter(User.id.in_(chatted_user_ids)).all() if chatted_user_ids else []

    return render_template('chat_list.html', users=chatted_users, current_user=user)

@main.route('/chat/<int:target_user_id>')
def chat(target_user_id):
    user = get_current_user()
    if not user: return redirect(url_for('main.login'))

    target_user = User.query.get_or_404(target_user_id)

    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == user.id, Message.receiver_id == target_user_id),
            and_(Message.sender_id == target_user_id, Message.receiver_id == user.id)
        )
    ).order_by(Message.timestamp.asc()).all()

    return render_template('chat.html', current_user=user, target_user=target_user, messages=messages)

# ---------------- ADMIN ----------------
@main.route('/admin')
def admin():
    # In a real app we'd check if user is admin. For now, just allow access.
    users = User.query.all()
    hobbies = Hobby.query.all()
    reports = Report.query.all()

    return render_template('admin.html', 
                           users=users, 
                           hobbies=hobbies, 
                           reports=reports,
                           total_users=len(users),
                           total_hobbies=len(hobbies),
                           total_reports=len(reports))

@main.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    UserHobby.query.filter_by(user_id=user.id).delete()
    Message.query.filter((Message.sender_id == user.id) | (Message.receiver_id == user.id)).delete()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('main.admin'))


# ================= SOCKET.IO EVENTS =================
users_online = {}

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        users_online[user_id] = request.sid
        # Join a personal room for private messaging
        room = f"user_{user_id}"
        join_room(room)
        
        user = User.query.get(user_id)
        if user:
            user.is_online = True
            db.session.commit()
            emit('user_status', {'user_id': user_id, 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        user_id = session['user_id']
        if user_id in users_online:
            del users_online[user_id]
        
        user = User.query.get(user_id)
        if user:
            user.is_online = False
            db.session.commit()
            emit('user_status', {'user_id': user_id, 'status': 'offline'}, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    sender_id = session.get('user_id')
    receiver_id = data['receiver_id']
    content = data['message']
    
    if not sender_id or not content.strip(): return

    new_msg = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(new_msg)
    db.session.commit()

    # Send to sender's and receiver's specific rooms
    msg_data = {
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'content': content,
        'timestamp': new_msg.timestamp.strftime('%I:%M %p')
    }
    emit('receive_message', msg_data, room=f"user_{receiver_id}")
    emit('receive_message', msg_data, room=f"user_{sender_id}")

@socketio.on('typing')
def handle_typing(data):
    sender_id = session.get('user_id')
    receiver_id = data['receiver_id']
    is_typing = data['is_typing']
    
    if sender_id:
        emit('user_typing', {'sender_id': sender_id, 'is_typing': is_typing}, room=f"user_{receiver_id}")
