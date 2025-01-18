from flask import Flask, render_template_string, request, jsonify
import threading
from datetime import datetime

app = Flask(__name__)

# Данные для отслеживания состояния
status_data = {
    "pc1": {"status": "idle", "lobby_id": None},
    "pc2": {"status": "idle", "lobby_id": None},
    "last_lobby_id": None,
    "game_history": []
}

# Блокировка для потокобезопасности
data_lock = threading.Lock()

# HTML-шаблон
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lobby Status</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f4f4f4;
        }
        .status-idle {
            color: #999;
        }
        .status-matched {
            color: green;
            font-weight: bold;
        }
        .status-waiting {
            color: orange;
            font-weight: bold;
        }
        .status-error {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Lobby Status</h1>
        <h2>Current Lobby</h2>
        <p>Last Lobby ID: <strong>{{ data.last_lobby_id }}</strong></p>
        <h2>Status</h2>
        <table>
            <tr>
                <th>PC</th>
                <th>Status</th>
                <th>Lobby ID</th>
            </tr>
            <tr>
                <td>PC1</td>
                <td class="status-{{ data.pc1.status }}">{{ data.pc1.status }}</td>
                <td>{{ data.pc1.lobby_id }}</td>
            </tr>
            <tr>
                <td>PC2</td>
                <td class="status-{{ data.pc2.status }}">{{ data.pc2.status }}</td>
                <td>{{ data.pc2.lobby_id }}</td>
            </tr>
        </table>
        <h2>Game History</h2>
        <table>
            <tr>
                <th>Date</th>
                <th>Lobby ID</th>
                <th>Status</th>
            </tr>
            {% for game in data.game_history %}
            <tr>
                <td>{{ game.time }}</td>
                <td>{{ game.lobby_id }}</td>
                <td>{{ game.status }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    with data_lock:
        data = {
            "pc1": status_data["pc1"],
            "pc2": status_data["pc2"],
            "last_lobby_id": status_data["last_lobby_id"],
            "game_history": status_data["game_history"]
        }
    return render_template_string(html_template, data=data)

@app.route("/update", methods=["POST"])
def update_status():
    request_data = request.json
    pc_name = request_data.get("pc")
    lobby_id = request_data.get("lobby_id")

    with data_lock:
        status_data[pc_name]["lobby_id"] = lobby_id
        status_data["last_lobby_id"] = lobby_id

        # Обновляем статус аккаунтов
        pc1_lobby = status_data["pc1"]["lobby_id"]
        pc2_lobby = status_data["pc2"]["lobby_id"]

        if pc1_lobby and pc2_lobby:
            if pc1_lobby == pc2_lobby:
                status_data["pc1"]["status"] = "matched"
                status_data["pc2"]["status"] = "matched"
                # Добавляем в историю игр
                status_data["game_history"].append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "lobby_id": pc1_lobby,
                    "status": "success"
                })
            else:
                status_data["pc1"]["status"] = "error"
                status_data["pc2"]["status"] = "error"
        else:
            if pc1_lobby:
                status_data["pc1"]["status"] = "waiting"
            if pc2_lobby:
                status_data["pc2"]["status"] = "waiting"

    return jsonify({"message": "Status updated"})

if __name__ == "__main__":
    print("Запуск сервера...")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
