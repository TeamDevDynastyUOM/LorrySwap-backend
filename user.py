from app.models import User,UserType,TempUser,Authentication
from scripts.hash import hash_password, verify_password
from database import Session 
from sqlalchemy import select 
from flask import request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from scripts.token import generate_token
import datetime
import re
import os
import smtplib
import random


def generate_otp():
    return random.randint(100000, 999999)

def send_otp(email, otp):
    from_email = "devdynasty365@gmail.com"
    from_password = "cacj pbfm awfk aozt"
    to_email = email
    subject = "Your OTP Code for LorrySwap"
    body = f"Your OTP code is {otp}."

    message = f"Subject: {subject}\n\n{body}"

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, message)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False



def create_user():
    print("Creating user with body: ", request.json)
    body = request.json
    session = Session()

    try:
        required_fields = ['roles', 'fname', 'lname', 'email', 'contact_no', 'age', 'gender', 'nic', 'username', 'password']
        if not all(field in body for field in required_fields):
            return jsonify({"message": "Missing required fields."}), 400

        if not re.match(r"[^@]+@[^@]+\.[^@]+", body['email']):
            return jsonify({"message": "Invalid input - Email format is incorrect."}), 400

        otp = generate_otp()
        temp_user = TempUser(
            email=body['email'],
            otp=otp,
            fname=body['fname'],
            lname=body['lname'],
            contact_no=body['contact_no'],
            age=body['age'],
            gender=body['gender'],
            nic=body['nic'],
            username=body['username'],
            password=body['password'],
            roles=str(body['roles']),
        )
        session.add(temp_user)
        session.commit()

        if not send_otp(body['email'], otp):
            return jsonify({"message": "Failed to send OTP. Please try again later."}), 500

        return jsonify({"message": "OTP sent to your email. Please verify to complete registration."}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()

def verify_otp():
    body = request.json

    email = body.get('email')
    otp = body.get('otp')

    if not email or not otp:
        return jsonify({"message": "Email and OTP are required."}), 400

    session = Session()
    try:
        temp_user = session.query(TempUser).filter_by(email=email).first()

        if not temp_user:
            return jsonify({"message": "OTP expired or invalid."}), 400

        expiration_time = temp_user.timestamp + datetime.timedelta(minutes=5)
        if datetime.datetime.now() > expiration_time:
            session.delete(temp_user)
            session.commit()
            return jsonify({"message": "OTP expired or invalid."}), 400

        if temp_user.otp != int(otp):
            return jsonify({"message": "Invalid OTP."}), 400

        # OTP is valid, proceed with user registration
        password_hash = hash_password(temp_user.password)

        new_user = User(
            fname=temp_user.fname,
            lname=temp_user.lname,
            email=temp_user.email,
            phone=temp_user.contact_no,
            age=temp_user.age,
            gender=temp_user.gender,
            nic=temp_user.nic,
            username=temp_user.username,
            password_hash=password_hash,
        )
        session.add(new_user)
        session.flush()

        roles = eval(temp_user.roles)  # Convert roles from string to list
        for role in roles:
            new_user_type = UserType(
                user_id=new_user.id,
                user_type=role
            )
            session.add(new_user_type)

        session.commit()
        session.delete(temp_user)
        session.commit()

        return jsonify({"message": "User created successfully."}), 200
    except IntegrityError as e:
        print(e)
        session.rollback()
        if "email" in str(e.orig):
            return jsonify({"message": "Conflict - Email already exists."}), 409
        elif "username" in str(e.orig):
            return jsonify({"message": "Conflict - Username already exists."}), 409
        else:
            return jsonify({"message": "Conflict - Duplicate entry."}), 409
    except Exception as e:
        print(e)
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()



def login_user():
    data = request.json

    username = data.get('username')
    password = data.get('password')

    session = Session()

    try:
        user = session.query(User).filter(User.username == username).first()

        if user is None:
            return jsonify({"message": "User not found"}), 404

        if not verify_password(password, user.password_hash):
            return jsonify({"message": "Incorrect username or password"}), 401

        # Retrieve user roles
        user_roles = session.query(UserType).filter(UserType.user_id == user.id).all()
        roles = [role.user_type for role in user_roles]

        secret_key = 'jHF4r3$4Df34@#LorrySwaP#@LkL0&$fKJd'  # Use an environment variable or secure storage for this in production
        token = generate_token(user.id, roles, secret_key)

        existing_auth = session.query(Authentication).filter(Authentication.user_id == user.id).first()

        if existing_auth:
            existing_auth.token = token
            existing_auth.last_used_at = datetime.datetime.utcnow()
            existing_auth.is_active = True
        else:
            new_auth = Authentication(user_id=user.id, token=token, token_type='access')
            session.add(new_auth)

        session.commit()
        return jsonify({"token": token, "message": "Login Successful"}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"message": "Database error", "error": str(e)}), 500
    finally:
        session.close()



def forgot_password():
    body = request.json
    email = body.get('email')

    if not email:
        return jsonify({"message": "Email is required."}), 400

    session = Session()
    try:
        user = session.query(User).filter_by(email=email).first()

        if not user:
            return jsonify({"message": "User with this email does not exist."}), 404

        otp = generate_otp()
        temp_user = TempUser(
            email=email,
            otp=otp,
            fname=user.fname,
            lname=user.lname,
            contact_no=user.phone,
            age=user.age,
            gender=user.gender,
            nic=user.nic,
            username=user.username,
            password='',  # Setting a default value to avoid NULL
            roles=''      # Setting a default value to avoid NULL
        )
        session.add(temp_user)
        session.commit()

        if not send_otp(email, otp):
            return jsonify({"message": "Failed to send OTP. Please try again later."}), 500

        return jsonify({"message": "OTP sent to your email. Please verify to reset your password."}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()



def reset_password():
    body = request.json
    email = body.get('email')
    otp = body.get('otp')
    new_password = body.get('new_password')

    if not email or not otp or not new_password:
        return jsonify({"message": "Email, OTP, and new password are required."}), 400

    session = Session()
    try:
        temp_user = session.query(TempUser).filter_by(email=email).first()

        if not temp_user:
            return jsonify({"message": "OTP expired or invalid."}), 400

        expiration_time = temp_user.timestamp + datetime.timedelta(minutes=5)
        if datetime.datetime.now() > expiration_time:
            session.delete(temp_user)
            session.commit()
            return jsonify({"message": "OTP expired or invalid."}), 400

        if temp_user.otp != int(otp):
            return jsonify({"message": "Invalid OTP."}), 400

        # OTP is valid, proceed with password reset
        user = session.query(User).filter_by(email=email).first()

        if not user:
            return jsonify({"message": "User not found."}), 404

        user.password_hash = hash_password(new_password)
        session.delete(temp_user)
        session.commit()

        return jsonify({"message": "Password reset successfully."}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()
