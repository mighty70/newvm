from flask import Flask, render_template_string, request, jsonify
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

# Данные для отслеживания состояния
status_data = {
    "pc1": {"status": "ожидание", "lobby_id": None, "last_update": None},
    "pc2": {"status": "ожидание", "lobby_id": None, "last_update": None},
    "last_lobby_id": None,
    "game_history": []
}

# Блокировка для потокобезопасности
data_lock = threading.Lock()

# HTML-шаблон
html_template = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Статус Лобби</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f0f2f5;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            font-size: 32px;
            color: #444;
        }
        .status-card {
            display: flex;
            justify-content: space-around;
            margin-bottom: 40px;
        }
        .card {
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            width: 220px;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        .card h2 {
            font-size: 20px;
            color: #555;
            margin-bottom: 10px;
        }
        .card p {
            font-size: 16px;
            margin-bottom: 20px;
        }
        .card .status {
            font-size: 18px;
            font-weight: bold;
        }
        .status-ожидание {
            color: #999;
        }
        .status-совпало {
            color: green;
        }
        .status-ждёт {
            color: orange;
        }
        .status-ошибка {
            color: red;
        }
        .history {
            margin-top: 40px;
            background: #ffffff;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .history h2 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #444;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Статус Лобби</h1>
        <div class="status-card">
            <div class="card">
                <h2>ПК1</h2>
                <p>ID Лобби: <br><strong>{{ data.pc1.lobby_id or '---' }}</strong></p>
                <p class="status status-{{ data.pc1.status }}">{{ data.pc1.status }}</p>
            </div>
            <div class="card">
                <h2>ПК2</h2>
                <p>ID Лобби: <br><strong>{{ data.pc2.lobby_id or '---' }}</strong></p>
                <p class="status status-{{ data.pc2.status }}">{{ data.pc2.status }}</p>
            </div>
        </div>

        <div class="history">
            <h2>История Игр</h2>
            <table>
                <thead>
                    <tr>
                        <th>Дата</th>
                        <th>ID Лобби</th>
                        <th>Статус</th>
                    </tr>
                </thead>
                <tbody>
                    {% for game in data.game_history %}
                    <tr>
                        <td>{{ game.time }}</td>
                        <td>{{ game.lobby_id }}</td>
                        <td>{{ game.status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
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

@app.route("/check_lobby", methods=["POST"])
def check_lobby():
    request_data = request.json
    pc_name = request_data.get("pc")
    lobby_id = request_data.get("lobby_id")

    with data_lock:
        status_data[pc_name]["lobby_id"] = lobby_id
        status_data[pc_name]["last_update"] = datetime.now()
        status_data["last_lobby_id"] = lobby_id

        # Обновляем статус аккаунтов
        pc1_lobby = status_data["pc1"].get("lobby_id")
        pc2_lobby = status_data["pc2"].get("lobby_id")

        if pc1_lobby and pc2_lobby:
            if pc1_lobby == pc2_lobby:
                status_data["pc1"]["status"] = "совпало"
                status_data["pc2"]["status"] = "совпало"
                # Добавляем в историю игр
                status_data["game_history"].append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "lobby_id": pc1_lobby,
                    "status": "успех"
                })
                return jsonify({"action": "accept"})
            else:
                status_data["pc1"]["status"] = "ошибка"
                status_data["pc2"]["status"] = "ошибка"
                return jsonify({"action": "reject"})
        else:
            now = datetime.now()
            if pc1_lobby and status_data["pc2"].get("last_update"):
                elapsed = now - status_data["pc2"].get("last_update")
                if elapsed.total_seconds() > 6:
                    status_data["pc1"]["status"] = "ошибка"
                    status_data["pc2"]["status"] = "ошибка"
                    return jsonify({"action": "reject"})
            if pc2_lobby and status_data["pc1"].get("last_update"):
                elapsed = now - status_data["pc1"].get("last_update")
                if elapsed.total_seconds() > 6:
                    status_data["pc1"]["status"] = "ошибка"
                    status_data["pc2"]["status"] = "ошибка"
                    return jsonify({"action": "reject"})

            if pc1_lobby or pc2_lobby:
                if pc1_lobby:
                    status_data["pc1"]["status"] = "ждёт"
                if pc2_lobby:
                    status_data["pc2"]["status"] = "ждёт"
                return jsonify({"action": "wait"})

    return jsonify({"action": "error"})

if __name__ == "__main__":
    print("Запуск сервера...")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
