from typing import List, Dict
import simplejson as json
from flask import Flask, request, Response
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
from flask import render_template, g, redirect, url_for
from flask_oidc import OpenIDConnect
from okta import UsersClient

app = Flask(__name__)
mysql = MySQL(cursorclass=DictCursor)

app.config['MYSQL_DATABASE_HOST'] = 'db'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_DB'] = 'pitchersData'
mysql.init_app(app)

app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = False
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc/callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "profile"]
app.config["SECRET_KEY"] = "{{ LONG_RANDOM_STRING }}"
app.config["OIDC_ID_TOKEN_COOKIE_NAME"] = "oidc_token"
oidc = OpenIDConnect(app)
okta_client = UsersClient("{{ https://dev-5564495.okta.com }}", "{{ 00sfBb7ZCadBOk_nIECHjS0o2okOi86Sq7EDcVuISi }}")


@app.before_request
def before_request():
    if oidc.user_loggedin:
        g.user = okta_client.get_user(oidc.user_getfield("sub"))
    else:
        g.user = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
@oidc.require_login
def dashboard():
    return render_template("dashboard.html")


@app.route("/login")
@oidc.require_login
def login():
    return redirect(url_for(".dashboard"))


@app.route("/logout")
def logout():
    oidc.logout()
    return redirect(url_for(".index"))

@app.route("/")
def login():
    user = {'username': 'Corey & Roberto'}
    return render_template('signup.html', user=user)

@app.route("/dashboard")
def dashboard():
    user = {'username': 'Corey & Roberto'}
    return render_template('dashboard.html', user=user)

@app.route('/home/')
def home():
    user = {'username': 'Corey & Roberto'}
    return render_template('home.html', user=user)


@app.route('/calendar/')
def calendar():
    user = {'username': 'Corey & Roberto'}
    return render_template('calendar.html', user=user)

@app.route('/index/', methods=['GET'])
def index():
    user = {'username': 'Corey & Roberto'}
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblPitchersImport')
    result = cursor.fetchall()
    return render_template('index.html', user=user, pitchers=result)


@app.route('/index/view/<int:pitcher_id>', methods=['GET'])
def record_view(pitcher_id):
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblPitchersImport WHERE id=%s', pitcher_id)
    result = cursor.fetchall()
    return render_template('view.html', title='View Form', pitcher=result[0])


@app.route('/edit/<int:pitcher_id>', methods=['GET'])
def form_edit_get(pitcher_id):
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblPitchersImport WHERE id=%s', pitcher_id)
    result = cursor.fetchall()
    return render_template('edit.html', title='Edit Form', pitcher=result[0])


@app.route('/edit/<int:pitcher_id>', methods=['POST'])
def form_update_post(pitcher_id):
    cursor = mysql.get_db().cursor()
    inputData = (request.form.get('Name'), request.form.get('Team'), request.form.get('Position'),
                 request.form.get('Height_in'), request.form.get('Weight_lb'), request.form.get('Age'), pitcher_id)
    sql_update_query = """UPDATE tblPitchersImport t SET t.Name = %s, t.Team = %s, t.Position = %s, t.Height_in = 
    %s, t.Weight_lb = %s, t.Age = %s WHERE t.id = %s """
    cursor.execute(sql_update_query, inputData)
    mysql.get_db().commit()
    return redirect("/", code=302)

@app.route('/pitchers/new', methods=['GET'])
def form_insert_get():
    return render_template('new.html', title='New Pitcher Form')


@app.route('/pitchers/new', methods=['POST'])
def form_insert_post():
    cursor = mysql.get_db().cursor()
    inputData = (request.form.get('Name'), request.form.get('Team'), request.form.get('Position'),
                 request.form.get('Height_in'), request.form.get('Weight_lb'),
                 request.form.get('Age'))
    sql_insert_query = """INSERT INTO tblPitchersImport (Name,Team,Position,Height_in,Weight_lb,Age) VALUES (%s, %s,%s, %s,%s, %s) """
    cursor.execute(sql_insert_query, inputData)
    mysql.get_db().commit()
    return redirect("/", code=302)

@app.route('/delete/<int:pitcher_id>', methods=['POST'])
def form_delete_post(pitcher_id):
    cursor = mysql.get_db().cursor()
    sql_delete_query = """DELETE FROM tblPitchersImport WHERE id = %s """
    cursor.execute(sql_delete_query, pitcher_id)
    mysql.get_db().commit()
    return redirect("/", code=302)


@app.route('/index/api/v1/pitchers', methods=['GET'])
def api_browse() -> str:
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblPitchersImport')
    result = cursor.fetchall()
    json_result = json.dumps(result);
    resp = Response(json_result, status=200, mimetype='application/json')
    return resp


@app.route('/index/api/v1/pitchers/<int:pitcher_id>', methods=['GET'])
def api_retrieve(pitcher_id) -> str:
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblPitchersImport WHERE id=%s', pitcher_id)
    result = cursor.fetchall()
    json_result = json.dumps(result);
    resp = Response(json_result, status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/pitchers/<int:pitcher_id>', methods=['PUT'])
def api_edit(pitcher_id) -> str:
    cursor = mysql.get_db().cursor()
    content = request.json
    inputData = (content['Name'], content['Team'], content['Position'], content['Height_in'], content['Weight_lb'], content['Age'],pitcher_id)
    sql_update_query = """UPDATE tblPitchersImport t SET t.Name = %s, t.Team = %s, t.Position = %s, t.Height_in = 
        %s, t.Weight_lb = %s, t.Age = %s WHERE t.id = %s """
    cursor.execute(sql_update_query, inputData)
    mysql.get_db().commit()
    resp = Response(status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/pitchers', methods=['POST'])
def api_add() -> str:

    content = request.json

    cursor = mysql.get_db().cursor()
    inputData = (content['Name'], content['Team'], content['Position'],
                 content['Height_in'], content['Weight_lb'],
                 content('Age'))
    sql_insert_query = """INSERT INTO tblPitchersImport (Name,Team,Position,Height_in,Weight_lb,Age) VALUES (%s, %s,%s, %s,%s, %s) """
    cursor.execute(sql_insert_query, inputData)
    mysql.get_db().commit()
    resp = Response(status=201, mimetype='application/json')
    return resp


@app.route('/api/v1/pitchers/<int:pitcher_id>', methods=['DELETE'])
def api_delete(pitcher_id) -> str:
    cursor = mysql.get_db().cursor()
    sql_delete_query = """DELETE FROM tblPitchersImport WHERE id = %s """
    cursor.execute(sql_delete_query, pitcher_id)
    mysql.get_db().commit()
    resp = Response(status=200, mimetype='application/json')
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)