import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Define the static folder path
app.config['STATIC_FOLDER'] = os.path.join(app.root_path, 'static')

# Define the uploads folder path
app.config['UPLOAD_FOLDER'] = os.path.join(app.config['STATIC_FOLDER'], 'uploads')

# Ensure the uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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

@app.route('/analyze/<filename>')
def analyze(filename):
    # Path to the uploaded CSV file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f'file path: {filepath}')
    
    # Read and clean the CSV
    df = pd.read_csv(filepath, skiprows=20, names=["date", "time", "kwh"])
    print(df.head())
    
    # Convert date and time columns
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
    df['time'] = pd.to_datetime(df['time'], format='%H:%M').dt.time

    # Add day of the week
    df['day_of_week'] = df['date'].dt.day_name()

    # Add daytime and nighttime columns
    df['daytime'] = ((df['time'] >= pd.to_datetime('07:00').time()) & (df['time'] <= pd.to_datetime('17:00').time())).astype(int)
    df['nighttime'] = ((df['time'] >= pd.to_datetime('23:00').time()) | (df['time'] <= pd.to_datetime('07:00').time())).astype(int)

    # Add regular price and reduced prices
    price_per_kwh = 0.5252
    df['Regular price'] = df['kwh'] * price_per_kwh
    df['15% Daytime'] = df.apply(lambda x: x['kwh'] * 0.85 * price_per_kwh if x['daytime'] == 1 else x['kwh'] * price_per_kwh, axis=1)
    df['20% Nighttime'] = df.apply(lambda x: x['kwh'] * 0.80 * price_per_kwh if x['nighttime'] == 1 else x['kwh'] * price_per_kwh, axis=1)
    df['7% All Day'] = df['Regular price'] * 0.93

    # Ensure the 'month' column is properly formatted
    df['month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')  # Format as YYYY-MM

    # Ensure the price columns are numeric
    price_columns = ['Regular price', '15% Daytime', '20% Nighttime', '7% All Day']
    for column in price_columns:
        df[column] = pd.to_numeric(df[column], errors='coerce')

    print(df.head())

    # Group data by month and sum the prices
    df_grouped = df.groupby('month').agg({
        'Regular price': 'sum',
        '15% Daytime': 'sum',
        '20% Nighttime': 'sum',
        '7% All Day': 'sum'
    })

    print(df_grouped.head))

    # Tight layout for better spacing
    plt.tight_layout()

    # Plot the grouped data
    ax = df_grouped.plot(kind='bar', figsize=(10, 6))
    plt.title('Monthly Price Comparison')
    plt.ylabel('Price (NIS)')
    plt.xlabel('Month')
    plt.xticks(rotation=45)
    plt.legend(title='Price Type')

    # Save the plot as an image to display on the webpage
    chart_path = os.path.join(app.config['UPLOAD_FOLDER'], 'chart.png')
    plt.savefig(chart_path)
    plt.close()
    
    # Save the chart as an image
    chart_path = os.path.join(app.config['STATIC_FOLDER'], 'uploads', 'chart.png')
    plt.savefig(chart_path)

    # Add log or return message with file path
    print(f'Chart saved at: {chart_path}')

    return render_template('result.html', chart_url=url_for('static', filename='uploads/chart.png'))

if __name__ == "__main__":
    app.run(debug=True)