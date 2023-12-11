# Jessica Fan
# ITP 216, Fall 2023, Section 32081
# Final Project
# Description: 
# A web application that allows user to view historical minimum wages across US territories, as well as future predictions

import os
import sqlite3 as sl

import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression
from matplotlib.figure import Figure
from io import BytesIO
import base64
import sqlite3
from flask import request
import numpy as np

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "minimum_wage.db"

# root end point or home 
@app.route("/")
def home():
    return render_template('home.html', wage = db_mean(), states=db_get_locales())

# gives user options of states to choose from as well as different modes of visualization
@app.route("/submit_locale", methods=["POST"])
def submit_locale():
    # session["locale"] = request.form["locale"].capitalize()
    session["state"] = request.form["state"]
    if 'state' not in session or session["state"] == "":
        return redirect(url_for("home"))
    if "data_type" not in request.form:
        return redirect(url_for("home"))
    session["data_type"] = request.form["data_type"]
    print(session["data_type"])
    if(session["data_type"] == "historic"):
        return redirect(url_for("locale_current", data_request=session["data_type"], locale=session["state"]))
    else:
        # provide 50 year prediction view if user selects
        return redirect(url_for("locale_projection", data_request="prediction", locale=session["state"], years=50))

# provides historical view of min. wage for given state
@app.route("/api/minwage/<data_request>/<locale>")
def locale_current(data_request, locale):
    return render_template("locale.html", data_request=data_request, locale=locale, project=False)

# provides prediction view 
@app.route("/submit_projection", methods=["POST"])
def submit_projection():
    years = request.form.get('years', type=int)
    return redirect(url_for("locale_projection", data_request="prediction", locale=session["state"], years=years))

# provides prediction view 
@app.route("/api/minwage/<data_request>/projection/<locale>")
def locale_projection(data_request, locale):
    years = request.args.get('years', type=int)
    print(years)
    return render_template("prediction.html", data_request=data_request, locale=locale, project=True,  years=years)

# helper function to plot minimum wage (historical view)
def plot_minimum_wage(state_data):
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(state_data['Year'], state_data['MinimumWage'], marker='o', linestyle='-', color='b')
    ax.set_xlabel('Year')
    ax.set_ylabel('Minimum Wage')
    ax.set_title(f'Minimum Wage in {state_data["State"].iloc[0]} Over the Years')
    ax.legend()

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png')  
    img_buffer.seek(0) 
    img_str = base64.b64encode(img_buffer.read()).decode('utf-8')

    fig.clf()

    return img_str

# helper function to plot minimum wage (prediction view)
def plot_prediction(state_data, year):
    X = state_data[['Year']]
    y = state_data['MinimumWage']
    reg = LinearRegression().fit(X, y)

    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)

    future_years = range(2020, 2020 + year)  # Adjust the range as needed
    print(year)
    print(future_years)
    future_X = pd.DataFrame({'Year': future_years})
    future_y = reg.predict(future_X)
    future_y = np.round(future_y)

    ax.plot(future_years, future_y, linestyle='--', color='r', label='Linear Regression (Prediction)')

    ax.set_xlabel('Year')
    ax.set_ylabel('Minimum Wage')
    ax.set_title(f'Minimum Wage in {state_data["State"].iloc[0]} Over the future Years')
    ax.legend()

    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png')  
    img_buffer.seek(0)  
    img_str = base64.b64encode(img_buffer.read()).decode('utf-8')

    fig.clf()

    return img_str

@app.route("/fig/<data_request>/<locale>")
def fig(data_request, locale):
    query = f"SELECT * FROM minimum_wage WHERE State = ?"
    state_data = pd.read_sql_query(query, get_db(), params=(locale,))
    
    # Pass state_data directly to create_figure
    img_str = create_figure(state_data)

    img = BytesIO(base64.b64decode(img_str))
    return send_file(img, mimetype="image/png")

# query to extract data for prediction
@app.route("/fig/prediction/<locale>")
def prediction(locale):
    print("in prediction now")
    years = request.args.get('years', type=int)

    query = f"SELECT * FROM minimum_wage WHERE State = ?"
    state_data = pd.read_sql_query(query, get_db(), params=(locale,))
    
    img_str = plot_prediction(state_data, years)  # Call the plot_prediction function

    img = BytesIO(base64.b64decode(img_str))
    return send_file(img, mimetype="image/png")

# plot minimum wage graph
def create_figure(locale):
    print("plotting figure")
    return plot_minimum_wage(locale);

# return a list of states and territories from db
def db_get_locales():
    db = "minimum_wage.db"  
    conn = sl.connect(db)
    curs = conn.cursor()

    table = "minimum_wage"
    stmt = "SELECT DISTINCT State FROM " + table
    curs.execute(stmt)

    # Fetch all results and extract the first element of each tuple
    data = curs.fetchall()
    locales = sorted({result[0] for result in data})

    conn.close()
    return locales

# connecting to database
def get_db():
    conn = sqlite3.connect("minimum_wage.db")
    return conn

# calculating mean using numpy
def db_mean():
    db = "minimum_wage.db"  
    conn = sl.connect(db)
    curs = conn.cursor()

     # Fetching column information
    curs.execute(f"PRAGMA table_info(minimum_wage)")
    columns = curs.fetchall()

    # Extracting and printing column names
    column_names = [col[1] for col in columns]  # Column name is at index 1
    print("Column names:", column_names)

    stmt = "SELECT MinimumWage FROM minimum_wage WHERE Year=2020"
    curs.execute(stmt)

    wages = curs.fetchall()

    # Extract the wage values from the query result
    wage_values = [wage[0] for wage in wages if wage[0] is not None]

    # Calculate the mean using NumPy
    mean_wage = np.mean(wage_values) if wage_values else None
    mean_wage = mean_wage.round(3)
    print (mean_wage)

    conn.close()

    return mean_wage

@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
