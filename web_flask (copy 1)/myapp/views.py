from flask import Blueprint, render_template, request, url_for, redirect, session, flash, jsonify
from myapp.database import *
from functools import wraps
from datetime import datetime
# import pandas as pd
# import matplotlib.pyplot as plt
from myapp import socket

views = Blueprint('views', __name__, static_folder='static',
                  template_folder='templates', static_url_path="/")


# Login decorator to ensure user is logged in before accessing certain routes
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("views.login"))
        return f(*args, **kwargs)

    return decorated


# Index route, this route redirects to login/register page
@views.route("/", methods=["GET", "POST"])
def index():
    """
    Redirects to the login/register page.

    Returns:
        Response: Flask response object.
    """
    return redirect(url_for("views.home_page"))


@views.route('/home_page')
def home_page():
    return render_template("index.html")


# Register a new user and hash password
@views.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles user registration and password hashing.

    Returns:
        Response: Flask response object.
    """
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("User already exists with that username.")
            return redirect(url_for("views.login"))

        # Create a new user
        new_user = User(username=username, email=email, password=password)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        default_user = User.query.filter_by(username="omze").first()
        if not default_user:
            flash("Default user 'omze' not found in database.")
            return redirect(url_for("views.register"))

        # Create default welcome message
        welcome_chat_list = [
            {
                "sender": "omze",
                "message": "Welcome to OMZE Chat! Let me know if you need any help getting started.",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]

        # Create a new chat between new user and omze
        default_chat = Chat(user_id=new_user.id, other_user_id=default_user.id, chat_list=welcome_chat_list)
        db.session.add(default_chat)
        db.session.commit()

        flash("Registration successful.")
        return redirect(url_for("views.login"))

    return render_template("auth.html")


@views.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user login and session creation.

    Returns:
        Response: Flask response object.
    """
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Query the database for the inputted email address
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Create a new session for the newly logged-in user
            session["user"] = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
            session['logged_in'] = True
            session['username'] = user.username
            return redirect(url_for("views.chat"))
        else:
            flash("Invalid login credentials. Please try again.")
            return redirect(url_for("views.login"))

    return render_template("auth.html")


@views.route("/new-chat", methods=["POST"])
@login_required
def new_chat():
    """
    Creates a new chat room and adds users to the chat list.

    Returns:
        Response: Flask response object.
    """
    user_id = session["user"]["id"]
    new_chat_email = request.form["email"].strip().lower()

    # If user is trying to add themselves, do nothing
    if new_chat_email == session["user"]["email"]:
        return redirect(url_for("views.chat"))

    # Check if the recipient user exists
    recipient_user = User.query.filter_by(email=new_chat_email).first()
    if not recipient_user:
        return redirect(url_for("views.chat"))

    # Check if the chat already exists
    existing_chat = Chat.query.filter_by(user_id=user_id).first()
    if not existing_chat:
        existing_chat = Chat(user_id=user_id, chat_list=[])
        db.session.add(existing_chat)
        db.session.commit()

    # Check if the new chat is already in the chat list
    if recipient_user.id not in [user_chat["user_id"] for user_chat in existing_chat.chat_list]:
        # Generate a room_id (you may use your logic to generate it)
        room_id = str(int(recipient_user.id) + int(user_id))[-4:]

        # Add the new chat to the chat list of the current user
        updated_chat_list = existing_chat.chat_list + \
            [{"user_id": recipient_user.id, "room_id": room_id}]
        existing_chat.chat_list = updated_chat_list

        # Save the changes to the database
        existing_chat.save_to_db()

        # Create a new chat list for the recipient user if it doesn't exist
        recipient_chat = Chat.query.filter_by(
            user_id=recipient_user.id).first()
        if not recipient_chat:
            recipient_chat = Chat(user_id=recipient_user.id, chat_list=[])
            db.session.add(recipient_chat)
            db.session.commit()

        # Add the new chat to the chat list of the recipient user
        updated_chat_list = recipient_chat.chat_list + \
            [{"user_id": user_id, "room_id": room_id}]
        recipient_chat.chat_list = updated_chat_list
        recipient_chat.save_to_db()

        # Create a new message entry for the chat room
        # Create a new message entry with a default message
        default_message = Message(
            room_id=room_id,
            sender_id=user_id,
            content="""hi, this omze homes and propertie.
            how can we help""",
            timestamp=datetime.utcnow()  # import datetime from datetime
        )
        db.session.add(default_message)
        db.session.commit()

    return redirect(url_for("views.chat"))


@views.route("/chat/", methods=["GET", "POST"])
@login_required
def chat():
    """
    Renders the chat interface and displays chat messages.

    Returns:
        Response: Flask response object.
    """
    # Get the room id in the URL or set to None
    room_id = request.args.get("rid", None)

    # Get the chat list for the user
    current_user_id = session["user"]["id"]
    current_user_chats = Chat.query.filter_by(user_id=current_user_id).first()
    chat_list = current_user_chats.chat_list if current_user_chats else []

    # Initialize context that contains information about the chat room
    data = [{"room_id": 1, "email": "johnpaulogirima156@gmail.com", "last_message": "Hello", "welcome_message": "Welcome to our chat!"},
            {"room_id": 2, "email": "user2@example.com", "last_message": "Hi",
                "welcome_message": "Welcome to our chat!"}
            ]

    for chat in chat_list:
        # Query the database to get the username of users in a user's chat list
        user = User.query.get(chat["user_id"])
        username = user.username
        email = user.email  # Get the email of the user
        is_active = room_id == chat["room_id"]

        try:
            # Get the Message object for the chat room
            message = Message.query.filter_by(room_id=chat["room_id"]).first()

            # Get the last ChatMessage object in the Message's messages relationship
            last_message = message.messages[-1]

            # Get the message content of the last ChatMessage object
            last_message_content = last_message.content
        except (AttributeError, IndexError):
            # Set variable to this when no messages have been sent to the room
            last_message_content = "This place is empty. No messages ..."

        # Append room data including the email
        data.append({
            "username": username,
            "room_id": chat["room_id"],
            "is_active": is_active,
            "last_message": last_message_content,
            "email": email,  # Add the email to the data
        })

    # Get all the message history in a certain room
    messages = Message.query.filter_by(
        room_id=room_id).first().messages if room_id else []

    return render_template(
        "chat.html",
        user_data=session["user"],
        room_id=room_id,
        data=data,
        messages=messages,
    )

# Custom time filter to be used in the jinja template


@views.app_template_filter("ftime")
def ftime(date):
    dt = datetime.fromtimestamp(int(date))
    time_format = "%I:%M %p"  # Use  %I for 12-hour clock format and %p for AM/PM
    formatted_time = dt.strftime(time_format)

    formatted_time += " | " + dt.strftime("%m/%d")
    return formatted_time


@views.route('/visualize')
def visualize():
    """
    TODO: Utilize pandas and matplotlib to analyze the number of users registered to the app.
    Create a chart of the analysis and convert it to base64 encoding for display in the template.

    Returns:
        Response: Flask response object.
    """
    pass


@views.route('/get_name')
def get_name():
    """
    :return: json object with username
    """
    data = {'name': ''}
    if 'username' in session:
        data = {'name': session['username']}

    return jsonify(data)


@views.route('/get_messages')
def get_messages():
    """
    query the database for messages o in a particular room id
    :return: all messages
    """
    pass


@views.route('/tutorial')
def tutorial():
    # if not session.get('logged_in'):
    #     return redirect(url_for('login'))
    return render_template("tutorials.html")

# Resources page route


@views.route('/resources')
def resources():
    # if not session.get('logged_in'):
    #     return redirect(url_for('login'))
    return render_template("software.html")


@views.route('/leave')
def leave():
    """
    Emits a 'disconnect' event and redirects to the home page.

    Returns:
        Response: Flask response object.
    """
    socket.emit('disconnect')
    return redirect(url_for('views.home'))


@views.route("/logout")
@login_required
def logout():
    """
    Logs the user out by clearing the session.

    Returns:
        Response: Flask response object.
    """
    session.clear()  # This will remove all data stored in the session
    flash("You have been logged out.")
    return redirect(url_for("views.index"))

# Load messages (AJAX)


@views.route('/load_messages/<int:room_id>')
@login_required
def load_messages(room_id):
    messages = Message.query.filter_by(
        room_id=room_id).order_by(Message.timestamp).all()

    messages_data = []
    for msg in messages:
        messages_data.append({
            "sender_username": msg.sender_username,
            "content": msg.content,
            "timestamp": msg.timestamp.strftime("%I:%M %p | %m/%d")
        })

    return jsonify({"messages": messages_data})
