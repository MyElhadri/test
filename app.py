from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import matplotlib.pyplot as plt
import io, base64, os
from matplotlib import cm
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create the upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'datafile' not in request.files:
        flash('No file part in the request.')
        return redirect(url_for('index'))

    file = request.files['datafile']
    if file.filename == '':
        flash('No file selected.')
        return redirect(url_for('index'))

    try:
        # Load the CSV file into a Pandas DataFrame
        df = pd.read_csv(file)
    except Exception as e:
        flash("Error reading file: " + str(e))
        return redirect(url_for('index'))

    # Attempt to set an index. For Corona data, we likely have no date.
    # If there's a date column, process it; otherwise, use the "ID" column.
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break
    if date_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df.sort_values(by=date_col, inplace=True)
            df.set_index(date_col, inplace=True)
        except Exception as e:
            flash("Error processing date column: " + str(e))
    elif 'ID' in df.columns:
        df.set_index('ID', inplace=True)

    # Fill missing values for both numeric and categorical data.
    df.fillna(method='ffill', inplace=True)

    # Generate HTML tables for data preview and descriptive statistics.
    details = df.head().to_html(classes="table table-striped")
    stats = df.describe(include="all").to_html(classes="table table-bordered")

    # Use the Temperature column for visualization if available; else fallback.
    if "Temperature" in df.columns:
        data_series = df["Temperature"]
        col_label = "Temperature"
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            col_label = numeric_cols[0]
            data_series = df[col_label]
        else:
            flash("No numeric column available for visualization.")
            return render_template('result.html', details=details, stats=stats,
                                   plot_wave_url=None, plot_bar_url=None)

    ## 1. Create an Abstract Wave-Like Line Graph
    # Generate an abstract x-axis and modulate the data with a sine wave.
    x = np.linspace(0, 2 * np.pi, len(data_series))
    amplitude = data_series.std() / 2 if data_series.std() != 0 else 1
    # Here, we add a sine modulation (frequency = 3) to the original data.
    wave_transformation = data_series + amplitude * np.sin(x * 3)

    plt.figure(figsize=(12, 6))
    plt.plot(x, wave_transformation, lw=2, color='magenta', linestyle='--', marker='o')
    plt.fill_between(x, wave_transformation, color='orchid', alpha=0.3)
    plt.xlabel('Abstract Index')
    plt.ylabel(f'{col_label} (Transformed)')
    plt.title(f'Abstract Wave-Like Pattern of {col_label} Data')
    plt.tight_layout()

    buf_wave = io.BytesIO()
    plt.savefig(buf_wave, format='png')
    buf_wave.seek(0)
    plot_wave_url = "data:image/png;base64," + base64.b64encode(buf_wave.getvalue()).decode('utf-8')
    plt.close()

    ## 2. Create a Creative Dynamic Bar Chart
    # Normalize the data for dynamic coloring.
    norm_data = (data_series - data_series.min()) / (data_series.max() - data_series.min())
    colors = cm.plasma(norm_data)  # using the 'plasma' colormap for a vibrant effect

    plt.figure(figsize=(12, 6))
    # Using range(len(data_series)) as x-axis labels to avoid clutter
    plt.bar(range(len(data_series)), data_series, color=colors)
    plt.xlabel('Record Index')
    plt.ylabel(col_label)
    plt.title(f'Creative Dynamic Bar Chart of {col_label} Data')
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf_bar = io.BytesIO()
    plt.savefig(buf_bar, format='png')
    buf_bar.seek(0)
    plot_bar_url = "data:image/png;base64," + base64.b64encode(buf_bar.getvalue()).decode('utf-8')
    plt.close()

    return render_template('result.html', details=details, stats=stats,
                           plot_wave_url=plot_wave_url, plot_bar_url=plot_bar_url)


if __name__ == '__main__':
    app.run(debug=True)
