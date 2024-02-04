from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mysqldb import MySQL
from flask_assets import Environment, Bundle
import json, os
import pandas as pd
import jinja2
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime

env = jinja2.Environment()
env.globals.update(zip=zip)

app = Flask(__name__)
assets = Environment(app)

# js = Bundle('chart.js', output='static/assets/js/main.js')
# css = Bundle('chart.css', output='static/assets/css/main.css')
# assets.register('js_all', js)
# assets.register('css_all', css)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "lomba"
app.secret_key='asdsdfsdfs13sdf_df%&'


mysql = MySQL(app)
@app.route("/")
def index():
    login = False
    username = ""
    if "username" in session:
        login = True
        username = session["username"]
    
    return render_template("index.html", login=login, username=username)

@app.route("/about")
def about():
    login = False
    username = ""
    if "username" in session:
        login = True
        username = session["username"]
    
    return render_template("about.html", login=login, username=username)
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM login")
        curfet = cur.fetchall()
        cur.close()
        user = [i[0] for i in curfet]
        pw = [i[3] for i in curfet]
        
        if username in user and password in pw:
            nama = [i[2] for i in curfet]
            name = nama[user.index(username)-1]
            session["username"] = username
            session["password"] = password
            session["nama"] = nama
            
            return redirect(url_for("index"))
        else:
            flash("Username atau password salah!")
            return render_template("login.html")

    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            nama_lengkap = request.form.get("nama_lengkap")
            email = request.form.get("email")
        
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO login(username, email, nama_lengkap, password) values (%s, %s, %s, %s)", (username, email, nama_lengkap, password))
            cur2 = cur.fetchall()
            mysql.connection.commit()
            cur.close()
            flash("Berhasil terdaftar")
            return redirect(url_for("login"))
        except:
            flash("Username telah terdaftar")
            return render_template("register.html")
    else:
        return render_template("register.html")

@app.route("/profile/<username>")
def profile(username):
    login = False
    user = ""
    username = ""
    if "username" in session:
        login = True
        username = session["username"]
        cur = mysql.connection.cursor()
        cur.execute(f"SELECT * FROM login WHERE username='{username}'")
        member = cur.fetchall()
        email = member[0][1]
        user = member[0][2]
        gambar = member[0][-1]
        
        cur.execute(f"SELECT status FROM premium WHERE username='{username}'")
        premium = cur.fetchall()
        if premium:
            status = premium[-1]
        else:
            status = False

    return render_template("profile.html", login=login, nama=user, email=email, gambar=gambar, status=status, username=username)

@app.route("/logout")
def logout():
    session.pop("username",None)
    session.pop("password", None)
    session.pop("nama", None)
    return redirect(url_for('index'))

@app.route("/change_profile")
def change_profile():
    return render_template("change_profile.html")

@app.route("/pencatatan", methods=["GET", "POST"])
def pencatatan():
    if request.method == "POST":
        try:
            tanggal = request.form.get("tanggal")
            pemasukkan = request.form.get("pemasukkan")
            pengeluaran = request.form.get("pengeluaran")
            tabungan = request.form.get("tabungan")
            username = session["username"]
            
            if "/" not in tanggal or tanggal[:2] == "00":
                flash("Gagal membuat catatan!", "danger")
                return redirect(url_for("pencatatan"))
            else:
                tanggal = "-".join(tanggal.split("/")[::-1])
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO pencatatan(tanggal, username, pemasukkan, pengeluaran, tabungan) VALUES (%s, %s, %s, %s, %s)",
                            (tanggal, username, pemasukkan, pengeluaran, tabungan))
                cur2 = cur.fetchall()
                mysql.connection.commit()
                cur.close()
                flash("Berhasil membuat catatan!", "success")
                return redirect(url_for("pencatatan"))
        
        except:
            flash("Gagal membuat catatan!", "danger")
            return redirect(url_for("pencatatan"))
    else:
        username = session["username"]
        cur = mysql.connection.cursor()
        cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
        member = cur.fetchall()
        
        cur.execute(f"SELECT status FROM premium WHERE username='{username}'")
        status = cur.fetchall()
        cur.close()
        if not status:
            return render_template("./pencatatan/pencatatan.html", login=True, username=username)
        elif ("Silahkan bayar" in status[0][0] or not status) or (status[0][0] == "Basic" and len(member) >= 8) or \
            (status[0][0] == "Medium" and len(member) >= 10) or (status[0][0] == "Expert" and len(member) >= 12):
            return redirect(url_for("premium"))
        else:
            return render_template("./pencatatan/pencatatan.html", login=True, username=username)

@app.route("/lihat_catatan")
def lihat_catatan():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
    member = cur.fetchall()
    cur.close()
    tanggal = [i[1] for i in member]
    if tanggal != []:
        pemasukkan = [i[3] for i in member]
        pengeluaran = [i[4] for i in member]
        tabungan = [i[5] for i in member]
        return render_template("./pencatatan/lihat_catatan.html", login=True, username=username, tanggal=tanggal,
                               pemasukkan=pemasukkan, pengeluaran=pengeluaran, tabungan=tabungan, zip=zip)
        
    else:
        flash("Anda belum membuat catatan!", "danger")
        return render_template("./pencatatan/pencatatan.html", login=True, username=username, zip=zip)

@app.route("/delete_catatan/<tanggal>")
def delete_catatan(tanggal):
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"DELETE FROM pencatatan WHERE tanggal='{tanggal}' and username='{username}'")
    cur2 = cur.fetchall()
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("lihat_catatan"))

@app.route("/analisis_pemasukkan")
def analisis_pemasukkan():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
    member = cur.fetchall()
    cur.close()
    tanggal = [i[1] for i in member]
    if tanggal != []:
        pemasukkan = [i[3] for i in member]
        df = pd.DataFrame({
            "tanggal": tanggal,
            "pemasukkan": pemasukkan
        })
        df.set_index("tanggal", inplace=True)
        plt.switch_backend('agg')
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        ax.plot(df["pemasukkan"])
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Pemasukkan")
        ax.set_title("Pemasukkan Anda")
        
        # Simpan plot sebagai BytesIO
        img_bytesio = BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()
        
        mean = df["pemasukkan"].mean()
        median = df["pemasukkan"].median()
        minim = df["pemasukkan"].min()
        maxim = df["pemasukkan"].max()
        std = round(df["pemasukkan"].std(), 2)
        total = df["pemasukkan"].sum()
        count = df["pemasukkan"].count()
        
        # Konversi BytesIO ke data URI
        img_data_uri = base64.b64encode(img_bytesio.getvalue()).decode('utf-8')

        return render_template("./analisis/analisis_pemasukkan.html", login=True, username=username, img_data_uri=img_data_uri,
                               mean=mean, median=median, minim=minim, maxim=maxim, std=std, total=total, count=count)
    else:
        flash("Anda belum membuat catatan!", "danger")
        return render_template("./pencatatan/pencatatan.html", login=True, username=username)

@app.route("/analisis_pengeluaran")
def analisis_pengeluaran():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
    member = cur.fetchall()
    cur.close()
    tanggal = [i[1] for i in member]
    if tanggal != []:
        pengeluaran = [i[4] for i in member]
        df = pd.DataFrame({
            "tanggal": tanggal,
            "pengeluaran": pengeluaran
        })
        df.set_index("tanggal", inplace=True)
        plt.switch_backend('agg')
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        ax.plot(df["pengeluaran"])
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Pengeluaran")
        ax.set_title("Pengeluaran Anda")
        
        # Simpan plot sebagai BytesIO
        img_bytesio = BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()
        
        mean = df["pengeluaran"].mean()
        median = df["pengeluaran"].median()
        minim = df["pengeluaran"].min()
        maxim = df["pengeluaran"].max()
        std = round(df["pengeluaran"].std(), 2)
        total = df["pengeluaran"].sum()
        count = df["pengeluaran"].count()
        
        # Konversi BytesIO ke data URI
        img_data_uri = base64.b64encode(img_bytesio.getvalue()).decode('utf-8')

        return render_template("./analisis/analisis_pengeluaran.html", login=True, username=username, img_data_uri=img_data_uri,
                               mean=mean, median=median, minim=minim, maxim=maxim, std=std, total=total, count=count)
    else:
        flash("Anda belum membuat catatan!", "danger")
        return render_template("./pencatatan/pencatatan.html", login=True, username=username)

@app.route("/analisis_tabungan")
def analisis_tabungan():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
    member = cur.fetchall()
    cur.close()
    tanggal = [i[1] for i in member]
    if tanggal != []:
        tabungan = [i[5] for i in member]
        df = pd.DataFrame({
            "tanggal": tanggal,
            "tabungan": tabungan
        })
        df.set_index("tanggal", inplace=True)
        plt.switch_backend('agg')
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        ax.plot(df["tabungan"])
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Tabungan")
        ax.set_title("Tabungan Anda")
        
        # Simpan plot sebagai BytesIO
        img_bytesio = BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()
        
        mean = df["tabungan"].mean()
        median = df["tabungan"].median()
        minim = df["tabungan"].min()
        maxim = df["tabungan"].max()
        std = round(df["tabungan"].std(), 2)
        total = df["tabungan"].sum()
        count = df["tabungan"].count()
        
        # Konversi BytesIO ke data URI
        img_data_uri = base64.b64encode(img_bytesio.getvalue()).decode('utf-8')

        return render_template("./analisis/analisis_tabungan.html", login=True, username=username, img_data_uri=img_data_uri,
                               mean=mean, median=median, minim=minim, maxim=maxim, std=std, total=total, count=count)
    else:
        flash("Anda belum membuat catatan!", "danger")
        return render_template("./pencatatan/pencatatan.html", login=True, username=username)

@app.route("/prediksi_pemasukkan")
def prediksi_pemasukkan():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
    member = cur.fetchall()
    cur.close()
    tanggal = [i[1] for i in member]
    if tanggal != []:
        pemasukkan = [i[3] for i in member]
        df = pd.DataFrame({
            "tanggal": tanggal,
            "pemasukkan": pemasukkan
        })
        df.set_index("tanggal", inplace=True)
        data = df['pemasukkan']
        
        ema = data.ewm(span=5, adjust=False).mean() 
        prediksi_tiga_langkah_ke_depan = ema.iloc[-1]  # Prediksi untuk waktu selanjutnya
        if len(member) <= 5:
            periods = 3
        elif len(member) <= 8:
            periods = 4
        elif len(member) <= 10:
            periods = 5
        else:
            periods = 6
        
        prediksi_df = pd.DataFrame(index=pd.date_range(start=ema.index[-1] + pd.DateOffset(1), periods=periods, freq='ME'))
            
        prediksi_df['prediksi'] = None

        for waktu in prediksi_df.index:
            # Menambahkan prediksi untuk langkah waktu selanjutnya
            prediksi_df.loc[waktu, 'pemasukkan'] = prediksi_tiga_langkah_ke_depan
            
            # Memperbarui EMA dengan nilai prediksi terbaru
            ema = pd.concat([ema, pd.Series([prediksi_tiga_langkah_ke_depan], index=[waktu])])
            ema = ema.ewm(span=5, adjust=False).mean()
            
            # Memperbarui nilai prediksi untuk langkah waktu selanjutnya
            prediksi_tiga_langkah_ke_depan = ema.iloc[-1]
        
        plt.switch_backend('agg')
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        df2 = pd.concat([df, prediksi_df])
        ax.plot(df2["pemasukkan"], c="orange")
        ax.plot(df["pemasukkan"], c="blue")
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Pemasukkan")
        ax.set_title("Prediksi Pemasukkan Anda")
        
        # Simpan plot sebagai BytesIO
        img_bytesio = BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()
        
        pred = []
        for i in range(periods, 0, -1):
            pred.append(round(ema.iloc[-i]))
        
        # Konversi BytesIO ke data URI
        img_data_uri = base64.b64encode(img_bytesio.getvalue()).decode('utf-8')
        
        return render_template("./prediksi/prediksi_pemasukkan.html", login=True, username=username, img_data_uri=img_data_uri,
                               prediksi=pred, zip=zip)
        
    else:
        flash("Anda belum membuat catatan!", "danger")
        return render_template("./pencatatan/pencatatan.html", login=True, username=username)        

@app.route("/prediksi_pengeluaran")
def prediksi_pengeluaran():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
    member = cur.fetchall()
    cur.close()
    tanggal = [i[1] for i in member]
    if tanggal != []:
        pengeluaran = [i[4] for i in member]
        df = pd.DataFrame({
            "tanggal": tanggal,
            "pengeluaran": pengeluaran
        })
        df.set_index("tanggal", inplace=True)
        data = df['pengeluaran']
        
        ema = data.ewm(span=5, adjust=False).mean() 
        prediksi_tiga_langkah_ke_depan = ema.iloc[-1]  # Prediksi untuk waktu selanjutnya
        if len(member) <= 5:
            periods = 3
        elif len(member) <= 8:
            periods = 4
        elif len(member) <= 10:
            periods = 5
        else:
            periods = 6
        
        prediksi_df = pd.DataFrame(index=pd.date_range(start=ema.index[-1] + pd.DateOffset(1), periods=periods, freq='ME'))
        prediksi_df['prediksi'] = None

        for waktu in prediksi_df.index:
            # Menambahkan prediksi untuk langkah waktu selanjutnya
            prediksi_df.loc[waktu, 'pengeluaran'] = prediksi_tiga_langkah_ke_depan
            
            # Memperbarui EMA dengan nilai prediksi terbaru
            ema = pd.concat([ema, pd.Series([prediksi_tiga_langkah_ke_depan], index=[waktu])])
            ema = ema.ewm(span=5, adjust=False).mean()
            
            # Memperbarui nilai prediksi untuk langkah waktu selanjutnya
            prediksi_tiga_langkah_ke_depan = ema.iloc[-1]
        
        plt.switch_backend('agg')
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        df2 = pd.concat([df, prediksi_df])
        ax.plot(df2["pengeluaran"], c="orange")
        ax.plot(df["pengeluaran"], c="blue")
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Pengeluaran")
        ax.set_title("Prediksi Pengeluaran Anda")
        
        # Simpan plot sebagai BytesIO
        img_bytesio = BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()
        
        pred = []
        for i in range(periods, 0, -1):
            pred.append(round(ema.iloc[-i]))
        
        # Konversi BytesIO ke data URI
        img_data_uri = base64.b64encode(img_bytesio.getvalue()).decode('utf-8')
        
        return render_template("./prediksi/prediksi_pengeluaran.html", login=True, username=username, img_data_uri=img_data_uri,
                               prediksi=pred, zip=zip)
        
    else:
        flash("Anda belum membuat catatan!", "danger")
        return render_template("./pencatatan/pencatatan.html", login=True, username=username)  

@app.route("/prediksi_tabungan")
def prediksi_tabungan():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM pencatatan WHERE username='{username}'")
    member = cur.fetchall()
    cur.close()
    tanggal = [i[1] for i in member]
    if tanggal != []:
        tabungan = [i[5] for i in member]
        df = pd.DataFrame({
            "tanggal": tanggal,
            "tabungan": tabungan
        })
        df.set_index("tanggal", inplace=True)
        data = df['tabungan']
        
        ema = data.ewm(span=5, adjust=False).mean() 
        prediksi_tiga_langkah_ke_depan = ema.iloc[-1]  # Prediksi untuk waktu selanjutnya
        if len(member) <= 5:
            periods = 3
        elif len(member) <= 8:
            periods = 4
        elif len(member) <= 10:
            periods = 5
        else:
            periods = 6
        
        prediksi_df = pd.DataFrame(index=pd.date_range(start=ema.index[-1] + pd.DateOffset(1), periods=periods, freq='ME'))
        prediksi_df['prediksi'] = None

        for waktu in prediksi_df.index:
            # Menambahkan prediksi untuk langkah waktu selanjutnya
            prediksi_df.loc[waktu, 'tabungan'] = prediksi_tiga_langkah_ke_depan
            
            # Memperbarui EMA dengan nilai prediksi terbaru
            ema = pd.concat([ema, pd.Series([prediksi_tiga_langkah_ke_depan], index=[waktu])])
            ema = ema.ewm(span=5, adjust=False).mean()
            
            # Memperbarui nilai prediksi untuk langkah waktu selanjutnya
            prediksi_tiga_langkah_ke_depan = ema.iloc[-1]
        
        plt.switch_backend('agg')
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        df2 = pd.concat([df, prediksi_df])
        ax.plot(df2["tabungan"], c="orange")
        ax.plot(df["tabungan"], c="blue")
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Tabungan")
        ax.set_title("Prediksi Tabungan Anda")
        
        # Simpan plot sebagai BytesIO
        img_bytesio = BytesIO()
        plt.savefig(img_bytesio, format='png')
        img_bytesio.seek(0)
        plt.close()
        
        pred = []
        for i in range(periods, 0, -1):
            pred.append(round(ema.iloc[-i]))
        
        # Konversi BytesIO ke data URI
        img_data_uri = base64.b64encode(img_bytesio.getvalue()).decode('utf-8')
        
        return render_template("./prediksi/prediksi_tabungan.html", login=True, username=username, img_data_uri=img_data_uri,
                               prediksi=pred, zip=zip)
        
    else:
        flash("Anda belum membuat catatan!", "danger")
        return render_template("./pencatatan/pencatatan.html", login=True, username=username)  

@app.route("/premium")
def premium():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT * FROM premium WHERE username = '{username}'")
    member = cur.fetchall()
    if member:
        status = member[0][-1]
    else:
        status = []
    cur.close()
    
    return render_template("premium.html", login=login, username=username, status=status)

@app.route("/premium_checkout/<status>")
def premium_checkout(status):
    login = True
    tanggal = datetime.now().date()
    username = session["username"]
    status = f"Silahkan bayar {status}"
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO premium(tanggal, username, status) VALUES (%s, %s, %s)", (tanggal, username, status))
    cur2 = cur.fetchall()
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for("premium"))

@app.route("/lihat_premium")
def lihat_premium():
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute("SELECT tanggal, username, status FROM premium")
    member = cur.fetchall()
    tanggal = [i[0] for i in member]
    user = [i[1] for i in member]
    status = [i[2] for i in member]
    cur.close()
    
    return render_template("./admin/lihat_premium.html", login=login, tanggal=tanggal, user=user, status=status, 
                           username=username, zip=zip)
 
@app.route("/acc_premium/<user>")
def acc_premium(user):
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"SELECT status FROM premium WHERE username='{user}'")
    status = cur.fetchall()[0][0]
    if status == "Silahkan bayar Basic":
        cur.execute(f"UPDATE premium SET status = 'Basic' where username='{user}'")
        cur2 = cur.fetchall()
        mysql.connection.commit()
        
    elif status == "Silahkan bayar Medium":
        cur.execute(f"UPDATE premium SET status = 'Medium' where username='{user}'")
        cur2 = cur.fetchall()
        mysql.connection.commit()
    
    elif status == "Silahkan bayar Expert":
        cur.execute(f"UPDATE premium SET status = 'Expert' where username='{user}'")
        cur2 = cur.fetchall()
        mysql.connection.commit()
    
    cur.close()
    
    return redirect(url_for("lihat_premium"))

@app.route("/clear_premium/<user>")
def clear_premium(user):
    login = True
    username = session["username"]
    cur = mysql.connection.cursor()
    cur.execute(f"DELETE FROM premium WHERE username='{user}'")
    cur2 = cur.fetchall()
    mysql.connection.commit()
    cur.close()
    
    return redirect(url_for("lihat_premium"))


if __name__ == "__main__":
    app.run(debug=True)