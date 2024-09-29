from flask import Flask, request, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os
import io
import base64

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            df = pd.read_csv(file)
            # Your processing logic goes here...
            df['Regular price'] = df['kwh'] * 0.5252
            df['7% All Day'] = df['Regular price'] * 0.93
            df['15% Daytime'] = df['Regular price'] * 0.85
            df['20% Nighttime'] = df['Regular price'] * 0.80
            
            # Group by month and sum the prices for each category
            df['month'] = pd.to_datetime(df['date'], format='%d/%m/%Y').dt.month
            monthly_data = df.groupby('month').sum(numeric_only=True)

            # Create a bar chart
            monthly_data.plot(kind='bar', figsize=(10, 5))
            plt.title('Monthly Prices')
            plt.xlabel('Month')
            plt.ylabel('Price')
            
            # Save the chart to a BytesIO object
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            plt.close()  # Close the plot to free up memory
            return render_template('index.html', plot_url=plot_url)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
