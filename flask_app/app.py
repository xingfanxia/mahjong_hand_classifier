from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import os

app = Flask(__name__)

# Directory for uploads and output. You may need to create them if they don't exist.
UPLOAD_FOLDER = 'static/uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create upload folder if it doesn't exist

# Load YOLOv8 model, make sure to place 'yolov8n.pt' in the working directory or specify the path
model = YOLO('best.pt')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_image():
    # handle image upload
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

            # Run batched inference on the uploaded image
            results = model(image_path)
            results.render() # Render detections into results.imgs
            result_filename = 'result_' + filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
            results.save(save_path=save_path)  # Save rendered results.imgs to file

            return redirect(url_for('show_result', filename=result_filename))

    # render upload page
    return render_template('upload.html')

@app.route('/show_result/<filename>')
def show_result(filename):
    # Redirect to a page that shows the uploaded image with detections
    return render_template('result.html', filename=filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5005')