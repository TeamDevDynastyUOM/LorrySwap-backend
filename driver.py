from app.models import User, Driver, base, UserType, Authentication,Ride,DriverLocation, Vehicle, RideStatus,CargoRide
from scripts.hash import hash_password, verify_password
from database import Session 
from sqlalchemy import select 
from flask import request, jsonify
from scripts.upload_to_gdrive import upload_licene_image
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from scripts.token import generate_token
from scripts.optimal_path import get_distances, create_graph, find_shortest_path, generate_google_maps_url
from auth import auth_token_required
import datetime
import re
import os


@auth_token_required(roles_required=['Driver'])
def upload_license(token_info=None, user=None, body=None, licenseImage=None):
    print(request)
    print(request.files)
    if 'licenseImage' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['licenseImage']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        # Ensure the 'Images/License2' directory exists
        save_directory = 'Images/License2'
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        
        filename = secure_filename(file.filename)
        temp_file_path = os.path.join(save_directory, filename)
        
        # Save the file to the specified directory
        file.save(temp_file_path)
        
        try:
            # Upload the file to Google Drive and get the shareable link
            shareable_link = upload_licene_image(temp_file_path)
            # Delete the temporary file after upload
            os.remove(temp_file_path)
            return jsonify({'message': 'Image uploaded successfully', 'shareable_link': shareable_link}), 200
        except Exception as e:
            # Ensure to delete the temporary file even if the upload fails
            os.remove(temp_file_path)
            return jsonify({'error': 'Failed to upload image', 'details': str(e)}), 500


@auth_token_required(roles_required=['Driver'])
def save_license_todb(token_info=None, user=None, body=None):
    session = Session()

    user_id = body.get('user_id')
    residence = body.get('residence')
    licence_side1 = body.get('licence_side1')
    licence_side2 = body.get('licence_side2')

    if not user_id or not residence:
        return jsonify({'error': 'User ID and residence are required fields.'}), 400

    new_driver = Driver(
        user_id=user_id,
        residence=residence,
        licence_side1=licence_side1,
        licence_side2=licence_side2,
    )

    try:
        session.add(new_driver)
        session.commit()
        return jsonify({'message': 'Data saved successfully'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': 'Failed to save data', 'details': str(e)}), 500


@auth_token_required(roles_required=['Driver'])
def find_optimal_path(token_info=None, user=None, body=None):

    body = request.json

    origin = body.get('origin')
    destination = body.get('destination')
    waypoints = body.get('waypoints')

    stops = [origin] + [wp['pickup'] for wp in waypoints.values()] + [wp['drop'] for wp in waypoints.values()] + [destination]
    distances = get_distances(stops)

    graph = create_graph(distances)

    route, total_distance = find_shortest_path(graph, origin, destination, waypoints)
    if isinstance(route, str):  # check if no feasible route found
        return jsonify({"status": "failure", "message": route}), 400

    print(route)
    print(str(total_distance / 1000) + "km")

    maps_url = generate_google_maps_url(origin, destination, [step['location'] for step in route])
    print("Google Maps URL:", maps_url)
    return jsonify({
        "status": "success", 
        "optimal_path": route, 
        "total_distance": str(total_distance / 1000) + " km", 
        "map_url": maps_url
    }), 200


@auth_token_required(roles_required=['CargoFinder', 'MarkerSeller'])
def search_driver(token_info=None, user=None):
    session = Session()
    print("hello")
    try:
        drivers = session.query(
                User.id, User.fname, User.lname, User.phone,
                User.age, User.gender, User.email, User.photo,
                Ride.finished_ride
            )\
            .select_from(User)\
            .join(Driver, User.id == Driver.user_id)\
            .outerjoin(Ride, User.id == Ride.user_id)\
            .all()

        # rides = session.query(Ride).filter(Ride.finished_ride == False)
       
        driver_list = []
        seen_driver_ids = set()
        
        for driver in drivers:
            if driver[8] == 0 or driver[8] == None:
                if driver[0] not in seen_driver_ids:

                    driver_dict = {
                        "id": driver[0],
                        "fname": driver[1],
                        "lname": driver[2],
                        "phone": driver[3],
                        "age": driver[4],
                        "gender": driver[5],
                        "email": driver[6],
                        "photo": driver[7],
                        "finished": driver[8]
                    }
                    driver_list.append(driver_dict)
                    seen_driver_ids.add(driver[0])

        print(driver_list)
        return driver_list

    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching drivers. {e}"), 500
        return {}
    

@auth_token_required(roles_required=['Driver'])
def check_license(token_info=None, user=None, userId=None):
    session = Session()
    driver = session.query(Driver).filter(Driver.user_id == userId).first()
    if not driver:
        return jsonify({"message": "Driver not found."}), 404
    if driver.licence_side1 and driver.licence_side2:
        return jsonify({"message": "License is valid."}), 200
    else:
        return jsonify({"message": "License is invalid. Please upload a valid license image."}), 400



@auth_token_required(roles_required=['Driver'])
def updateCurrentLocation(token_info=None, user=None, body=None):
    session = Session()
    body = request.get_json()
    if not body:
        return jsonify({'error': 'Request body is missing'}), 400

    driver_id = body.get('driver_id')
    latitude = body.get('latitude')
    longitude = body.get('longitude')

    if not all([driver_id, latitude, longitude]):
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        driver_location = session.query(DriverLocation).filter_by(driver_id=driver_id).one_or_none()

        if driver_location:
            driver_location.latitude = latitude
            driver_location.longitude = longitude
        else:
            new_location = DriverLocation(driver_id=driver_id, latitude=latitude, longitude=longitude)
            session.add(new_location)

        session.commit()
        return jsonify({'message': 'Location updated successfully'}), 200 if driver_location else 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()



@auth_token_required(roles_required=['Driver'])
def verify_driver(token_info=None, user=None, userId=None):
    if userId is None:
        return jsonify({'error': 'User ID is missing'}), 400

    session = Session()
    # print(session,userId)
    try:
        driver = session.query(Driver).filter_by(user_id=userId).one_or_none()
        print(driver)
        if driver is None:
            return jsonify({'error': 'No driver found'}), 404

        if driver.verify == 1:
            return jsonify({'status': 'OK'}), 200
        else:
            return jsonify({'error': 'NOK'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


def get_vehicle_details(userId=None):
    session = Session()

    try:
        driver = session.query(Driver).filter(Driver.user_id == userId).first()

        if not driver:
            return jsonify({'error': 'No driver found'}), 404

        vehicle_no = driver.Vehicleno

        vehicle = session.query(Vehicle).filter(Vehicle.Vehicleno == vehicle_no).first()

        if not vehicle:
            vehicle_details = {}

            return vehicle_details
        
        else:
            vehicle_details = {
                "id": vehicle.id, 
                "Vehicleno": vehicle.Vehicleno,
                "brand": vehicle.brand,
                "model": vehicle.model,
                "type": vehicle.type, 
                "length":vehicle.length, 
                "width":vehicle.width,  
                "height":vehicle.height,  
                "tonnage":vehicle.tonnage,
                "verify": vehicle.verify
            }

            return vehicle_details
        
    except Exception as e:
        return {"error": str(e)},500

    finally:
        session.close()

