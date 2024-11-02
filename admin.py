from sqlalchemy import MetaData
from database import Session, engine
from flask import request, jsonify
from app.models import User, base, UserType, Authentication, Vehicle
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from scripts.hash import hash_password, verify_password
from scripts.token import generate_token
import datetime
import re


def create_admin():
    session = Session()
    body = request.json
    try:
        # Basic validation for required fields
        required_fields = ['fname', 'lname', 'email', 'contact_no', 'age', 'gender', 'nic', 'username', 'password']
        if not all(field in body for field in required_fields):
            return jsonify({"message": "Missing required fields."}), 400

        # Email format validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", body['email']):
            return jsonify({"message": "Invalid input - Email format is incorrect."}), 400

        # Password hashing
        password_hash = hash_password(body['password'])

        new_user = User(
            fname=body['fname'],
            lname=body['lname'],
            email=body['email'],
            phone=body['contact_no'],
            age=body['age'],
            gender=body['gender'],
            nic=body['nic'],
            username=body['username'],
            password_hash=password_hash,
        )
        session.add(new_user)
        session.flush()

        new_user_type = UserType(
            user_id=new_user.id, 
            user_type='admin'
        )
        session.add(new_user_type)
        session.commit()

        return jsonify({"message": "Admin created successfully.", "ok":"true"}), 200
    except IntegrityError as e:
        session.rollback()
        if "email" in str(e.orig):
            return jsonify({"message": "Conflict - Email already exists."}), 409
        elif "username" in str(e.orig):
            return jsonify({"message": "Conflict - Username already exists."}), 409
        else:
            return jsonify({"message": "Conflict - Duplicate entry."}), 409
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()

def login_admin():
    # Parse the JSON from the request body
    data = request.json

    # Extract username and password from the parsed JSON
    username = data.get('username')
    password = data.get('password')

    # Start the session to interact with the database
    session = Session()

    try:
        # Get the user from the database
        user = session.query(User).filter(User.username == username).first()

        if user is None:
            # User not found
            return jsonify({"message": "User not found"}), 404

        # Verify the password
        if not verify_password(password, user.password_hash):
            # Password is incorrect
            return jsonify({"message": "Incorrect username or password"}), 401

        # If we reach here, the user is found and the password is correct
        # Generate a token for the user
        secret_key = 'kavindu123'  # Use an environment variable or secure storage for this in production
        token = generate_token(user.id, secret_key)

        # Check if an authentication record already exists for the user
        existing_auth = session.query(Authentication).filter(Authentication.user_id == user.id).first()

        if existing_auth:
            # Update the existing token and last used timestamp
            existing_auth.token = token
            existing_auth.last_used_at = datetime.datetime.utcnow()
            existing_auth.is_active = True  # Reactivate the token if it was deactivated
        else:
            # If no existing token, create a new authentication record
            new_auth = Authentication(user_id=user.id, token=token, token_type='access')
            session.add(new_auth)

        session.commit()
        return jsonify({"token": token,"message": "Login Sucesfull"}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"message": "Database error", "error": str(e)}), 500
    finally:
        session.close()

def clear_db():
    session = Session() # Start a session to interact with the database
    metadata = MetaData() # Create a metadata object to hold the tables
    metadata.reflect(bind=engine)  # Reflect the tables from the database
    
    ''' Iterate over tables and clear them, skipping "alembic_version" because it's 
    not a table we created and it contains the migration history '''
    # We need to clear the tables in reverse order to avoid foreign key constraints
    # metadata.sorted_tables is a list of the tables in the database, sorted by their foreign key dependencies
    for table in reversed(metadata.sorted_tables):
        if table.name != "alembic_version":
            print(f'Clearing table {table.name}')
            session.execute(table.delete())
    session.commit()

    session.close()

def drop_db():
    metadata = MetaData() # Create a metadata object to hold the tables
    metadata.reflect(bind=engine) # Reflect the tables from the database
    metadata.drop_all(engine) # Drop all the tables in the database

def clear_table(body):
    # Extract table name from the request body
    # print(body)
    table_name = body.get('table_name')
    print(f'Clearing table {table_name}')

    # Return a 400 Bad Request response if table_name is not provided
    if not table_name:
        return jsonify({'message': 'Invalid request or table name supplied.'}), 400

    session = Session()
    metadata = MetaData()
    metadata.reflect(bind=engine)

    if table_name in metadata.tables and table_name != "alembic_version":
        table = metadata.tables[table_name]
        try:
            session.execute(table.delete())
            session.commit()
            return jsonify({'message': f'Table {table_name} cleared successfully.'}), 200
        except Exception as e:
            session.rollback()  # Rollback the session in case of exception
            # Log the exception e if necessary
            return jsonify({'message': f'Error clearing table {table_name}.', 'error': str(e)}), 500
        finally: 
            session.close()

def get_pending_vehicles():
    session = Session()

    try:
        # Use SQLAlchemy select to query all Rides objects
        get_all_vehicles = session.query(Vehicle).all()

        print(get_all_vehicles)

        # Convert each Ride object to a dictionary
        pending_vehicle_list = []

        for vehicle in get_all_vehicles:
            if vehicle.verify == 2:
                pending_vehicle_dict = {
                    'id': vehicle.id,
                    'vehicleNo': vehicle.Vehicleno,
                    'brand': vehicle.brand,
                    'model': vehicle.model,
                    'type': vehicle.type,
                    'length': vehicle.length,
                    'width': vehicle.width,
                    'height': vehicle.height,
                    'tonnage': vehicle.tonnage,
                }
                pending_vehicle_list.append(pending_vehicle_dict)

        # Return the list of dictionaries
        return pending_vehicle_list
    
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching all ride. {e}"), 500
        return {}

    finally:
        session.close()

def confirm_vehicle(vehicle_id=None):

    session = Session()

    try:
        print(vehicle_id)
        confirmed_vehicle = session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

        # Check if the ride exists
        if confirmed_vehicle:
            # Update the cf confirmation
            confirmed_vehicle.verify = 1
            session.commit()
            return jsonify({"message": "Vehicle confirmation successfully", "ok":True}), 200
        else:
            # Handle case where the ride does not exist
            print(f"vehicle with id {vehicle_id} does not exist.")
            return {'message': f"vehicle with id {vehicle_id} does not exist."}, 404
                
    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        session.close() 

def reject_vehicle(vehicle_id=None):

    session = Session()

    try:
        print(vehicle_id)
        rejected_vehicle = session.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

        # Check if the ride exists
        if rejected_vehicle:
            # Update the cf confirmation
            rejected_vehicle.verify = 0
            session.commit()
            return jsonify({"message": "Vehicle confirmation successfully", "ok":True}), 200
        else:
            # Handle case where the ride does not exist
            print(f"vehicle with id {vehicle_id} does not exist.")
            return {'message': f"vehicle with id {vehicle_id} does not exist."}, 404
                
    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        session.close() 