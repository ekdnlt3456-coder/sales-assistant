from flask import Flask, render_template, request, jsonify
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

def get_db():
    return psycopg2.connect(os.environ.get('DATABASE_URL'), cursor_factory=RealDictCursor)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            status TEXT DEFAULT 'active',
            amount TEXT,
            picks TEXT,
            memo TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM clients ORDER BY created_at DESC')
        clients = [dict(r) for r in cur.fetchall()]
        for c in clients:
            if c.get('created_at'):
                c['created_at'] = c['created_at'].strftime('%Y.%m.%d')
        cur.close()
        conn.close()
        return jsonify(clients)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients', methods=['POST'])
def add_client():
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO clients (name, phone, status, amount, picks, memo) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *',
            (data.get('name'), data.get('phone'), data.get('status','active'),
             data.get('amount'), data.get('picks'), data.get('memo'))
        )
        client = dict(cur.fetchone())
        if client.get('created_at'):
            client['created_at'] = client['created_at'].strftime('%Y.%m.%d')
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(client)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('DELETE FROM clients WHERE id = %s', (client_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'UPDATE clients SET name=%s, phone=%s, status=%s, amount=%s, picks=%s, memo=%s WHERE id=%s RETURNING *',
            (data.get('name'), data.get('phone'), data.get('status'),
             data.get('amount'), data.get('picks'), data.get('memo'), client_id)
        )
        client = dict(cur.fetchone())
        if client.get('created_at'):
            client['created_at'] = client['created_at'].strftime('%Y.%m.%d')
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(client)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai', methods=['POST'])
def ai_proxy():
    try:
        import anthropic
        data = request.json
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1000,
            messages=data.get('messages', [])
        )
        return jsonify({'content': message.content[0].text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
