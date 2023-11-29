from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'pdf', 'xlsx', 'xls'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def compress_image(image_path):
    img = Image.open(image_path)
    img.save(image_path, quality=85) 

@app.route('/')
def index():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
    return render_template('index.html', folders=folders)

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

    return redirect(url_for('index'))


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

    return redirect(url_for('index'))

@app.route('/view/<folder_name>/<image_name>')
def view_image(folder_name, image_name):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    return send_from_directory(folder_path, image_name)

if __name__ == '__main__':
    app.run(debug=True)