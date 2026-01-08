import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, redirect, url_for
import base64
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'wayang_heritage_secret_key'

# ==========================================
# 1. INISIALISASI FIREBASE
# ==========================================
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred) 

db = firestore.client()
COLLECTION_NAME = 'admin' 

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def convert_file_to_base64(file):
    if not file: return None
    file.seek(0, 2); size = file.tell(); file.seek(0)
    # Batas ukuran gambar (misal 1MB)
    if size > 1050000: return "ERROR_SIZE"
    try:
        file_content = file.read()
        encoded_str = base64.b64encode(file_content).decode('utf-8')
        return f"data:{file.content_type};base64,{encoded_str}"
    except Exception as e:
        print(f"Error: {e}")
        return None

def time_ago(timestamp):
    if not timestamp: return ""
    now = datetime.now()
    try:
        diff = now - timestamp.replace(tzinfo=None)
        seconds = diff.total_seconds()
        if seconds < 60: return "Baru saja"
        elif seconds < 3600: return f"{int(seconds // 60)} menit lalu"
        elif seconds < 86400: return f"{int(seconds // 3600)} jam lalu"
        elif seconds < 604800: return f"{int(seconds // 86400)} hari lalu"
        else: return timestamp.strftime("%d %b %Y")
    except Exception:
        return "Baru saja"

# ==========================================
# 3. ROUTE DASHBOARD (INDEX)
# ==========================================
@app.route('/')
def index():
    # A. Users
    users_ref = db.collection('users').stream()
    users = []
    total_xp = 0
    for doc in users_ref:
        u = doc.to_dict(); u['id'] = doc.id
        xp = int(u.get('xp', 0)); total_xp += xp; u['xp'] = xp
        if 'name' not in u: u['name'] = 'Tanpa Nama'
        if 'email' not in u: u['email'] = 'no-email@example.com'
        users.append(u)
    users.sort(key=lambda x: x['xp'], reverse=True)

    # B. Comments
    comments_ref = db.collection('comments').order_by('created_at', direction=firestore.Query.DESCENDING).limit(9).stream()
    comments = []
    for doc in comments_ref:
        c = doc.to_dict()
        c['time_ago'] = time_ago(c.get('created_at'))
        if 'user_name' not in c: c['user_name'] = 'Pengguna'
        if 'rating' not in c: c['rating'] = 5
        if 'text' not in c: c['text'] = ''
        if 'content_title' not in c: c['content_title'] = 'Konten'
        c['content_type'] = c.get('content_type', 'Umum')
        comments.append(c)

    return render_template('index.html', active_page='dashboard', users=users, total_users=len(users), total_xp="{:,.0f}".format(total_xp), comments=comments)

# ==========================================
# 4. ROUTE FILTER KONTEN
# ==========================================

MUSEUM_CATS = ['Museum', 'Galeri', 'Cagar Budaya', 'Sanggar', 'Tempat']
EVENT_CATS = ['Event', 'Agenda', 'Jadwal', 'Pertunjukan', 'Festival']
WAYANG_CATS = ['Wayang Kulit', 'Wayang Golek', 'Wayang Orang', 'Wayang Klithik', 'Wayang Beber', 'Lainnya']
DALANG_CATS = ['Dalang', 'Maestro', 'Legend', 'Senior', 'Profesional', 'Dalang Muda']
NON_KISAH_CATS = DALANG_CATS + WAYANG_CATS + EVENT_CATS + MUSEUM_CATS + ['Video']

@app.route('/kisah')
def kisah():
    all_docs = db.collection(COLLECTION_NAME).stream()
    content_list = []
    for doc in all_docs:
        data = doc.to_dict(); data['id'] = doc.id
        cat = data.get('category', '').title()
        if (cat not in NON_KISAH_CATS) and ('maps_url' not in data) and ('time' not in data) and ('performer' not in data):
            content_list.append(data)
    return render_template('kisah.html', contents=content_list, active_page='kisah')

@app.route('/tokoh-wayang')
def tokoh_wayang():
    all_docs = db.collection(COLLECTION_NAME).stream()
    content_list = []
    for doc in all_docs:
        data = doc.to_dict(); data['id'] = doc.id
        cat = data.get('category', '')
        if cat in WAYANG_CATS:
            content_list.append(data)
    return render_template('tokoh_wayang.html', contents=content_list, active_page='tokoh-wayang')

@app.route('/tokoh-dalang')
def tokoh_dalang():
    all_docs = db.collection(COLLECTION_NAME).stream()
    content_list = []
    for doc in all_docs:
        data = doc.to_dict(); data['id'] = doc.id
        cat = data.get('category', '')
        if cat in DALANG_CATS:
            content_list.append(data)
    return render_template('tokoh_dalang.html', contents=content_list, active_page='tokoh-dalang')

@app.route('/museum')
def museum():
    all_docs = db.collection(COLLECTION_NAME).stream()
    content_list = []
    for doc in all_docs:
        data = doc.to_dict(); data['id'] = doc.id
        cat = data.get('category', '')
        is_museum_cat = cat in MUSEUM_CATS
        has_location = 'maps_url' in data
        is_event = (cat in EVENT_CATS) or ('time' in data) or ('performer' in data)
        if is_museum_cat or (has_location and not is_event):
            content_list.append(data)
    return render_template('museum.html', contents=content_list, active_page='museum')

@app.route('/event')
def event():
    all_docs = db.collection(COLLECTION_NAME).stream()
    content_list = []
    for doc in all_docs:
        data = doc.to_dict(); data['id'] = doc.id
        cat = data.get('category', '')
        is_event_cat = cat in EVENT_CATS
        has_event_props = ('time' in data) or ('performer' in data)
        if is_event_cat or has_event_props:
            content_list.append(data)
    return render_template('event.html', contents=content_list, active_page='event')

@app.route('/video')
def video():
    all_docs = db.collection(COLLECTION_NAME).stream()
    content_list = []
    for doc in all_docs:
        data = doc.to_dict(); data['id'] = doc.id
        if data.get('category') == 'Video':
            content_list.append(data)
    return render_template('video.html', contents=content_list, active_page='video')

# ==========================================
# 5. CRUD (SIMPAN & HAPUS) - UPDATED
# ==========================================
@app.route('/save', methods=['POST'])
def save_content():
    if request.method == 'POST':
        content_id = request.form.get('id')
        
        # Data dasar (Subtitle/Durasi DIHAPUS dari sini)
        data = {
            'title': request.form['title'],
            'category': request.form['category'],
            'description': request.form['description'],
            'status': request.form['status'],
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        # Opsi tambahan (Subtitle juga tidak perlu masuk sini)
        opts = ['price', 'phone', 'maps_url', 'time', 'performer', 'location', 'publish_date']
        for opt in opts:
            if request.form.get(opt): data[opt] = request.form.get(opt)

        # 1. Handle Gambar (Thumbnail/Cover)
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            base64_image = convert_file_to_base64(image_file)
            if base64_image == "ERROR_SIZE": return "GAGAL: Ukuran GAMBAR > 1MB."
            elif base64_image: data['image_url'] = base64_image

        # 2. Handle Video Link
        youtube_link = request.form.get('video_link')
        if youtube_link:
            data['video_url'] = youtube_link

        # Simpan ke Firestore
        if content_id:
            db.collection(COLLECTION_NAME).document(content_id).update(data)
        else:
            data['created_at'] = firestore.SERVER_TIMESTAMP
            if 'image_url' not in data: 
                data['image_url'] = 'https://via.placeholder.com/400x300?text=No+Image'
            db.collection(COLLECTION_NAME).add(data)
            
        return redirect(request.referrer or url_for('index'))

@app.route('/delete/<id>')
def delete_content(id):
    db.collection(COLLECTION_NAME).document(id).delete()
    return redirect(request.referrer or url_for('index'))

@app.route('/setting')
def setting():
    return render_template('setting.html', active_page='setting', settings={"site_title": "Ensiklopedi Wayang", "maintenance_mode": False})

if __name__ == '__main__':
    app.run(debug=True)