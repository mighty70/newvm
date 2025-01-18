from flask import Flask, render_template_string, request, jsonify
import threading
from datetime import datetime

app = Flask(__name__)

# Данные для отслеживания состояния
status_data = {
    "pc1": {"status": "ожидание", "lobby_id": None},
    "pc2": {"status": "ожидание", "lobby_id": None},
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
        .status-ожидание {
            color: #999;
        }
        .status-совпало {
            color: green;
            font-weight: bold;
        }
        .status-ждёт {
            color: orange;
            font-weight: bold;
        }
        .status-ошибка {
            color: red;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Статус Лобби</h1>
        <h2>Текущее Лобби</h2>
        <p>Последний ID Лобби: <strong>{{ data.last_lobby_id }}</strong></p>
        <h2>Статус ПК</h2>
        <table>
            <tr>
                <th>ПК</th>
                <th>Статус</th>
                <th>ID Лобби</th>
            </tr>
            <tr>
                <td>ПК1</td>
                <td class="status-{{ data.pc1.status }}">{{ data.pc1.status }}</td>
                <td>{{ data.pc1.lobby_id }}</td>
            </tr>
            <tr>
                <td>ПК2</td>
                <td class="status-{{ data.pc2.status }}">{{ data.pc2.status }}</td>
                <td>{{ data.pc2.lobby_id }}</td>
            </tr>
        </table>
        <h2>История Игр</h2>
        <table>
            <tr>
                <th>Дата</th>
                <th>ID Лобби</th>
                <th>Статус</th>
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

@app.route("/check_lobby", methods=["POST"])
def check_lobby():
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
