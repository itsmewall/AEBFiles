import random
import sqlite3
from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
import os
from os import path
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)

DATABASE_NAME = 'docs_info.db' 
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'xlsx', 'xls'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def compress_image(image_path):
    img = Image.open(image_path)
    new_width = 800  # Ajuste conforme necessário
    new_height = 600  # Ajuste conforme necessário
    # Redimensiona a imagem
    img = img.resize((new_width, new_height), Image.ANTIALIAS)
    img.save(image_path)

def get_all_images():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]

    all_images = {}
    for folder in folders:
        images = get_images_from_folder(folder)
        all_images[folder] = {'images': images, 'info': {}}

    # Adicionando a obtenção de imagens para a pasta 'carousel'
    carousel = 'carousel'
    carousel_images = ['caminho_para_sua_imagem.jpg']  # Substitua pelo caminho real da imagem fixa

    # Obtém caminhos completos das imagens no carrossel
    carousel_images_full_paths = [url_for('view_image', folder_name=carousel, image_name=image) for image in carousel_images]

    all_images[carousel] = {'images': carousel_images, 'info': {}, 'full_paths': carousel_images_full_paths}

    return all_images



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


@app.route('/get_image_info', methods=['GET'])
def get_image_info():
    image_name = request.args.get('image_name')

    # Conecta ao banco de dados
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Substitua isso pela lógica real para obter informações da imagem do seu sistema
    image_info = {
        'description': 'Descrição da imagem',
        'author': 'Autor da imagem',
        'date_uploaded': 'Data de upload',
    }

    # Obtém informações da imagem
    cursor.execute('SELECT * FROM docs_info WHERE doc_name = ?', (image_name,))
    doc_info = cursor.fetchone()

    # Fecha a conexão
    conn.close()

    if doc_info:
        # Retorna as informações em formato JSON
        return jsonify({
            'description': doc_info[2],
            'author': doc_info[3],
            'date_uploaded': doc_info[4]
        })
    else:
        # Retorna um objeto vazio se não houver informações
        return jsonify({})



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

@app.route('/')
def publicIndex():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]

    # Obtém todas as informações do banco de dados
    doc_info_dict = get_all_doc_info()

    # Adiciona as informações ao contexto do template
    app.jinja_env.globals.update(doc_info_dict=doc_info_dict)

    # Get all images for each folder
    folder_images = get_all_images()

    # Conecta ao banco de dados
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Itera sobre os resultados do banco de dados e adiciona informações ao dicionário folder_images
    for folder, images in folder_images.items():
        for image in images:
            cursor.execute('SELECT * FROM docs_info WHERE doc_name = ?', (image,))
            image_info = cursor.fetchone()

            if image_info:
                image_details = {
                    'description': image_info[2],
                    'author': image_info[3],
                    'date_uploaded': image_info[4]
                }
                # Atualiza o dicionário folder_images
                folder_images[folder]['info'][image] = image_details

    # Fecha a conexão
    conn.close()

    return render_template('publicIndex.html', folders=folders, folder_images=folder_images)


@app.route('/admin')
def adminIndex():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
    return render_template('adminIndex.html', folders=folders)

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

        # Comprimir a imagem (se for uma imagem)
        if file.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
            compress_image(file_path)

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
