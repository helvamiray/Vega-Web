from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3 
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# --- GÜVENLİK VE MAİL AYARLARI ---
app.secret_key = 'vega_enerji_ozel_anahtar'
app.config['MAIL_SERVER'] = 'smtp.mail.me.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mirayhelva15@icloud.com' 
app.config['MAIL_PASSWORD'] = 'iifl-yabc-ivtl-rirg' 
mail = Mail(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# VERİTABANI BAŞLATMA (Ürünlerin silinmemesi için güncellendi)
def init_db():
    conn = get_db_connection()
    # "IF NOT EXISTS" kullanarak tablo varsa dokunmamasını sağlıyoruz
    conn.execute('''
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            ad TEXT NOT NULL, 
            marka TEXT,
            kategori TEXT,
            aciklama TEXT, 
            resim_yolu TEXT
        )
    ''')
    conn.close()

# 1. ANA SAYFA
@app.route('/')
def index():
    conn = get_db_connection()
    urunler = conn.execute('SELECT * FROM urunler').fetchall()
    conn.close()
    return render_template('index.html', urunler=urunler)

# 2. ADMİN GİRİŞ (Şifre: efa123 yapıldı)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sifre = request.form.get('sifre')
        if sifre == 'efa123': # İstediğin şifre buraya eklendi
            session['admin_giris'] = True
            return redirect(url_for('admin'))
        return "Hatalı Şifre! Lütfen tekrar deneyin."
    return '''
        <div style="text-align:center; margin-top:100px; font-family:sans-serif; background:#f4f7f9; padding:50px;">
            <div style="display:inline-block; background:white; padding:30px; border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.1);">
                <h2 style="color:#003366;">Vega Admin Girişi</h2>
                <form method="post">
                    <input type="password" name="sifre" placeholder="Admin Şifresi" required 
                           style="padding:12px; width:200px; border:1px solid #ddd; border-radius:8px; margin-bottom:10px;"><br>
                    <button type="submit" 
                            style="padding:12px 30px; background:#003366; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">
                        Giriş Yap
                    </button>
                </form>
            </div>
        </div>
    '''

# 3. ADMİN PANELİ
@app.route('/admin')
def admin():
    if not session.get('admin_giris'): return redirect(url_for('login'))
    conn = get_db_connection()
    urunler = conn.execute('SELECT * FROM urunler').fetchall()
    conn.close()
    return render_template('admin.html', urunler=urunler)

# 4. ÜRÜN EKLEME
@app.route('/admin/ekle', methods=['POST'])
def urun_ekle():
    if not session.get('admin_giris'): return redirect(url_for('login'))
    ad = request.form.get('ad')
    marka = request.form.get('marka')
    kategori = request.form.get('kategori')
    aciklama = request.form.get('aciklama')
    resim_yolu = request.form.get('resim_yolu')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO urunler (ad, marka, kategori, aciklama, resim_yolu) VALUES (?, ?, ?, ?, ?)',
                  (ad, marka, kategori, aciklama, resim_yolu))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# 5. ÜRÜN SİLME
@app.route('/admin/sil/<int:id>')
def urun_sil(id):
    if not session.get('admin_giris'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM urunler WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# 6. TEKLİF GÖNDERME
@app.route('/teklif-gonder', methods=['POST'])
def teklif_gonder():
    try:
        data = request.get_json()
        urunler_yazisi = ", ".join(data.get('urunler', []))
        
        msg = Message("Vega Enerji - Yeni Teklif Talebi",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['mirayhelva15@icloud.com'])
        
        msg.body = f"""
        Sayın Yetkili, web sitesinden yeni bir teklif talebi geldi:

        Müşteri Bilgileri:
        ------------------
        İsim: {data.get('isim')}
        Firma: {data.get('firma')}
        Telefon: {data.get('tel')}
        E-posta: {data.get('email')}

        İstenen Ürünler:
        ------------------
        {urunler_yazisi}

        Müşteri Notu:
        ------------------
        {data.get('not')}
        """
        
        mail.send(msg)
        return jsonify({"status": "success", "message": "Mail gönderildi"})
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 7. ÇIKIŞ
@app.route('/logout')
def logout():
    session.pop('admin_giris', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db() # Tablo yoksa oluşturur, varsa dokunmaz.
    app.run(debug=True)