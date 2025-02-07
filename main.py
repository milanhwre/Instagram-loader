from flask import Flask, render_template_string, request
import time
from io import StringIO
from instagrapi import Client

app = Flask(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt'}

# Function to check if file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to log in to Instagram
def instagram_login(username, password):
    cl = Client()
    try:
        cl.login(username, password)
        return cl
    except Exception as e:
        return f"Login failed: {e}"

# Function to send a message to inbox
def send_inbox_message(cl, target_username, messages, hater_name, delay):
    try:
        user_id = cl.user_id_from_username(target_username)
        for message in messages:
            final_message = f"{hater_name}: {message}"
            cl.direct_send(final_message, [user_id])
            time.sleep(delay)
        return "Messages sent successfully to inbox!"
    except Exception as e:
        return f"Error sending message to inbox: {e}"

# Function to send a message to group
def send_group_message(cl, thread_id, messages, hater_name, delay):
    try:
        for message in messages:
            final_message = f"{hater_name}: {message}"
            cl.direct_send(final_message, thread_ids=[thread_id])
            time.sleep(delay)
        return "Messages sent successfully to group!"
    except Exception as e:
        return f"Error sending message to group: {e}"

# Frontend (HTML) Template
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anish Instagram Message Sender</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: auto; background-color: white; padding: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }
        h2 { text-align: center; color: #333; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; color: #333; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
        .form-group input[type="submit"] { background-color: #4CAF50; color: white; cursor: pointer; border: none; }
        .form-group input[type="submit"]:hover { background-color: #45a049; }
        .error { color: red; }
        .result { color: green; }
    </style>
</head>
<body>
    <div class="container">
        <h2> Milan Instagram Message Sender</h2>

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if result %}
        <div class="result">{{ result }}</div>
        {% endif %}

        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label for="username">Instagram Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Instagram Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="form-group">
                <label for="choice">Send Message To:</label>
                <select id="choice" name="choice" required>
                    <option value="inbox">Inbox</option>
                    <option value="group">Group</option>
                </select>
            </div>
            <div class="form-group">
                <label for="hater_name">Hater's Name:</label>
                <input type="text" id="hater_name" name="hater_name" required>
            </div>
            <div class="form-group">
                <label for="file">Select Message File (.txt):</label>
                <input type="file" id="file" name="file" accept=".txt" required>
            </div>
            <div class="form-group">
                <label for="delay_seconds">Delay Between Messages (in seconds):</label>
                <input type="number" id="delay_seconds" name="delay_seconds" required>
            </div>
            <div class="form-group" id="target_group_div">
                <label for="target_username">Target Username:</label>
                <input type="text" id="target_username" name="target_username">
            </div>
            <div class="form-group" id="group_thread_div">
                <label for="thread_id">Group Thread ID:</label>
                <input type="text" id="thread_id" name="thread_id">
            </div>
            <div class="form-group">
                <input type="submit" value="Send Messages">
            </div>
        </form>
    </div>
    <script>
        // Toggle visibility based on whether user selects 'inbox' or 'group'
        document.getElementById('choice').addEventListener('change', function() {
            const targetUsernameDiv = document.getElementById('target_group_div');
            const threadIdDiv = document.getElementById('group_thread_div');
            if (this.value === 'inbox') {
                targetUsernameDiv.style.display = 'block';
                threadIdDiv.style.display = 'none';
            } else {
                targetUsernameDiv.style.display = 'none';
                threadIdDiv.style.display = 'block';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        choice = request.form['choice']
        hater_name = request.form['hater_name']
        delay_seconds = int(request.form['delay_seconds'])

        # Handle file upload
        if 'file' not in request.files:
            return render_template_string(html_template, error="No file selected.")
        file = request.files['file']
        if file.filename == '':
            return render_template_string(html_template, error="No selected file.")
        if file and allowed_file(file.filename):
            # Read the content of the uploaded file directly from memory
            file_content = file.stream.read().decode("utf-8")
            messages = file_content.splitlines()

            # Login to Instagram
            cl = instagram_login(username, password)
            if isinstance(cl, str):  # If login failed, return error message
                return render_template_string(html_template, error=cl)

            # Send messages based on choice
            if choice == 'inbox':
                target_username = request.form['target_username']
                result = send_inbox_message(cl, target_username, messages, hater_name, delay_seconds)
                return render_template_string(html_template, result=result)
            elif choice == 'group':
                thread_id = request.form['thread_id']
                result = send_group_message(cl, thread_id, messages, hater_name, delay_seconds)
                return render_template_string(html_template, result=result)
            else:
                return render_template_string(html_template, error="Invalid choice! Please select either 'inbox' or 'group'.")
        else:
            return render_template_string(html_template, error="Invalid file type. Only .txt files are allowed.")

    return render_template_string(html_template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
