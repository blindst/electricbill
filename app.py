import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Define the folder to save uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed extensions for the upload
ALLOWED_EXTENSIONS = {'csv'}

# Function to check allowed file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the POST request has the file part
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    # If user does not select file, browser may also submit an empty part without filename
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Call the processing function
        return redirect(url_for('analyze', filename=filename))

    return redirect(request.url)

@app.route('/analyze/<filename>', methods=['GET'])
def analyze(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)

    # Generate the chart
    chart_path = os.path.join(app.root_path, 'static', 'uploads', 'chart.png')
    print(f"Chart path: {chart_path}")  # Debug: Prints the chart path to logs

    df['Total Price (NIS)'] = df['kWh'] * 0.5252
    df.groupby('Month')['Total Price (NIS)'].sum().plot(kind='bar')

    # Save the plot as an image in static/uploads/
    plt.savefig(chart_path)
    plt.close()

    return render_template('result.html', chart_url=url_for('static', filename='uploads/chart.png'))


if __name__ == "__main__":
    app.run(debug=True)
