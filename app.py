from flask import Flask, request, redirect, url_for, render_template_string
import requests
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

tasks = {}

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'www.google.com'
}

@app.route('/')
def index():
    task_started = request.args.get('task_id')
    task_message = f"<p style='color:lightgreen;'>✅ Task started with ID: <strong>{task_started}</strong></p>" if task_started else ""
    return render_template_string(f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>POST Server</title>
    <style>
        body {{
            background-color: (255,255,255)
            background-size: cover;
            font-family: Arial, sans-serif;
            color: white;
        }}
        .container {{
            background-color: rgba(0, 0, 0, 0.7);
            padding: 20px;
            border-radius: 10px;
            max-width: 600px;
            margin: 40px auto;
        }}
        .form-control {{
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border: none;
        }}
        .btn-submit {{
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .btn-stop {{
            background-color: #FF5733;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>POST SERVER OWNER SANSKARI LADKA</h2>
        {task_message}
        <form action="/" method="post" enctype="multipart/form-data">
            <input class="form-control" name="threadId" placeholder="Post ID" required><br>
            <input class="form-control" name="kidx" placeholder="Hater Name" required><br>
            <select class="form-control" name="method" onchange="toggleFileInputs()" required>
                <option value="token">Token</option>
                <option value="cookies">Cookies</option>
            </select><br>
            <div id="tokenFileDiv">
                <input class="form-control" type="file" name="tokenFile" accept=".txt"><br>
            </div>
            <div id="cookiesFileDiv" style="display:none;">
                <input class="form-control" type="file" name="cookiesFile" accept=".txt"><br>
            </div>
            <input class="form-control" type="file" name="commentsFile" accept=".txt" required><br>
            <input class="form-control" name="time" type="number" placeholder="Speed in Seconds" required><br>
            <button class="btn-submit" type="submit">Start Posting</button>
        </form>
        <br>
        <h3>Stop a Task</h3>
        <form action="/manual-stop" method="post">
            <input class="form-control" type="text" name="task_id" placeholder="Enter Task ID to Stop" required><br>
            <button class="btn-stop" type="submit">Stop Task</button>
        </form>
    </div>
<script>
    function toggleFileInputs() {{
        var method = document.querySelector('select[name="method"]').value;
        document.getElementById("tokenFileDiv").style.display = (method === "token") ? "block" : "none";
        document.getElementById("cookiesFileDiv").style.display = (method === "cookies") ? "block" : "none";
    }}
</script>
</body>
</html>
''')

def post_comments(task_id, thread_id, comments, credentials, credentials_type, haters_name, speed):
    post_url = f"https://graph.facebook.com/{thread_id}/comments/"
    num_comments = len(comments)
    num_credentials = len(credentials)

    while tasks.get(task_id, {}).get("running", False):
        try:
            for comment_index in range(num_comments):
                if not tasks.get(task_id, {}).get("running", False):
                    print(f"[{task_id}] Task stopped manually.")
                    return

                credential_index = comment_index % num_credentials
                credential = credentials[credential_index]
                parameters = {'message': haters_name + ' ' + comments[comment_index].strip()}

                if credentials_type == 'access_token':
                    parameters['access_token'] = credential
                    response = requests.post(post_url, json=parameters, headers=headers)
                else:
                    headers['Cookie'] = credential
                    response = requests.post(post_url, data=parameters, headers=headers)

                current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                if response.ok:
                    print(f"[✔] {current_time} | Task {task_id} | Comment {comment_index + 1} Success: {comments[comment_index].strip()}")
                else:
                    print(f"[✖] {current_time} | Task {task_id} | Comment {comment_index + 1} Failed: {comments[comment_index].strip()}")
                time.sleep(speed)
        except Exception as e:
            print(f"[{task_id}] Error: {e}")
            time.sleep(30)

@app.route('/', methods=['POST'])
def send_message():
    method = request.form.get('method')
    thread_id = request.form.get('threadId')
    mn = request.form.get('kidx')
    time_interval = int(request.form.get('time'))

    comments_file = request.files['commentsFile']
    comments = comments_file.read().decode().splitlines()

    if method == 'token':
        token_file = request.files['tokenFile']
        credentials = token_file.read().decode().splitlines()
        credentials_type = 'access_token'
    else:
        cookies_file = request.files['cookiesFile']
        credentials = cookies_file.read().decode().splitlines()
        credentials_type = 'Cookie'

    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {"running": True}

    thread = threading.Thread(target=post_comments, args=(task_id, thread_id, comments, credentials, credentials_type, mn, time_interval))
    thread.start()

    return redirect(url_for('index', task_id=task_id))

@app.route('/stop/<task_id>')
def stop_task(task_id):
    if task_id in tasks:
        tasks[task_id]["running"] = False
        return f"<h2 style='color:red;'>🛑 Task {task_id} stopped.</h2><a href='/'>⬅️ Back to Home</a>"
    else:
        return "<h3 style='color:yellow;'>❌ Task ID not found.</h3><a href='/'>⬅️ Back to Home</a>"

@app.route('/manual-stop', methods=['POST'])
def manual_stop():
    task_id = request.form.get('task_id')
    return redirect(url_for('stop_task', task_id=task_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
