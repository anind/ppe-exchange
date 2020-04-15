from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug import secure_filename
from app import app, db
from app.forms import LoginForm, RegistrationForm, VerifyForm, AdminAuthorizationForm
from app.models import User, PPE, Hospital, Wants, Has, Exchanges, Exchange, EXCHANGE_COMPLETE, EXCHANGE_COMPLETE_TEXT, EXCHANGE_COMPLETE_ADMIN, EXCHANGE_COMPLETE_ADMIN_TEXT, EXCHANGE_COMPLETE_HOSPITAL_CANCELED, EXCHANGE_COMPLETE_HOSPITAL_CANCELED_TEXT, EXCHANGE_COMPLETE_ADMIN_CANCELED, EXCHANGE_COMPLETE_ADMIN_CANCELED_TEXT, EXCHANGE_UNVERIFIED, EXCHANGE_UNVERIFIED_TEXT, EXCHANGE_IN_PROGRESS, EXCHANGE_IN_PROGRESS_TEXT, EXCHANGE_NOT_ACCEPTED, EXCHANGE_ACCEPTED_NOT_SHIPPED, EXCHANGE_ACCEPTED_SHIPPED, EXCHANGE_ACCEPTED_RECEIVED, EXCHANGE_HOSPITAL_CANCELED, EXCHANGE_ADMIN_CANCELED
from app import crypto
from app import email
from datetime import datetime

import json
import os

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = User.query.filter_by(username=current_user.username).first()
    if user.is_admin:
        return render_template('admin_index.html', title='Home')
    elif not user.is_verified:
        return render_template("404.html")
    else:
        user = User.query.filter_by(username=current_user.username).first()
        user_hospital = Hospital.query.filter_by(id=user.hospital_id).first()
        
        hospital = {
            "hospital_name": user_hospital.name
        }
        return render_template('index.html', title='Home', hospital=hospital)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    form.hospital_name.choices = [(h.id, h.name) for h in Hospital.query.all()]
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    is_admin=False,
                    is_verified=False,
                    hospital_address=form.address.data,
                    hospital_contact=form.contact.data,
                    hospital_id=form.hospital_name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if not current_user.is_authenticated:
        return redirect(url_for('login',next='/verify?key='+request.args.get("key")))

    user = User.query.filter_by(username=current_user.username).first()
    if request.args.get("key") == user.verification_key:
        form = VerifyForm()
        if form.validate_on_submit():
            # Mark user as verified
            q = db.session.query(User)
            q = q.filter(User.id == user.id)
            record = q.first()
            record.is_verified = True
            record.verification_key = None
            db.session.commit()

            flash('Congratulations, you are now a verified user!')
            return redirect(url_for('index'))
        return render_template('verify.html', title='Verify', form=form)
    elif user.is_verified:
        return redirect(url_for("index"))
    else:
        return render_template('404.html')
@app.route('/wants', methods=['GET', 'POST'])
def wants():
    if not current_user.is_authenticated:
        return redirect(url_for('login',next='/wants'))
    
    user = User.query.filter_by(username=current_user.username).first()
    if not user.is_verified:
        return render_template("404.html")
    
    user = User.query.filter_by(username=current_user.username).first()
    user_hospital = Hospital.query.filter_by(id=user.hospital_id).first()
    
    skus = PPE.query.all()
    items = []
    for item in skus:
        count = 0
        try:
            count = Wants.query.filter_by(hospital_id=user_hospital.id, ppe_id=item.id).first().count
        except:
            count = 0
        items.append({
            "sku": item.sku,
            "desc": item.desc,
            "img": item.img.decode(),
            "count": count
        })

    hospital = {
        "hospital_name": user_hospital.name
    }
    return render_template('item_base.html', title='Wants', hospital=hospital, state="Wants", items=items)

@app.route('/has', methods=['GET', 'POST'])
def has():
    if not current_user.is_authenticated:
        return redirect(url_for('login',next='/has'))
    
    user = User.query.filter_by(username=current_user.username).first()
    if not user.is_verified:
        return render_template("404.html")
    
    user = User.query.filter_by(username=current_user.username).first()
    user_hospital = Hospital.query.filter_by(id=user.hospital_id).first()
    
    skus = PPE.query.all()
    items = []
    for item in skus:
        count = 0
        try:
            count = Has.query.filter_by(hospital_id=user_hospital.id, ppe_id=item.id).first().count
        except:
            count = 0
        items.append({
            "sku": item.sku,
            "desc": item.desc,
            "img": item.img.decode(),
            "count": count
        })

    hospital = {
        "hospital_name": user_hospital.name
    }
    return render_template('item_base.html', title='Have', hospital=hospital, state="Has", items=items)

@app.route('/update_want_need', methods=['GET', 'POST'])
def update_want_need():
    data = json.loads(request.get_data())
    if not current_user.is_authenticated:
        return jsonify(target="login?next="+data['state'])
    
    user = User.query.filter_by(username=current_user.username).first()
    user_hospital = Hospital.query.filter_by(id=user.hospital_id).first()

    if data["state"] == "wants":
        q = db.session.query(Wants)
        for item in data["items"]:
            ppe_id = PPE.query.filter_by(sku=item["sku"]).first().id

            old_count = 0
            count_query = Wants.query.filter_by(hospital_id=user_hospital.id, ppe_id=ppe_id).first()
            if count_query:
                old_count = count_query.count
            
            if old_count > 0 and item["count"] > 0:
                f = q.filter(Wants.ppe_id == ppe_id)
                record = f.first()
                record.count = item["count"]
            elif old_count > 0 and item["count"] == 0:
                Wants.query.filter_by(hospital_id=user_hospital.id, ppe_id=ppe_id).delete()
            elif old_count == 0 and item["count"] > 0:
                w = Wants(hospital_id=user_hospital.id, ppe_id=ppe_id, count=item["count"])
                db.session.add(w)
        db.session.commit()
    elif data["state"] == "has":
        q = db.session.query(Has)
        for item in data["items"]:
            ppe_id = PPE.query.filter_by(sku=item["sku"]).first().id

            old_count = 0
            count_query = Has.query.filter_by(hospital_id=user_hospital.id, ppe_id=ppe_id).first()
            if count_query:
                old_count = count_query.count
            
            if old_count > 0 and item["count"] > 0:
                f = q.filter(Has.ppe_id == ppe_id)
                record = f.first()
                record.count = item["count"]
            elif old_count > 0 and item["count"] == 0:
                Has.query.filter_by(hospital_id=user_hospital.id, ppe_id=ppe_id).delete()
            elif old_count == 0 and item["count"] > 0:
                h = Has(hospital_id=user_hospital.id, ppe_id=ppe_id, count=item["count"])
                db.session.add(h)
        db.session.commit()
    return jsonify(target=data['state'])

@app.route('/admin_sku', methods=['GET', 'POST'])
def admin_sku():
    if not current_user.is_authenticated:
        return redirect(url_for('login',next='/admin_sku'))

    skus = PPE.query.all()
    items = []
    for item in skus:
        items.append({
            "sku": item.sku,
            "desc": item.desc,
            "img": item.img.decode()
        })
    return render_template('admin_sku.html', title='Have', items=items)

@app.route('/update_admin_sku', methods=['GET', 'POST'])
def update_admin_sku():
    data = json.loads(request.get_data())
    if not current_user.is_authenticated:
        return jsonify(target="login?next="+data['state'])
    if data["task"] == "add":
        q = PPE.query.filter_by(sku = data["sku"])
        if q.count() > 0:
            return "SKU already exists"
        else:
            p = PPE(sku=data["sku"], desc=data["desc"], img=str.encode(data["img"]))
            db.session.add(p)
            db.session.commit()
    elif data["task"] == "remove":
        PPE.query.filter_by(sku=data["sku"]).delete()
        db.session.commit()
    elif data["task"] == "edit":
        q = db.session.query(PPE)
        q = q.filter(PPE.sku == data["sku"])
        record = q.first()
        record.desc = data["desc"]
        record.img = str.encode(data["img"])
        db.session.commit()
    return jsonify(target="index")

@app.route('/admin_auth', methods=['GET', 'POST'])
def admin_auth():
    auth_key = {}
    with open('auth_key.txt') as json_file:
        auth_key = json.load(json_file)
    if request.args.get("key") == auth_key["key"]:
        form  = AdminAuthorizationForm()
        if form.validate_on_submit():
            user = User(username="admin", email=auth_key["admin_email"], is_admin=True, is_verified=True)
            user.set_password(form.password.data)
            User.query.filter_by(username="admin").delete()
            db.session.add(user)
            db.session.commit()
            os.remove("auth_key.txt")
            flash('Congratulations, you are now a registered administrator!')
            return redirect(url_for('login'))
        return render_template('admin_auth.html', title='Admin Setup', form=form)
    else:
        return render_template('404.html')

@app.route('/admin_users', methods=['GET', 'POST'])
def admin_users():
    if not current_user.is_authenticated:
        return redirect(url_for('login',next='/admin_users'))
    
    users = User.query.all()
    items = []
    for user in users:
        user_hospital = Hospital.query.filter_by(id=user.hospital_id).first()
        item = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "hospital": "N/A",
            "contact": "N/A",
            "address": "N/A",
            "is_verified": user.is_verified,
            "verification_pending": user.verification_key is not None,
            "is_admin": user.is_admin
        }
        if user_hospital is not None:
            item["hospital"] = user_hospital.name
            item["contact"] = user.hospital_contact
            item["address"] = user.hospital_address
        items.append(item)
    return render_template('admin_users.html', title='Users Dashboard', users=items)


@app.route('/update_admin_users', methods=['GET', 'POST'])
def update_admin_users():
    data = json.loads(request.get_data())
    if not current_user.is_authenticated:
        return jsonify(target="login?next="+data['state'])
    if data["task"] == "remove":
        q = db.session.query(User)
        q = q.filter(User.id == data["user_id"])
        record = q.first()
        record.is_verified = False
        record.verification_key = None

        db.session.commit()
    elif data["task"] == "verify":
        # Set user as generate verification key for user
        q = db.session.query(User)
        q = q.filter(User.id == data["user_id"])
        record = q.first()
        record.is_verified = False
        key = crypto.generate_key()
        record.verification_key = key

        # Update hospitals database
        user = User.query.filter_by(id=data["user_id"]).first()
        q = db.session.query(Hospital)
        q = q.filter(Hospital.id == user.hospital_id)
        record = q.first()
        record.address = user.hospital_address
        record.contact = user.hospital_contact
        
        db.session.commit()

        email.send_user_verification(
            User.query.filter_by(id=data["user_id"]).first().username,
            key,
            "localhost:5000",
            "kaviasher@gmail.com")#'''User.query.filter_by(id=data["user_id"]).first().email''' )
        
    elif data["task"] == "cancel":
        q = db.session.query(User)
        q = q.filter(User.id == data["user_id"])
        record = q.first()
        record.is_verified = False
        record.verification_key = None
        db.session.commit()
    return jsonify(target="index")


@app.route('/admin_hospitals', methods=['GET', 'POST'])
def admin_hospitals():
    if not current_user.is_authenticated:
        return redirect(url_for('login',next='/admin_hospitals'))

    hospitals = Hospital.query.all()
    items = []
    for item in hospitals:
        items.append({
            "id": item.id,
            "name": item.name,
            "address": item.address
        })
    return render_template('admin_hospitals.html', items=items)

@app.route('/update_admin_hospital', methods=['GET', 'POST'])
def update_admin_hospital():
    data = json.loads(request.get_data())
    if not current_user.is_authenticated:
        return jsonify(target="login?next=admin_hospital")
    if data["task"] == "add":
        q = Hospital.query.filter_by(name = data["name"])
        if q.count() > 0:
            return "Hospital already exists"
        else:
            h = Hospital(name=data["name"], address=data["address"])
            db.session.add(h)
            db.session.commit()
    elif data["task"] == "remove":
        Hospital.query.filter_by(id=data["id"]).delete()
        db.session.commit()
    elif data["task"] == "edit":
        q = db.session.query(Hospital)
        q = q.filter(Hospital.id == data["id"])
        record = q.first()
        record.name = data["name"]
        record.address = data["address"]
        db.session.commit()
    return jsonify(target="index")

@app.route('/admin_exchange', methods=['GET', 'POST'])
def admin_exchange():
    if not current_user.is_authenticated:
        return redirect(url_for('login',next='/admin_exchange'))
    
    exchanges = Exchanges.query.all()
    items = []
    for ex in exchanges:
        its = []
        exchange = Exchange.query.filter_by(exchange_id=ex.id)
        
        stat = ""
        if ex.status==EXCHANGE_COMPLETE:
            stat=EXCHANGE_COMPLETE_TEXT
        elif ex.status==EXCHANGE_COMPLETE_ADMIN:
            stat=EXCHANGE_COMPLETE_ADMIN_TEXT
        elif ex.status==EXCHANGE_COMPLETE_HOSPITAL_CANCELED:
            stat=EXCHANGE_COMPLETE_HOSPITAL_CANCELED_TEXT
        elif ex.status==EXCHANGE_COMPLETE_ADMIN_CANCELED:
            stat=EXCHANGE_COMPLETE_ADMIN_CANCELED_TEXT
        elif ex.status==EXCHANGE_IN_PROGRESS:
            stat=EXCHANGE_IN_PROGRESS_TEXT
        elif ex.status==EXCHANGE_UNVERIFIED:
            stat=EXCHANGE_UNVERIFIED_TEXT

        for x in exchange:
            i = {
                "h1": Hospital.query.filter_by(id = x.hospital1).first().name,
                "h2": Hospital.query.filter_by(id = x.hospital2).first().name,
                "ppe": PPE.query.filter_by(id = x.ppe).first().sku,
                "count": x.count
            }
            its.append(i)
        item = {
            "id": ex.id,
            "created_timestamp": ex.created_timestamp,
            "updated_timestamp": ex.updated_timestamp,
            "exchanges": its,
            "status": ex.status,
            "status_text": stat
        }
        items.append(item)
    return render_template('admin_exchange.html', title='Exchanges Dashboard', exchanges=items)

@app.route('/update_admin_exchanges', methods=['GET', 'POST'])
def update_admin_exchanges():
    data = json.loads(request.get_data())
    print (data)
    if not current_user.is_authenticated:
        return jsonify(target="login?next="+data['state'])
    if data["task"] == "cancel":
        q = db.session.query(Exchanges)
        q = q.filter(Exchanges.id == data["exchange_id"])
        record = q.first()
        record.status = EXCHANGE_COMPLETE_ADMIN_CANCELED
        record.updated_timestamp = datetime.now()
        exchange = Exchange.query.filter_by(exchange_id=data["exchange_id"])
        for x in exchange:
            x.status=EXCHANGE_ADMIN_CANCELED
        db.session.commit()
    return jsonify(target="index")

@app.route('/exchanges', methods=['GET', 'POST'])
def exchanges():
#    if not current_user.is_authenticated:
#        return redirect(url_for('login',next='/exchanges'))

#    user_id = User.query.filter_by(username=current_user.username).first().id
 #   hospital_id = Hospital.query.filter_by(user_id=user_id).first().id
    hospital_id = 1
    
    exchanges = Exchanges.query.all()
    items = []
    for ex in exchanges:
        exchange = Exchanges.query.filter_by(ex.id)
        good = False
        its = []
 
        for x in exchange:
            if x.hospital1==hospital_id:
                good = True
            elif x.hospital2==hospital_id:
                good = True
        if good:
            for x in exchange:
                i = {
                    "h1_name": Hospital.query.filter_by(id = x.hospital1).first().name,
                    "h1": x.hospital1,
                    "h2_name": Hospital.query.filter_by(id = x.hospital2).first().name,
                    "h2": x.hospital2,
                    "ppe": PPE.query.filter_by(id = x.ppe).first().sku,
                    "count": x.count
                }
                its.append(i)
        exchange = Exchange.query.filter_by(hospital1=ex.id) 
        for x in exchange:
            items.append({
                "exchange_sid": ex.id,
                "exchange_created": ex.created_timestamp,
                "exchange_updated": ex.updated_timestamp,
                "exchanges": its,
            })
        
    hospital = {
        "hospital_name": Hospital.query.filter_by(id=hospital_id).first().name,
        "hospital_id":hospital_id
    }
    return render_template('exchanges.html', title='Exchanges', hospital=hospital, state="Exchange", exchanges=items)

# exchanges logic
# loop through exchanges
#   find ones that have this user's hospital id somewhere in the linked exchange --> grab whole "exchanges"
#   exchange id --> exchanges.id
#   when created --> exchanges.creation_timestamp
#   when updated --> exchanges.updated_timestamp
#   loop through exchanges
#     print out exchange
#     print out status
#     depending on status, show optional button

# Exchange ID   when created    when updated    exchange part 1     status part 1: optional button (verify/shipped/received)
#                                               exchange part 2     status part 2: optional button
#                                               ...                 ...