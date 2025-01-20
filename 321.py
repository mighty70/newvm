from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Хранение данных о лобби ID и статусе
lobby_data = {
    "pc1": {"lobby_id": None, "timestamp": None},
    "pc2": {"lobby_id": None, "timestamp": None}
}

# История игр
game_history = []

def clear_old_lobby_ids():
    current_time = datetime.now()
    for pc in lobby_data:
        if lobby_data[pc]["timestamp"]:
            time_diff = (current_time - lobby_data[pc]["timestamp"]).total_seconds()
            if time_diff > 300:  # 5 минут
                lobby_data[pc]["lobby_id"] = None
                lobby_data[pc]["timestamp"] = None

@app.route("/")
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dota Lobby Status</title>
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .status-box {
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 10px;
            color: white;
        }
        .status-box.green {
            background-color: #28a745;
        }
        .status-box.orange {
            background-color: #ffc107;
        }
        .status-box.red {
            background-color: #dc3545;
        }
        .history-table {
            margin-top: 20px;
        }
        .history-table th {
            background-color: #343a40;
            color: white;
        }
        .history-table tr:hover {
            background-color: #f1f1f1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center my-4">Dota Lobby Status</h1>
        <div class="row">
            <div class="col-md-6">
                <div class="status-box {% if lobby_data['pc1']['lobby_id'] and lobby_data['pc2']['lobby_id'] and lobby_data['pc1']['lobby_id'] == lobby_data['pc2']['lobby_id'] %}green{% elif lobby_data['pc1']['lobby_id'] or lobby_data['pc2']['lobby_id'] %}orange{% else %}red{% endif %}">
                    <h2>PC1</h2>
                    <p>Последний ID лобби: {{ lobby_data['pc1']['lobby_id'] or 'Нет данных' }}</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="status-box {% if lobby_data['pc1']['lobby_id'] and lobby_data['pc2']['lobby_id'] and lobby_data['pc1']['lobby_id'] == lobby_data['pc2']['lobby_id'] %}green{% elif lobby_data['pc1']['lobby_id'] or lobby_data['pc2']['lobby_id'] %}orange{% else %}red{% endif %}">
                    <h2>PC2</h2>
                    <p>Последний ID лобби: {{ lobby_data['pc2']['lobby_id'] or 'Нет данных' }}</p>
                </div>
            </div>
        </div>

        <h2 class="text-center my-4">История игр</h2>
        <table class="table table-bordered history-table">
            <thead>
                <tr>
                    <th>Время</th>
                    <th>PC1 Lobby ID</th>
                    <th>PC2 Lobby ID</th>
                    <th>Статус</th>
                </tr>
            </thead>
            <tbody>
                {% for game in game_history %}
                <tr>
                    <td>{{ game['time'] }}</td>
                    <td>{{ game['pc1_lobby_id'] }}</td>
                    <td>{{ game['pc2_lobby_id'] }}</td>
                    <td>
                        {% if game['status'] == 'accept' %}
                            <span class="badge badge-success">Совпадение</span>
                        {% else %}
                            <span class="badge badge-danger">Не совпадение</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
    ''', lobby_data=lobby_data, game_history=game_history)

@app.route("/send_lobby_id", methods=["POST"])
def send_lobby_id():
    data = request.json
    pc_name = data.get("pc")
    lobby_id = data.get("lobby_id")

    logging.debug(f"Received data: pc={pc_name}, lobby_id={lobby_id}")

    if not pc_name or not lobby_id:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    # Сохраняем лобби ID и время получения
    lobby_data[pc_name]["lobby_id"] = lobby_id
    lobby_data[pc_name]["timestamp"] = datetime.now()

    logging.debug(f"Updated lobby_data: {lobby_data}")

    # Проверяем статус игры
    status = check_game_status()
    logging.debug(f"Game status: {status}")

    return jsonify({"status": "success"}), 200

@app.route("/check_status", methods=["GET"])
def check_status():
    pc_name = request.args.get("pc")
    if not pc_name:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    # Возвращаем текущий статус игры
    status = get_game_status()
    return jsonify({"status": status}), 200

def check_game_status():
    clear_old_lobby_ids()
    pc1_data = lobby_data["pc1"]
    pc2_data = lobby_data["pc2"]

    if pc1_data["lobby_id"] and pc2_data["lobby_id"]:
        if pc1_data["lobby_id"] == pc2_data["lobby_id"]:
            status = "accept"
        else:
            status = "reject"
    else:
        status = "wait"

    # Добавляем запись в историю игр
    game_history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pc1_lobby_id": pc1_data["lobby_id"],
        "pc2_lobby_id": pc2_data["lobby_id"],
        "status": status
    })

    return status

def get_game_status():
    pc1_data = lobby_data["pc1"]
    pc2_data = lobby_data["pc2"]

    if pc1_data["lobby_id"] and pc2_data["lobby_id"]:
        if pc1_data["lobby_id"] == pc2_data["lobby_id"]:
            return "accept"
        else:
            return "reject"
    elif pc1_data["lobby_id"] or pc2_data["lobby_id"]:
        return "wait"
    else:
        return "idle"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
