# --- KODUN BAŞLANGICI ---

import json
import os
import uuid
from typing import List, Dict, Any
from functools import wraps 
from flask import Flask, render_template, request, redirect, url_for, flash, session as flask_session

# YENİ KÜTÜPHANE: Vercel KV veritabanı için eklendi (HARF HATASI DÜZELTİLDİ)
from vercel_kv import KV

app = Flask(__name__)
app.secret_key = os.environ.get("ATTENDANCE_APP_SECRET", "dev-secret-key")

TEACHER_PASSWORD = "12345" 

# YENİ BAĞLANTI: Veritabanına bağlanıyoruz (HARF HATASI DÜZELTİLDİ)
kv_store = KV()

# YENİ FONKSİYON: Artık veriyi /tmp'den değil, Vercel KV'den okuyoruz
def load_sessions() -> List[Dict[str, Any]]:
    # 'sessions_data' anahtarı altındaki tüm veriyi çek
    data = kv_store.get('sessions_data')
    if data is None:
        # Eğer veritabanı boşsa (ilk çalıştırma), boş liste döndür
        return []
    return data

# YENİ FONKSİYON: Artık veriyi /tmp'ye değil, Vercel KV'ye yazıyoruz
def save_sessions(sessions: List[Dict[str, Any]]):
    # Tüm oturum listesini 'sessions_data' anahtarı altına kaydet
    kv_store.set('sessions_data', sessions)


# --- GERİ KALAN TÜM KODLAR AYNI ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "teacher_logged_in" not in flask_session:
            flash("Bu sayfayı görmek için giriş yapmalısınız.", "error")
            return redirect(url_for("teacher_login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return redirect(url_for("student_login"))

@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == TEACHER_PASSWORD:
            flask_session["teacher_logged_in"] = True
            flash("Başarıyla giriş yaptınız.", "success")
            return redirect(url_for("teacher_panel"))
        else:
            flash("Hatalı şifre.", "error")
            return redirect(url_for("teacher_login"))
    return render_template("teacher_login.html")

@app.route("/teacher/logout")
def teacher_logout():
    flask_session.pop("teacher_logged_in", None)
    flash("Başarıyla çıkış yaptınız.", "info")
    return redirect(url_for("teacher_login"))

@app.route("/teacher")
@login_required 
def teacher_panel():
    sessions = load_sessions()
    return render_template("teacher.html", sessions=sessions, weeks=list(range(1, 15)))

@app.route("/teacher/create", methods=["POST"])
@login_required
def create_session():
    session_name = request.form.get("session_name", "").strip()
    student_list_raw = request.form.get("student_list", "").strip()

    if not session_name:
        flash("Oturum adı gereklidir.", "error")
        return redirect(url_for("teacher_panel"))

    if not student_list_raw:
        flash("Öğrenci listesi gereklidir.", "error")
        return redirect(url_for("teacher_panel"))

    students: List[Dict[str, Any]] = []
    invalid_lines = []

    for index, line in enumerate(student_list_raw.splitlines(), start=1):
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split(",")]
        parts = [part for part in parts if part]
        if len(parts) < 2:
            invalid_lines.append(index)
            continue
        number, name = parts[0], parts[1]
        department = parts[2] if len(parts) > 2 else ""
        students.append(
            {
                "number": number,
                "name": name,
                "department": department,
                "attendance": [False] * 14,
            }
        )

    if invalid_lines:
        line_text = ", ".join(str(line) for line in invalid_lines)
        flash(
            f"Öğrenci listesi satırlarında format hatası var (satırlar: {line_text}). 'Öğrenci Numarası, Adı Soyadı' biçimini kullanın.",
            "error",
        )
        return redirect(url_for("teacher_panel"))

    if not students:
        flash("Geçerli öğrenci bulunamadı.", "error")
        return redirect(url_for("teacher_panel"))

    sessions = load_sessions()
    new_session = {
        "id": str(uuid.uuid4()),
        "name": session_name,
        "active_week": None,
        "students": students,
    }
    sessions.append(new_session)
    save_sessions(sessions)

    flash("Oturum başarıyla oluşturuldu.", "success")
    return redirect(url_for("teacher_panel"))

@app.route("/teacher/<session_id>/week", methods=["POST"])
@login_required
def update_active_week(session_id: str):
    week_value = request.form.get("active_week")
    sessions = load_sessions()

    for session_data in sessions:
        if session_data["id"] == session_id:
            if week_value:
                try:
                    week_number = int(week_value)
                    if week_number < 1 or week_number > 14:
                        raise ValueError
                    session_data["active_week"] = week_number
                except ValueError:
                    flash("Hafta değeri 1-14 arasında olmalıdır.", "error")
                    save_sessions(sessions)
                    return redirect(url_for("teacher_panel"))
            else:
                session_data["active_week"] = None
            break

    save_sessions(sessions)
    flash("Aktif hafta güncellendi.", "success")
    return redirect(url_for("teacher_panel"))


@app.route("/teacher/delete/<session_id>", methods=["POST"])
@login_required
def delete_session(session_id: str):
    sessions = load_sessions()
    sessions_to_keep = [session for session in sessions if session["id"] != session_id]
    
    if len(sessions) == len(sessions_to_keep):
        flash("Silinecek oturum bulunamadı.", "error")
    else:
        save_sessions(sessions_to_keep)
        flash("Oturum başarıyla silindi.", "success")
        
    return redirect(url_for("teacher_panel"))

@app.route("/student", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        student_number = request.form.get("student_number", "").strip()
        if not student_number:
            flash("Öğrenci numarası gereklidir.", "error")
            return redirect(url_for("student_login"))

        flask_session["student_number"] = student_number
        flash("Giriş başarılı.", "success")
        return redirect(url_for("student_sessions"))

    return render_template("student_login.html")


@app.route("/student/sessions", methods=["GET"])
def student_sessions():
    student_number = flask_session.get("student_number")
    if not student_number:
        flash("Lütfen önce giriş yapın.", "error")
        return redirect(url_for("student_login"))

    sessions = [session for session in load_sessions() if session.get("active_week")]
    return render_template("student_sessions.html", sessions=sessions, student_number=student_number)


@app.route("/student/sessions/<session_id>/attend", methods=["POST"])
def attend_session(session_id: str):
    student_number = flask_session.get("student_number")
    if not student_number:
        flash("Giriş yapılmadı.", "error")
        return redirect(url_for("student_login"))

    sessions = load_sessions()
    target_session = next((session for session in sessions if session["id"] == session_id), None)

    if not target_session:
        flash("Oturum bulunamadı.", "error")
        return redirect(url_for("student_sessions"))

    active_week = target_session.get("active_week")
    if not active_week:
        flash("Bu oturum için aktif hafta ayarlanmamış.", "error")
        return redirect(url_for("student_sessions"))

    student_entry = next((student for student in target_session["students"] if student["number"] == student_number), None)
    if not student_entry:
        flash("Öğrenci listede bulunamadı.", "error")
        return redirect(url_for("student_sessions"))

    week_index = active_week - 1
    student_entry["attendance"][week_index] = True
    save_sessions(sessions)

    flash("Yoklama işleminiz alındı.", "success")
    return redirect(url_for("student_sessions"))


@app.context_processor
def inject_enumerate():
    return {"enumerate": enumerate}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

# --- KODUN SONU ---
