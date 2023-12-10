import datetime
import io
import os
import sqlite3 as sl

import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "minimum_wage.db"

@app.route("/")
def home():
    return render_template('home.html', states=db_get_locales())


@app.route("/submit_locale", methods=["POST"])
def submit_locale():
    # session["locale"] = request.form["locale"].capitalize()
    print(request.form['locale'])
    session["locale"] = request.form["locale"]
    if 'locale' not in session or session["locale"] == "":
        return redirect(url_for("home"))
    if "data_request" not in request.form:
        return redirect(url_for("home"))
    session["data_request"] = request.form["data_request"]
    return redirect(url_for("locale_current", data_request=session["data_request"], locale=session["locale"]))


@app.route("/api/coronavirus/<data_request>/<locale>")
def locale_current(data_request, locale):
    return render_template("locale.html", data_request=data_request, locale=locale, project=False)


@app.route("/submit_projection", methods=["POST"])
def submit_projection():
    if 'locale' not in session:
        return redirect(url_for("home"))
    session["date"] = request.form["date"]
    # THESE NEED TO BE BACK IN!
    # if session["locale"] == "" or session["data_request"] == "" or session["date"] == "":
    #     return redirect(url_for("home"))
    return redirect(url_for("locale_projection", data_request=session["data_request"], locale=session["locale"]))


@app.route("/api/coronavirus/<data_request>/projection/<locale>")
def locale_projection(data_request, locale):
    return render_template("locale.html", data_request=data_request, locale=locale, project=True, date=session["date"])


@app.route("/fig/<data_request>/<locale>")
def fig(data_request, locale):
    fig = create_figure(data_request, locale)

    # img = io.BytesIO()
    # fig.savefig(img, format='png')
    # img.seek(0)
    # w = FileWrapper(img)
    # # w = werkzeug.wsgi.wrap_file(img)
    # return Response(w, mimetype="text/plain", direct_passthrough=True)

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


def create_figure(data_request, locale):
    df = db_create_dataframe(data_request, locale)
    print(session)
    if 'date' not in session:
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        fig.suptitle(data_request.capitalize() + " cases in " + locale)
        # fig, ax = plt.subplots(1, 1)
        ax.plot(df["date"], df["cases"])
        ax.set(xlabel="date", ylabel="cases")  # , xticks=range(0, len(df), 31))
        return fig
    else:
        df['datemod'] = df['date'].map(datetime.datetime.toordinal)
        y = df['cases'][-30:].values
        X = df['datemod'][-30:].values.reshape(-1, 1)
        # session['date'] = '11/11/20'  # REMOVE THIS LATER
        dt = [[datetime.datetime.strptime(session['date'], '%m/%d/%y')]]
        print('dt:', dt)
        draw = datetime.datetime.toordinal(dt[0][0])
        dord = datetime.datetime.fromordinal(int(draw))
        regr = LinearRegression(fit_intercept=True, copy_X=True, n_jobs=2)
        regr.fit(X, y)
        pred = int(regr.predict([[draw]])[0])

        # append() is removed in pandas 2.0, replace w/ concat() below

        # df = df.append({'date': dord,
        #                 'cases': pred,
        #                 'datemod': draw}, ignore_index=True)

        # make a new dataframe for prediction
        df_pred = pd.DataFrame({'date': dord,
                                'cases': pred,
                                'datemod': draw}, index=[0])

        # save lengths of dates and cases of original/historical data for diff colors below
        orig_date_len = len(df['date'])
        orig_cases_len = len(df['cases'])

        # concat orig and prediction dataframes
        df = pd.concat([df, df_pred])

        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        fig.suptitle('By ' + session['date'] + ', there will be ' + str(
            pred) + ' ' + data_request.capitalize() + " cases in " + locale)

        # show the original/historical data in blue using slicing
        ax.plot(df["date"][:orig_date_len], df["cases"][:orig_cases_len], color='blue')
        # show the predicted data in orange, notice the - 1 since a line plot needs at least 2 points.
        ax.plot(df['date'][orig_date_len - 1:], df['cases'][orig_cases_len - 1:], color='orange')
        ax.set(xlabel="date", ylabel="cases")  # , xticks=range(0, len(df), 31))
        return fig


def db_create_dataframe(data_request, locale):
    conn = sl.connect(db)
    curs = conn.cursor()

    df = pd.DataFrame()
    table = "time_series_" + data_request
    print(f'{table=}')
    # if locale.lower() == "us":
    #     locale = "US"
    print(f'{locale=}')
    stmt = "SELECT * from " + table + " where `Country/Region`=?"
    data = curs.execute(stmt, (locale,))
    item = curs.fetchone()
    df["date"] = [description[0] for description in curs.description]
    df = df[12:]  # HACK should be 4
    df['date'] = df['date'].str.replace('/', '')
    df['date'] = pd.to_datetime(df['date'], format='%m%d%y')
    df["cases"] = item[12:]  # HACK should be 4
    conn.close()
    return df


def db_get_locales():
    db = "minimum_wage.db"  # Replace with the actual name of your SQLite database
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


# m = "SELECT * FROM time_series_confirmed WHERE `Country/Region`='France'"
# result = conn.execute(m)

@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for("home"))


if __name__ == "__main__":
    # print(db_get_locales())
    app.secret_key = os.urandom(12)
    app.run(debug=True)
