from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
import locale
from bson import ObjectId
import json

import os
from os.path import join, dirname
from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

locale.setlocale(locale.LC_TIME, 'id_ID')

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app = Flask(__name__)
SECRET_KEY = os.environ.get("SECRET_KEY")

# _________________ Token User ________________________________________________


def get_user_info():
    token_receive = request.cookies.get("mytoken")
    user_info = None
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY,
                                 algorithms=["HS256"])
            user_info = db.users.find_one({"nama": payload["id"]})
        except jwt.ExpiredSignatureError:
            pass
        except jwt.exceptions.DecodeError:
            pass
    return user_info


@app.context_processor
def inject_user_info():
    user_info = get_user_info()
    return dict(user_info=user_info)

# _________________ End Token User ________________________________________________

# _________________ Token Admin ________________________________________________


def get_admin_info():
    token_receive = request.cookies.get("mytoken")
    admininfo = None
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY,
                                 algorithms=["HS256"])
            admininfo = db.admin.find_one({"admin": payload["id"]})
        except jwt.ExpiredSignatureError:
            pass
        except jwt.exceptions.DecodeError:
            pass
    return admininfo


@app.context_processor
def inject_admin_info():
    admininfo = get_admin_info()
    return dict(admininfo=admininfo)

# _________________ End Token Admin ________________________________________________


def get_user_data():
    users_info = get_user_info()
    jumlah_user = db.users.count_documents({})
    jumlah_antri = db.antrian.count_documents({})
    jumlah_mcu = db.medical_checkup.count_documents({})
    users = db.users.find({})
    antrian = db.antrian.find({})
    mcu = db.medical_checkup.find({})
    hasil_mcu = db.hasil_mcu.find({})
    data_user = db.users.find_one({'_id': users_info})

    mcu_data = db.medical_checkup.find({}, {'nama_mcu': 1})
    mcu_list = [mcu_item['nama_mcu'] for mcu_item in mcu_data]

    informasi = {
        'jumlah_user': jumlah_user,
        'jumlah_antrian': jumlah_antri,
        'user': users,
        'mcu': mcu,
        'antrian': antrian,
        'mcu_jumlah': jumlah_mcu,
        'data_user': data_user,
        'mcu_list': mcu_list,
        'hasil_mcu': hasil_mcu,
    }
    return informasi


def get_all_users():
    users_collection = db.users
    users = users_collection.find({})
    result = []

    for user in users:
        result.append({'id': str(user['_id']), 'nama': user.get('nama', '')})

    return result


def get_updated_user_data():
    users_info = get_user_info()
    jumlah_user = db.users.count_documents({})
    jumlah_antri = db.antrian.count_documents({})
    jumlah_mcu = db.medical_checkup.count_documents({})
    users = db.users.find({})
    antrian = db.antrian.find({})
    informasi = {
        'jumlah_user': jumlah_user,
        'jumlah_antrian': jumlah_antri,
        'user': users,
        'antrian': antrian,
        'mcu': jumlah_mcu,
    }
    return informasi


@app.context_processor
def inject_user_info():
    informasi = get_user_data()
    return dict(informasi=informasi)


def get_user_mcu_data():
    user_info = get_user_info()
    if user_info:
        user_id = user_info['_id']
        user_id = str(user_id)
        hasil_mcu_data = list(db.hasil_mcu.find({"user_id": user_id}))
        return {"hasil_mcu": hasil_mcu_data}
    else:
        return {"hasil_mcu": []}

# _________________ Login Page Display ________________________________________________


@app.route('/login', methods=['GET'])
def show_login():
    return render_template('user/login.html')

# _________________ Login Process ________________________________________________


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        nama_received = request.form["nama"]
        nik_received = request.form["nik"]

        hashed_nik = hashlib.sha256(nik_received.encode("utf-8")).hexdigest()

        user = db.users.find_one({'nama': nama_received, 'nik': hashed_nik})

        if user:
            token = jwt.encode({'id': nama_received, "exp": datetime.utcnow(
            ) + timedelta(seconds=60 * 60 * 24)}, SECRET_KEY, algorithm='HS256')
            response = jsonify({
                "result": "success",
                "token": token,
                'message': 'Selamat datang'
            })
            response.set_cookie('mytoken', token)
            return response
        else:
            return jsonify({'error': 'Invalid credentials', 'message': 'Data tidak valid'})

# _________________ Encrypted Pages ________________________________________________


@app.route('/pendaftaranonline', methods=['GET'])
def show_pendaftaranonline():
    user_info = get_user_info()
    if not user_info:
        return redirect(url_for("login"))

    user_data = db.users.find_one({'_id': user_info['_id']})

    if user_data:
        nama_pengguna = user_data.get('nama')
        nik_pengguna = user_data.get('nik')

        return render_template('user/pendaftaranonline.html', nama=nama_pengguna, nik=nik_pengguna, user_info=user_info)
    else:
        return jsonify({'error': 'Data pengguna tidak ditemukan'})

# _________________ Queue Registration ________________________________________________


@app.route('/pendaftaranonline', methods=['POST'])
def pendaftaranonline():
    if request.method == 'POST':

        nama = request.form['nama']
        tanggal = request.form['tanggal']
        sesi = request.form['sesi']
        mcu = request.form['mcu']

        user_info = get_user_info() if get_user_info() else {'_id': None}

        if not (tanggal and sesi and mcu and nama):
            return jsonify({'result': 'error', 'message': 'Data tidak lengkap'})

        tanggal_obj = datetime.strptime(tanggal, '%Y-%m-%d')
        tanggal_formatted = tanggal_obj.strftime('%d %b %Y')
        hari = tanggal_obj.strftime("%A")

        tanggal_sekarang = datetime.now()

        if tanggal_obj < tanggal_sekarang:
            return jsonify({'result': 'error', 'message': 'Pendaftaran tidak bisa dilakukan untuk tanggal yang sudah lewat'})

        if hari == "Sabtu" or hari == "Minggu":
            return jsonify({'result': 'error', 'message': 'Pelayanan Tidak Tersedia Pada Akhir Pekan (Sabtu atau Minggu)'})

        if sesi.lower() == "pagi":
            jam_awal = datetime.strptime('08:00', '%H:%M')
            jam_akhir = datetime.strptime('12:00', '%H:%M')
            durasi_per_antrian = timedelta(minutes=60)
        elif sesi.lower() == "siang":
            jam_awal = datetime.strptime('12:30', '%H:%M')
            jam_akhir = datetime.strptime('14:30', '%H:%M')
            durasi_per_antrian = timedelta(minutes=15)
        elif sesi.lower() == "sore":
            jam_awal = datetime.strptime('15:00', '%H:%M')
            jam_akhir = datetime.strptime('18:00', '%H:%M')
            durasi_per_antrian = timedelta(minutes=15)
        else:
            return jsonify({'result': 'error', 'message': 'Sesi tidak valid'})

        if db.antrian.find_one({"user_id": user_info["_id"], "tanggal": tanggal_formatted}):
            return jsonify({'result': 'error', 'message': f'Anda sudah mendaftar pada Hari {hari}, {tanggal_formatted} '})

        # _________________ Antrian _________________________
        if db.antrian.count_documents({"tanggal": tanggal_formatted,
                                       "sesi": sesi,
                                       "mcu": mcu}) == 0:
            nomor_antrian_baru = 1
            jam = jam_awal
        else:
            last_item = db.antrian.find_one(sort=[('_id', -1)])

            if (last_item['tanggal'] != tanggal_formatted and
                last_item['sesi'] != sesi and
                    last_item['mcu'] != mcu):

                nomor_antrian_baru = 1
                jam = jam_awal
            else:
                nomor_antrian_baru = last_item['nomor_antrian'] + 1
                last_jam = datetime.strptime(last_item['jam'], '%H:%M')
                jam = last_jam + durasi_per_antrian
                if jam >= jam_akhir:
                    return jsonify({'result': 'error', 'message': f'Maaf Untuk Sesi {sesi} hari {hari}, {tanggal_formatted} sudah habis'})

        data_pendaftaran = {
            'user_id': user_info["_id"],
            'nama': nama,
            'nomor_antrian': nomor_antrian_baru,
            'hari': hari,
            'jam': jam.strftime('%H:%M'),
            'tanggal': tanggal_formatted,
            'sesi': sesi,
            'mcu': mcu,
            'nomor_antrian': nomor_antrian_baru
        }
        db.antrian.insert_one(data_pendaftaran)

        return jsonify({'result': 'success', 'nama': nama,
                        'nomor_antrian': nomor_antrian_baru,
                        'hari': hari,
                        'tanggal': tanggal_formatted,
                        'sesi': sesi,
                        'jam': jam.strftime('%H:%M'),
                        'mcu': mcu,
                        'nomor_antrian': nomor_antrian_baru})

# _________________ Register Page Display ________________________________________________


@app.route('/register', methods=['GET'])
def show_register():
    return render_template('user/register.html')

# _________________ Registration Process ________________________________________________


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        nama = request.form['nama']
        nik = request.form['nik']
        jenis_kelamin = request.form['gender']
        alamat = request.form['alamat']

        if jenis_kelamin == '1':
            jenis_kelamin = 'LAKI-LAKI'
        elif jenis_kelamin == '2':
            jenis_kelamin = 'PEREMPUAN'

        if not nik or len(nik) != 16:
            return jsonify({'result': 'error', 'message': 'NIK harus terdiri dari 16 karakter!'})

        if not (nama and nik and jenis_kelamin and alamat):
            return jsonify({'result': 'error', 'message': 'Harap Isi Semua Data'})

        hashed_nik = hashlib.sha256(nik.encode()).hexdigest()

        user = {
            'nama': nama,
            'nik': hashed_nik,
            'jenis_kelamin': jenis_kelamin,
            'alamat': alamat
        }

        existing_user = db.users.find_one({'nik': hashed_nik})
        if existing_user:
            return jsonify({'result': 'error', 'message': 'NIK sudah terdaftar'})

        db.users.insert_one(user)

        return jsonify({'result': 'success', 'message': 'Registrasi berhasil', 'redirect_url': '/login'})

# _________________ Home Pages Display ________________________________________________


@app.route('/')
def home():
    user_info = get_user_info()
    return render_template('user/index.html', user_info=user_info)

# _________________ Queue Pages Display ________________________________________________


@app.route('/antrian')
def antrian():
    token = request.cookies.get('token')
    data_antrian = list(db.antrian.aggregate([
        {"$group": {
            "_id": "$mcu",
            "totalPendaftar": {"$sum": 1}
        }}
    ]))

    return render_template('user/antrian.html', token=token, data_antrian=data_antrian)

# _________________ Instruction Pages Display ________________________________________________


@app.route('/petunjuk')
def petunjuk():
    user_info = get_user_info()
    return render_template('user/petunjuk.html', user_info=user_info)

# _________________ Article Pages Display ________________________________________________


@app.route('/artikelkolesterol')
def artikelkolesterol():
    return render_template('user/artikelkolesterol.html')


@app.route('/artikelguladarah')
def artikelguladarah():
    return render_template('user/artikelguladarah.html')


@app.route('/artikelurine')
def artikelurine():
    return render_template('user/artikelurine.html')

# _________________ Account Pages Display ________________________________________________


@app.route('/akun')
def akun():

    user_info = get_user_info()
    if not user_info:
        return redirect(url_for("login"))

    user_data = db.users.find_one({'_id': user_info[str('_id')]})

    if user_data:
        nama_pengguna = user_data.get('nama')
        nik_pengguna = user_data.get('nik')
        informasi_user = {
            'nama': user_data.get('nama'),
            'jenis_kelamin': user_data.get('jenis_kelamin'),
            'alamat': user_data.get('alamat')
        }

        return render_template('user/akun.html', nama=nama_pengguna, nik=nik_pengguna, user_info=user_info, informasi_user=informasi_user)
    else:
        return jsonify({'error': 'Data pengguna tidak ditemukan'})

# _________________ Admin Pages Encrypted ________________________________________________


@app.route('/admin', methods=['GET'])
def homeAdmin():
    admininfo = get_admin_info()

    if not admininfo:
        return redirect(url_for("show_loginAdmin"))

    admin_data = db.admin.find_one({'admin': admininfo['admin']})

    if admin_data:
        admin_log = admin_data.get('admin')
        password_log = admin_data.get('password')
        informasi = get_user_data()

        return render_template('admin/dashboard.html', admin=admin_log, password=password_log, active_page='homeAdmin', informasi=informasi)
    else:
        return jsonify({'error': 'Data pengguna tidak ditemukan'})


# _________________ Admin Login Process ________________________________________________
@app.route('/admin/login', methods=['POST'])
def loginAdmin():
    if request.method == 'POST':
        nama_received = request.form["nama"]
        pass_received = request.form["pass"]

        admin = db.admin.find_one(
            {'admin': nama_received, 'password': pass_received})

        if admin:
            token = jwt.encode({'id': nama_received, "exp": datetime.utcnow(
            ) + timedelta(seconds=60 * 60 * 24)}, SECRET_KEY, algorithm='HS256')
            response = jsonify({
                "result": "success",
                "token": token
            })
            response.set_cookie('mytoken', token)
            return response
        else:
            return jsonify({'error': 'Invalid credentials'})

# _________________ Login Admin Pages Display ________________________________________________


@app.route("/admin/login", methods=['GET'])
def show_loginAdmin():
    return render_template("admin/login-admin.html")

# _________________ Edit Detail Rumah Sakit ________________________________________________


@app.route('/admin/detail/mcu/editrs')
def editrs():
    admininfo = get_admin_info()
    if not admininfo:
        return redirect(url_for("show_loginAdmin"))
    admin_data = db.admin.find_one({'admin': admininfo['admin']})
    if admin_data:
        admin = admin_data.get('admin')
        password = admin_data.get('password')

        return render_template('admin/editrs.html', admin=admin, password=password, admininfo=admininfo)
    else:
        return jsonify({'error': 'Data pengguna tidak ditemukan'})


@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        token_receive = request.cookies.get("mytoken")
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        nama_mcu = request.form['nama_mcu']
        detailrs_mcu = request.form['detailrs_mcu']

        doc = {
            "nama_mcu": nama_mcu,
            "detailrs_mcu": detailrs_mcu,
            "user_id": payload["id"]
        }
        db.medical_checkup.insert_one(doc)
        return jsonify({'message': 'Data Berhasil Disimpan!', 'success': True})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({'message': 'Token tidak valid!'})


@app.route('/admin/detail/users')
def detail_users():

    informasi = get_user_data()
    admininfo = get_admin_info()
    if not admininfo:
        return redirect(url_for("show_loginAdmin"))
    admin_data = db.admin.find_one({'admin': admininfo['admin']})
    if admin_data:
        admin = admin_data.get('admin')
        password = admin_data.get('password')

        return render_template('admin/user.html', informasi=informasi, active_page="detail_users", admininfo=admininfo)
    else:
        return jsonify({'error': 'Data pengguna tidak ditemukan'})


@app.route('/delete_mcu', methods=['POST'])
def delete_mcu():
    data = request.get_json()
    _id = data['_id']

    try:
        db.medical_checkup.delete_one({"_id": ObjectId(_id)})
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json()
    _id = data['_id']

    try:
        db.users.delete_one({"_id": ObjectId(_id)})
        # db.antrian.delete_many({'user_id': id})

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/delete_antrian', methods=['POST'])
def delete_antrian():
    data = request.get_json()
    _id = data['_id']

    try:
        db.antrian.delete_one({"_id": ObjectId(_id)})
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/admin/detail/antrian')
def detail_antrian():
    informasi = get_user_data()
    admininfo = get_admin_info()
    data_from_db = list(db.antrian.find({}))
    for doc in data_from_db:
        doc['tanggal'] = datetime.strptime(doc['tanggal'], '%d %b %Y')
    sorted_data = sorted(data_from_db, key=lambda x: x['tanggal'])

    if not admininfo:
        return redirect(url_for("show_loginAdmin"))
    admin_data = db.admin.find_one({'admin': admininfo['admin']})
    if admin_data:
        admin = admin_data.get('admin')
        password = admin_data.get('password')

        return render_template('admin/antrian.html', informasi=informasi, sorted_data=sorted_data, active_page="detail_antrian", admininfo=admininfo)


@app.route('/admin/detail/mcu')
def detail_mcu():

    informasi = get_user_data()
    return render_template('admin/das_mcu.html', informasi=informasi, active_page="detail_mcu")


@app.route('/admin/hasil')
def hasil():

    informasi = get_user_data()
    return render_template('admin/das_hasil.html', informasi=informasi, active_page="hasil")


@app.route('/hasil_mcu')
def hasil_mcu():
    informasi_mcu = get_user_mcu_data()
    return render_template('user/hasil_mcu.html', informasi_mcu=informasi_mcu)


@app.route('/admin/mcu')
def mcu():
    informasi = get_user_data()
    user_info = get_user_info()
    all_users = get_all_users()
    return render_template('admin/mcu.html', informasi=informasi, user_info=user_info, all_users=all_users)


@app.route('/save_hasil_mcu', methods=['POST'])
def save_hasil_mcu():
    try:
        token_receive = request.cookies.get("mytoken")
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        user_id = request.form.get('user_id')
        nama = request.form.get('nama')
        tanggal_lahir = request.form.get('tanggal_lahir')
        umur = request.form.get('umur')
        jenis_kelamin = request.form.get('jenis_kelamin')
        alamat = request.form.get('alamat')
        tanggal_pemeriksaan = request.form.get('tanggal_pemeriksaan')
        berat_badan = request.form.get('berat_badan')
        tinggi_badan = request.form.get('tinggi_badan')
        tekanan_darah = request.form.get('tekanan_darah')
        kolesterol_total = request.form.get('kolesterol_total')
        kolesterol_hdl = request.form.get('kolesterol_hdl')
        kolesterol_ldl = request.form.get('kolesterol_ldl')
        gula_darah_puasa = request.form.get('gula_darah_puasa')
        gula_darah_sewaktu = request.form.get('gula_darah_sewaktu')
        gula_darah_sesudah_makan = request.form.get('gula_darah_sesudah_makan')
        warna_urine = request.form.get('warna_urine')
        kejernihan_urine = request.form.get('kejernihan_urine')
        nitrit_urine = request.form.get('nitrit_urine')
        protein_urine = request.form.get('protein_urine')
        glukosa_urine = request.form.get('glukosa_urine')

        if not (nama and tanggal_lahir and umur and jenis_kelamin and alamat and tanggal_pemeriksaan and berat_badan and tinggi_badan and tekanan_darah and kolesterol_total and kolesterol_hdl and kolesterol_ldl and gula_darah_puasa and gula_darah_sewaktu and gula_darah_sesudah_makan and warna_urine and kejernihan_urine and nitrit_urine and protein_urine and glukosa_urine and user_id):
            return jsonify({'message': 'Data MCU Kolesterol tidak lengkap', 'success': False})

        doc = {
            "user_id": user_id,
            "nama": nama,
            "tanggal_lahir": tanggal_lahir,
            "umur": umur,
            "jenis_kelamin": jenis_kelamin,
            "alamat": alamat,
            "tanggal_pemeriksaan": tanggal_pemeriksaan,
            "berat_badan": berat_badan,
            "tinggi_badan": tinggi_badan,
            "tekanan_darah": tekanan_darah,
            "kolesterol_total": kolesterol_total,
            "kolesterol_hdl": kolesterol_hdl,
            "kolesterol_ldl": kolesterol_ldl,
            "gula_darah_puasa": gula_darah_puasa,
            "gula_darah_sewaktu": gula_darah_sewaktu,
            "gula_darah_sesudah_makan": gula_darah_sesudah_makan,
            "warna_urine": warna_urine,
            "kejernihan_urine": kejernihan_urine,
            "nitrit_urine": nitrit_urine,
            "protein_urine": protein_urine,
            "glukosa_urine": glukosa_urine
        }
        db.hasil_mcu.insert_one(doc)

        return jsonify({'message': 'Data Hasil MCU berhasil disimpan!', 'success': True})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({'message': 'Token tidak valid!', 'success': False})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
