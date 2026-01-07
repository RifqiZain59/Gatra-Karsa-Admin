import firebase_admin
from firebase_admin import credentials, firestore, storage
from flask import Flask, render_template, request, redirect, url_for
import uuid

app = Flask(__name__)
app.secret_key = 'wayang_heritage_secret_key'

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'id-project-anda.firebasestorage.app' 
    })

db = firestore.client()
bucket = storage.bucket()
COLLECTION_NAME = 'wayang_content'

@app.route('/')
def index():
    docs = db.collection(COLLECTION_NAME).order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    content_list = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        content_list.append(data)
    return render_template('index.html', contents=content_list, active_page='dashboard')


@app.route('/kisah')
def kisah():
    # Ambil data khusus kategori 'Kisah'
    docs = db.collection(COLLECTION_NAME).where('category', '==', 'Kisah').stream()
    content_list = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        content_list.append(data)
    # Render file khusus kisah.html
    return render_template('kisah.html', contents=content_list, active_page='kisah')

@app.route('/tokoh-wayang')
def tokoh_wayang():
    docs = db.collection(COLLECTION_NAME).where('category', '==', 'Tokoh Wayang').stream()
    content_list = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        content_list.append(data)
    return render_template('tokoh_wayang.html', contents=content_list, active_page='tokoh-wayang')

@app.route('/tokoh-dalang')
def tokoh_dalang():
    docs = db.collection(COLLECTION_NAME).where('category', '==', 'Tokoh Dalang').stream()
    content_list = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        content_list.append(data)
    return render_template('tokoh_dalang.html', contents=content_list, active_page='tokoh-dalang')

@app.route('/museum')
def museum():
    docs = db.collection(COLLECTION_NAME).where('category', '==', 'Museum').stream()
    content_list = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        content_list.append(data)
    return render_template('museum.html', contents=content_list, active_page='museum')

@app.route('/event')
def event():
    docs = db.collection(COLLECTION_NAME).where('category', '==', 'Event').stream()
    content_list = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        content_list.append(data)
    return render_template('event.html', contents=content_list, active_page='event')

# =========================================================

@app.route('/settings')
def settings():
    return render_template('settings.html', active_page='settings')

@app.route('/save', methods=['POST'])
def save_content():
    if request.method == 'POST':
        content_id = request.form.get('id')
        data = {
            'title': request.form['title'],
            'subtitle': request.form['subtitle'],
            'category': request.form['category'],
            'description': request.form['description'],
            'status': request.form['status'],
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        file = request.files.get('image')
        if file and file.filename != '':
            extension = file.filename.split('.')[-1]
            filename = f"uploads/{uuid.uuid4()}.{extension}"
            blob = bucket.blob(filename)
            blob.upload_from_file(file, content_type=file.content_type)
            blob.make_public()
            data['image_url'] = blob.public_url

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
    app_settings = {
        "site_title": "Ensiklopedi Wayang Nusantara",
        "admin_email": "admin@wayang.id",
        "maintenance_mode": False
    }
    # Perhatikan: active_page='setting' agar sidebar menyala
    return render_template('setting.html', active_page='setting', settings=app_settings)

if __name__ == '__main__':
    app.run(debug=True)