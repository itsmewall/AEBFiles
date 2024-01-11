import random
import sqlite3
from flask import Flask, make_response, redirect, render_template, request, send_from_directory, session, url_for, jsonify
from datetime import datetime, timedelta
import os
from flask_cors import CORS
from os import path
from werkzeug.utils import secure_filename
from PIL import Image
from urllib.parse import unquote
import traceback
from ldap3 import Connection, Server
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  
app.secret_key = 'AEB'

DATABASE_NAME = 'docs_info.db' 
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_images_from_folder(folder):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    images = [img for img in os.listdir(folder_path) if img.lower().endswith(('png', 'jpg', 'jpeg', 'gif'))]
    return images

def get_first_image_from_random_folder():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]

    if not folders:
        return None

    random_folder = random.choice(folders)
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], random_folder)
    images = [img for img in os.listdir(folder_path) if img.lower().endswith(('png', 'jpg', 'jpeg', 'gif'))]

    if images:
        first_image = images[0]
        return {'folder': random_folder, 'image': first_image}
    else:
        return None

def get_all_doc_info():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Obtém todas as informações da tabela docs_info
    cursor.execute('SELECT * FROM docs_info')
    doc_info = cursor.fetchall()

    # Fecha a conexão
    conn.close()

    # Converte as informações para um dicionário
    doc_info_dict = {row[1]: {'description': row[2], 'author': row[3], 'date_uploaded': row[4]} for row in doc_info}

    return doc_info_dict

# Função para criar e popular o banco de dados
def create_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Crie suas tabelas aqui
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS docs_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name TEXT NOT NULL,
            description TEXT,
            author TEXT,
            date_uploaded TEXT
        );
    ''')

    # Commit e fechar a conexão
    conn.commit()
    conn.close()
create_database()


def populate_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Insira dados na tabela
    cursor.execute("INSERT INTO docs_info (doc_name, description, author, date_uploaded) VALUES (?, ?, ?, ?)",
                   ('Nome do Documento', 'Descrição do Documento', 'Autor do Documento', '2024-01-02'))

    # Commit e fechar a conexão
    conn.commit()
    conn.close()

# Chame a função para criar o banco de dados
create_database()

# Chame a função para popular o banco de dados
populate_database()

def get_all_images():
    all_images = {}
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]

    for folder in folders:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        images = [img for img in os.listdir(folder_path) if img.lower().endswith(('png', 'jpg', 'jpeg', 'gif'))]
        decoded_images = [unquote(img) for img in images]
        all_images[folder] = {'full_paths': [os.path.join(folder_path, img) for img in decoded_images], 'info': {}}

    return all_images


@app.route('/uploads/carousel/<filename>')
def serve_carousel_images(filename):
    return send_from_directory('/uploads/carousel', filename)

@app.route('/')
def publicIndex():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]

    # Obtém todas as informações do banco de dados
    doc_info_dict = get_all_doc_info()

    # Adiciona as informações ao contexto do template
    app.jinja_env.globals.update(doc_info_dict=doc_info_dict)

    # Get all images for each folder
    folder_images = get_all_images()

    # Adiciona as informações das imagens ao contexto do template
    app.jinja_env.globals.update(folder_images=folder_images)

    carousel_images_with_index = [(index, image.replace("\\", "/")) for index, image in enumerate(folder_images['carousel']['full_paths'])]

    return render_template('publicIndex.html', folders=folders, carousel_images_with_index=carousel_images_with_index)

def obter_username_ldap(username, password):
    server = Server('ldap://192.168.0.83:389')
    base_dn = 'OU=USUARIOS,OU=AEB,DC=aeb,DC=gov,DC=br'
    user_dn = f'AEB\\{username}'
    ldap_connection = Connection(server, user=user_dn, password=password)

    if ldap_connection.bind():
        search_filter = f'(sAMAccountName={username})'
        logging.debug(f"Searching LDAP with filter: {search_filter}")
        
        ldap_connection.search(base_dn, search_filter, attributes=['displayName'])
        
        if ldap_connection.entries:
            user_entry = ldap_connection.entries[0]
            display_name = user_entry.displayName.value
            logging.debug(f"Display Name found: {display_name}")
            return display_name
        else:
            logging.debug("No entries found in LDAP search.")
    else:
        logging.debug("LDAP bind failed.")

    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    success_message = None
    if 'username' in session:
        return redirect(url_for('adminIndex'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error_message = 'Por favor, insira o usuário e a senha.'
            return render_template('login.html', error_message=error_message)
        ldap_username = obter_username_ldap(username, password)
        if ldap_username:
            session['username'] = username
            session['ldap_username'] = ldap_username
            session['expiry'] = datetime.now() + timedelta(minutes=30)
            # Define o cookie
            response = make_response(redirect(url_for('adminIndex')))
            response.set_cookie('username', username, expires=session['expiry'])
            return response
        else:
            error_message = 'Usuário ou senha inválidos. Tente novamente.'
            return render_template('login.html', error_message=error_message)
    return render_template('login.html', login_message=success_message, error_message=error_message)

@app.before_request
def verificar_autenticacao():
    rotas_autenticacao = ['/login']
    if ('username' not in session or request.cookies.get('username') != session['username']) and request.path in rotas_autenticacao:
        return None 

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
def adminIndex():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
    ldap_username = session.get('ldap_username')
    return render_template('adminIndex.html', folders=folders, ldap_username=ldap_username)

@app.route('/sobre')
def about():    
    return render_template('about.html')

@app.route('/contatos')
def contact():
    return render_template('contact.html')

@app.route('/documents')
def documents():
    return render_template('documents.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/folder/<folder_name>')
def show_folder(folder_name):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    images = os.listdir(folder_path)
    return render_template('folder.html', folder_name=folder_name, images=images)

@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form['folder_name']
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    return redirect(url_for('adminIndex'))


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        folder = request.form['folder']
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        filename = secure_filename(file.filename)
        file_path = os.path.join(folder_path, filename)

        # Salvar o arquivo
        file.save(file_path)

        
    return redirect(url_for('adminIndex'))

@app.route('/view/<folder_name>/<image_name>')
def view_image(folder_name, image_name):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    image_path = os.path.join(folder_path, image_name)

    # Verifica se o arquivo existe antes de enviá-lo
    if os.path.exists(image_path):
        return send_from_directory(folder_path, image_name)
    else:
        return "Imagem não encontrada", 404


if __name__ == '__main__':
    app.run(debug=True)
