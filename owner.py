from app.models import User, Driver,Vehicle, base, UserType, Authentication
from scripts.hash import hash_password, verify_password
from database import Session 
from sqlalchemy import select, func
from flask import request, jsonify
from scripts.upload_to_gdrive import upload_licene_image
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from scripts.token import generate_token
# from auth import auth_token_required
from scripts.optimal_path import get_distances, create_graph, find_shortest_path, generate_google_maps_url
import datetime
import re
import os


# @auth_token_required(roles_required=['Owner'])
def get_all_drivers():
    session = Session()
    try:
        query = (
            select(User.id, User.fname, User.lname)
            .select_from(User)
            .join(Driver, User.id == Driver.user_id)
            .filter(Driver.Organization_id == None)
        )

        results = session.execute(query).all()

        drivers = [{"id": id, "first_name": fname, "last_name": lname} for id, fname, lname in results]        

        return jsonify({"Results": drivers}), 200
    except Exception as e:
       
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()



# @auth_token_required(roles_required=['Owner'])
def get_all_vehicles():
    session = Session()

    try:
        # Define the query to select vehicle numbers
        query = session.query(Vehicle.Vehicleno).outerjoin(Driver, Vehicle.Vehicleno == Driver.Vehicleno).filter(Driver.Vehicleno == None)

        # Execute the query and fetch all results
        results = session.execute(query).scalars().all()

        # Prepare the response data
        vehicles = [{"vehicle_number": Vehicleno} for Vehicleno in results]

        print(vehicles)

        # Return the response in JSON format
        return jsonify({"Results": vehicles}), 200
    finally:
        
        session.close()
        


# @auth_token_required(roles_required=['Owner'])
def assign_vehicle_to_driver(userId):
    
    session = Session()
    try:
        # Ensure the request data is JSON
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400

        data = request.get_json()
        new_vehicle_no = data.get('vehicle_no')

        if not new_vehicle_no:
            return jsonify({"error": "Vehicle number is required"}), 400

        # Fetch the driver
        driver = session.query(Driver).filter(Driver.user_id == userId).first()

        if not driver:
            return jsonify({"error": "Driver not found for the given user ID"}), 404

        # Update the driver's vehicle number
        driver.Vehicleno = new_vehicle_no
        session.commit()

        return jsonify({"message": "Vehicle number updated successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        session.close()



# @auth_token_required(roles_required=['Owner'])
def add_vehicle(organizationId):
    session = Session()
    try:
        # owner = session.query(Owner).filter(Owner.user_id == organizationId).first()

        # if not owner:
        #     return jsonify({"error": "Owner not found for the given organization user ID"}), 404

        body = request.get_json()

        # Extract values from the request body
        vehicle_no = body.get("Vehicleno")
        brand = body.get("brand")
        model = body.get("model")
        vehicle_type = body.get("type")
        length = body.get("length")
        width = body.get("width")
        height = body.get("height")
        tonnage = body.get("tonnage")

        # Debugging: Print extracted values
        print(f"Vehicle No: {vehicle_no}, Brand: {brand}, Model: {model}, Type: {vehicle_type}, Length: {length}, Width: {width}, Height: {height}, Tonnage: {tonnage}, Organization ID: {organizationId}")

        # Check if Vehicleno is provided
        if not vehicle_no:
            return jsonify({"error": "Vehicleno is required"}), 400

        new_vehicle = Vehicle(
            Vehicleno=vehicle_no,
            brand=brand,
            model=model,
            type=vehicle_type,
            length=length,
            width=width,
            height=height,
            tonnage=tonnage,
            organization_id=organizationId
        )

        session.add(new_vehicle)
        session.commit()

        return jsonify({"success": "Vehicle added successfully"}), 201

    except Exception as e:
        session.rollback()
        print(e)
        return jsonify({"error": "Failed to add vehicle"}), 500

    finally:
        session.close()



# @auth_token_required(roles_required=['Owner'])
def get_organization_details(organizationId):
    session = Session()
    try:

        # owner = session.query(Owner).filter(Owner.user_id == organizationId).first()

        # if not owner:
        #     return jsonify({"error": "Owner not found for the given organization user ID"}), 404

        query = (
            select(User.id, User.fname, User.lname, User.phone, Driver.Vehicleno)
            .select_from(User)
            .join(Driver, User.id == Driver.user_id)
            .where(Driver.Organization_id == organizationId)
            .where(Driver.Vehicleno.isnot(None))  # Add this line to filter out records with Vehicleno as null
        )

        results = session.execute(query).all()

        drivers = [{"id": id, "first_name": fname, "last_name": lname, "phone": phone, "vehicle_number": Vehicleno} for id,fname, lname, phone, Vehicleno in results]

        return jsonify({"Results": drivers}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()



# @auth_token_required(roles_required=['Owner'])
def edit_vehicle(userId):

    # Ensure session is properly handled
    session = Session()
    try:
        # Ensure the request data is JSON
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400

        data = request.get_json()
        new_vehicle_no = data.get('vehicle_no')

        if not new_vehicle_no:
            return jsonify({"error": "Vehicle number is required"}), 400

        # Fetch the driver
        driver = session.query(Driver).filter(Driver.user_id == userId).first()

        if not driver:
            return jsonify({"error": "Driver not found for the given user ID"}), 404

        # Fetch the new vehicle
        new_vehicle = session.query(Vehicle).filter(Vehicle.Vehicleno == new_vehicle_no).first()

        if not new_vehicle:
            return jsonify({"error": f"Vehicle number '{new_vehicle_no}' not found"}), 404

        # Update the driver's vehicle number
        driver.Vehicleno = new_vehicle_no

        # Commit changes to both Driver and Vehicle tables
        session.commit()

        return jsonify({"message": "Vehicle number updated successfully"}), 200

    except IntegrityError as e:
        session.rollback()
        return jsonify({"error": "Integrity constraint violated"}), 400

    except NoResultFound as e:
        session.rollback()
        return jsonify({"error": "No result found"}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        session.close()



# @auth_token_required(roles_required=['Owner'])
def get_drivers_by_organization(organizationId):

    session = Session()
    try:

        # owner = session.query(Owner).filter(Owner.user_id == organizationId).first()

        # if not owner:
        #     return jsonify({"error": "Owner not found for the given organization user ID"}), 404

        query = (
            select(User.id, User.fname, User.lname, User.phone)
            .select_from(User)
            .join(Driver, User.id == Driver.user_id)
            .filter(Driver.Organization_id == organizationId)
        )

        results = session.execute(query).all()

        drivers = [{"id": id, "first_name": fname, "last_name": lname, "phone_no": phone} for id, fname, lname, phone in results]        

        return jsonify({"Results": drivers}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

def get_vehicles_by_organization(organizationId):

    session = Session()
    try:
        # owner = session.query(Owner).filter(Owner.user_id == organizationId).first()
        # print(owner.id)

        # if not owner:
        #     return jsonify({"error": "Owner not found for the given organization user ID"}), 404

        query = (
            select(Vehicle.id,Vehicle.Vehicleno, Vehicle.brand, Vehicle.type, Vehicle.length, Vehicle.width, Vehicle.height, Vehicle.tonnage)
            .select_from(Vehicle)
            .filter(Vehicle.organization_id == organizationId)
        )

        results = session.execute(query).all()

        drivers = [{"id": id, "Vehicleno": Vehicleno, "brand": brand, "type": type, "length":length, "width":width, "height":height, "tonnage":tonnage} for id, Vehicleno, brand, type, length, width, height,tonnage in results]        

        return jsonify({"Results": drivers}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

def delete_driver(userId):

    session = Session()
    try:
        # Fetch the driver
        driver = session.query(Driver).filter(Driver.user_id == userId).first()

        if not driver:
            return jsonify({"error": "Driver not found for the given user ID"}), 404

        # Update the driver's organization_id and Vehicleno to None
        driver.Organization_id = None
        if driver.Vehicleno is not None:
            driver.Vehicleno = None

        # Commit changes to the Driver table
        session.commit()

        return jsonify({"message": "Driver Delete successfully"}), 200

    except IntegrityError as e:
        session.rollback()
        return jsonify({"error": "Integrity constraint violated"}), 400

    except NoResultFound as e:
        session.rollback()
        return jsonify({"error": "No result found"}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        session.close()

def delete_vehicle(Vehicleno):

    session = Session()
    try:
        # Fetch the vehicle
        vehicle = session.query(Vehicle).filter(Vehicle.Vehicleno == Vehicleno).first()

        if not vehicle:
            return jsonify({"error": "Vehicle not found"}), 404

        # Update drivers where Vehicleno matches
        drivers = session.query(Driver).filter(Driver.Vehicleno == Vehicleno).all()

        for driver in drivers:
            driver.Vehicleno = None

        # Delete the vehicle
        session.delete(vehicle)
        session.commit()

        return jsonify({"message": "Vehicle deleted successfully"}), 200

    except IntegrityError as e:
        session.rollback()
        return jsonify({"error": "Integrity constraint violated"}), 400

    except NoResultFound as e:
        session.rollback()
        return jsonify({"error": "No result found"}), 404

    except Exception as e:
        session.rollback()
        print(e)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        session.close()


def get_driver_by_userId(userId):

    session = Session()
    try:
        query = (
            select(
                User.fname,
                User.lname,
                User.phone,
                User.nic,
                User.age,
                User.gender,
                User.email,
                Driver.residence,
                Driver.Vehicleno,
            )
            .select_from(User)
            .join(Driver, User.id == Driver.user_id)
            .where(User.id == userId)
        )

        result = session.execute(query).first()

        if result:
            driver_details = {
                "first_name": result.fname,
                "last_name": result.lname,
                "phone": result.phone,
                "nic": result.nic,
                "age": result.age,
                "gender": result.gender,
                "email": result.email,
                "residence": result.residence,
                "Vehicleno": result.Vehicleno,
            }
            return jsonify({"Result": driver_details}), 200
        else:
            return jsonify({"error": "Driver not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

def add_driver(userId):
    
    session = Session()
    try:
        # Ensure the request data is JSON
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400

        data = request.get_json()
        organization_id = data.get('organization_id')

        if not organization_id:
            return jsonify({"error": "Organization ID is required"}), 400
        
        owner = session.query(User).filter(User.id == organization_id).first()

        if not owner:
            return jsonify({"error": "Owner not found for the given organization ID"}), 404

        # Fetch the driver
        driver = session.query(Driver).filter(Driver.user_id == userId).first()

        if not driver:
            return jsonify({"error": "Driver not found for the given user ID"}), 404

        # Update the driver's vehicle number and organization ID
        driver.Organization_id = owner.id
        session.commit()

        return jsonify({"message": "driver added successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        session.close()


def get_assign_details(organizationId):
    session = Session()
    try:
        # owner = session.query(Owner).filter(Owner.user_id == organizationId).first()

        # if not owner:
        #     return jsonify({"error": "Owner not found for the given organization user ID"}), 404
        
        # Count of unassigned drivers
        unassigned_drivers_query = (
            select(func.count())
            .select_from(Driver)
            .where(Driver.Organization_id == organizationId)
            .where(Driver.Vehicleno.is_(None))
        )
        unassigned_drivers_count = session.execute(unassigned_drivers_query).scalar()

        # Count of assigned drivers
        assigned_drivers_query = (
            select(func.count())
            .select_from(Driver)
            .where(Driver.Organization_id == organizationId)
            .where(Driver.Vehicleno.isnot(None))
        )
        assigned_drivers_count = session.execute(assigned_drivers_query).scalar()

        # Count of unassigned vehicles
        unassigned_vehicles_query = (
            select(func.count())
            .select_from(Vehicle)
            .where(Vehicle.organization_id == organizationId)
            .where(Vehicle.Vehicleno.isnot(None))
            .where(~Vehicle.Vehicleno.in_(
                select(Driver.Vehicleno)
                .where(Driver.Organization_id == organizationId)
                .where(Driver.Vehicleno.isnot(None))
            ))
        )
        unassigned_vehicles_count = session.execute(unassigned_vehicles_query).scalar()

        return jsonify({
            "unassigned_drivers_count": unassigned_drivers_count,
            "assigned_drivers_count": assigned_drivers_count,
            "unassigned_vehicles_count": unassigned_vehicles_count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

def get_unassigned_drivers(organizationId):

    session = Session()
    try:
        # owner = session.query(Owner).filter(Owner.user_id == organizationId).first()

        # if not owner:
        #     return jsonify({"error": "Owner not found for the given organization user ID"}), 404

        query = (
            select(User.id, User.fname, User.lname)
            .select_from(User)
            .join(Driver, User.id == Driver.user_id)
            .filter(Driver.Organization_id == organizationId, Driver.Vehicleno == None)
        )

        results = session.execute(query).all()

        drivers = [{"id": id, "first_name": fname, "last_name": lname} for id, fname, lname in results]        

        return jsonify({"Results": drivers}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


def get_owner_by_userId(userId):

    session = Session()
    try:
        query = (
            select(
                User.fname,
                User.lname,
                User.phone,
                User.email,
            )
            .select_from(User)
            .where(User.id == userId)
        )

        result = session.execute(query).first()

        if result:
            owner_details = {
                "first_name": result.fname,
                "last_name": result.lname,
                "phone": result.phone,
                "email": result.email,
            }
            return jsonify({"Result": owner_details}), 200
        else:
            return jsonify({"error": "Owner not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


def get_total_count(organizationId):
    session = Session()
    try:
        # owner = session.query(Owner).filter(Owner.user_id == organizationId).first()

        # if not owner:
        #     return jsonify({"error": "Owner not found for the given organization user ID"}), 404

        # Count of drivers for the given organizationId
        total_drivers_query = (
            select(func.count())
            .where(Driver.Organization_id == organizationId)
        )
        total_drivers_count = session.execute(total_drivers_query).scalar()

        # Count of vehicles for the given organizationId
        total_vehicles_query = (
            select(func.count())
            .where(Vehicle.organization_id == organizationId)
        )
        total_vehicles_count = session.execute(total_vehicles_query).scalar()

        return jsonify({
            "total_drivers_count": total_drivers_count,
            "total_vehicles_count": total_vehicles_count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

def edit_owner_details(userId):

    session = Session()
    try:
        # Ensure the request data is JSON
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400

        data = request.get_json()
        user_id = userId
        fname = data.get('fname')
        lname = data.get('lname')
        phone = data.get('phone')
        email = data.get('email')

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        if not (fname and lname and phone and email):
            return jsonify({"error": "All fields (fname, lname, phone, email) are required"}), 400

        # Fetch the user
        user = session.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({"error": "User not found for the given user ID"}), 404

        # Update the user's details
        user.fname = fname
        user.lname = lname
        user.phone = phone
        user.email = email
        session.commit()

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        session.close()

def edit_driver_details(userId):

    session = Session()
    try:
        # Ensure the request data is JSON
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400

        data = request.get_json()
        user_id = userId  # Assuming userId is already defined
        fname = data.get('fname')
        lname = data.get('lname')
        phone = data.get('phone')
        email = data.get('email')
        residence = data.get('residence')

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        if not (fname and lname and phone and email and residence):
            return jsonify({"error": "All fields (fname, lname, phone, email, residence) are required"}), 400

        # Fetch the user
        user = session.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({"error": "User not found for the given user ID"}), 404

        # Fetch the associated driver (assuming one-to-one relationship between User and Driver)
        driver = session.query(Driver).filter(Driver.user_id == user_id).first()

        if not driver:
            return jsonify({"error": "Driver not found for the given user ID"}), 404

        # Update the user's details
        user.fname = fname
        user.lname = lname
        user.phone = phone
        user.email = email

        # Update the driver's residence
        driver.residence = residence

        session.commit()

        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        session.close()

# def insert_owner(userId):
#     session = Session()
#     try:
#         # Extract values from the request body
#         owner_user_id = userId 

#         # Debugging: Print extracted values
#         print(f"Owner User ID: {owner_user_id}")

#         # Check if owner_user_id is provided
#         if not owner_user_id:
#             return jsonify({"error": "UserID is required"}), 400

#         # Check if the user already exists in the database
#         owner = session.query(Owner).filter_by(user_id=owner_user_id).first()

#         if owner:
#             session.rollback()
#             return jsonify({"error": "User is already in the database"}), 401

#         # Create new owner instance
#         new_owner = Owner(
#             user_id=owner_user_id
#         )

#         session.add(new_owner)
#         session.commit()  # Commit to save the new owner

#         return jsonify({"success": "Owner added successfully"}), 201

#     except Exception as e:
#         session.rollback()
#         print(e)
#         return jsonify({"error": "Failed to add owner"}), 500

#     finally:
#         session.close()