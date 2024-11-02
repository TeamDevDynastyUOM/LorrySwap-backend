from app.models import CargoRide, Ride, UserType, User, RideStatus, base, Cargo
from database import Session
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
import requests
import polyline

def suggested_ride(userId=None):
    print(userId)

    session = Session()
    try:
        all_rides = session.query(
            UserType.user_type, User.fname, User.photo, CargoRide.contact_recipient, 
            CargoRide.date, CargoRide.package_type, CargoRide.weight, Cargo.height,
            Cargo.length, Cargo.width, CargoRide.truck_type,
            CargoRide.location, CargoRide.destination, CargoRide.plat, CargoRide.plon,
            CargoRide.dlat, CargoRide.dlon, CargoRide.id, CargoRide.driver_id,
            RideStatus.driver_confirmation, RideStatus.cf_confirmation,
            RideStatus.finished, User.phone, User.lname, RideStatus.driver_rejection,
            RideStatus.cf_rejection, CargoRide.special_request, CargoRide.cost
            )\
            .join(User, UserType.user_id == User.id) \
            .join(CargoRide, CargoRide.user_id == User.id) \
            .join(RideStatus, RideStatus.ride_id == CargoRide.id) \
            .join(Cargo, Cargo.ride_id == CargoRide.id) \
            .all()

        print("all",all_rides)

        driver_ride = session.query(Ride).filter(Ride.user_id == userId).order_by(Ride.id.desc()).first()

        print("driver",driver_ride)
        
        new_ride_list = matchRide(
                driver_ride.location_lat, driver_ride.location_lon,
                driver_ride.destination_lat,driver_ride.destination_lon, all_rides)
        
        print('new rides ',new_ride_list)


        session.commit()

        ride_list = []
        seen_ids = set()

        for ride in new_ride_list:
            if ride[0] != 'EconomicCenterSeller'and driver_ride.date == ride[4] and ride[17] not in seen_ids :
                ride_dict = {
                    'id': ride[17], 'contact_recipient' : ride[3],'date' : ride[4],
                    'package_type' : ride[5], 'weight' : ride[6], 'height' : ride[7],
                    'length' : ride[8], 'width' : ride[9], 'truck_type' : ride[10],
                    'photo' : ride[2], 'location' : ride[11], 'destination' : ride[12],
                    'plat' : ride[13], 'plon' : ride[14], 'dlat' : ride[15],
                    'dlon':  ride[16], 'actor' : ride[0], 'fname' : ride[1],
                    'lname' : ride[23], 'phone' : ride[22], 'driver_id' : ride[18],
                    'driver_confirmation' : ride[19],'cf_confirmation' : ride[20],
                    'finished' : ride[21], 'driver_rejection' : ride[24],
                    'cf_rejection' : ride[25], 'special_request': ride[26],
                    'cost' : ride[27],
                }
                ride_list.append(ride_dict)
                seen_ids.add(ride[17])

        print('rideList is', ride_list)

        return ride_list
    
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching suggested rides for Driver ID {userId}: {e}"), 500
        return {}

    finally:
        session.close()

def suggested_ride_returns(userId=None):
    print(userId)

    session = Session()
    try:
        all_rides = session.query(
            UserType.user_type, User.fname, User.photo, CargoRide.contact_recipient, 
            CargoRide.date, CargoRide.package_type, CargoRide.weight, Cargo.height,
            Cargo.length, Cargo.width, CargoRide.truck_type,
            CargoRide.location, CargoRide.destination, CargoRide.plat, CargoRide.plon,
            CargoRide.dlat, CargoRide.dlon, CargoRide.id, CargoRide.driver_id,
            RideStatus.driver_confirmation, RideStatus.cf_confirmation,
            RideStatus.finished, User.phone, User.lname, RideStatus.driver_rejection,
            RideStatus.cf_rejection, CargoRide.special_request, CargoRide.cost
            )\
            .join(User, UserType.user_id == User.id) \
            .join(CargoRide, CargoRide.user_id == User.id) \
            .join(RideStatus, RideStatus.ride_id == CargoRide.id) \
            .join(Cargo, Cargo.ride_id == CargoRide.id) \
            .all()

        print("all",all_rides)

        driver_ride = session.query(Ride).filter(Ride.user_id == userId).order_by(Ride.id.desc()).first()

        print("driver",driver_ride)
        
        new_ride_list = matchRide(
                driver_ride.destination_lat,driver_ride.destination_lon,
                driver_ride.location_lat, driver_ride.location_lon, all_rides)
        
        print(new_ride_list)

        session.commit()

        ride_list = []
        seen_ids = set()

        for ride in new_ride_list:
            if ride[0] != 'EconomicCenterSeller' and ride[17] not in seen_ids:
                ride_dict = {
                    'id': ride[17], 'contact_recipient' : ride[3],'date' : ride[4],
                    'package_type' : ride[5], 'weight' : ride[6], 'height' : ride[7],
                    'length' : ride[8], 'width' : ride[9], 'truck_type' : ride[10],
                    'photo' : ride[2], 'location' : ride[11], 'destination' : ride[12],
                    'plat' : ride[13], 'plon' : ride[14], 'dlat' : ride[15],
                    'dlon':  ride[16], 'actor' : ride[0], 'fname' : ride[1],
                    'lname' : ride[23], 'phone' : ride[22], 'driver_id' : ride[18],
                    'driver_confirmation' : ride[19],'cf_confirmation' : ride[20],
                    'finished' : ride[21], 'driver_rejection' : ride[24],
                    'cf_rejection' : ride[25], 'special_request': ride[26],
                    'cost' : ride[27],
                }
                ride_list.append(ride_dict)
                seen_ids.add(ride[17])
        return ride_list
    
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching suggested rides for Driver ID {userId}: {e}"), 500
        return {}

    finally:
        session.close()

def matchRide(location_lat, location_lon, destination_lat, destination_lon,  all_rides):

    originLat = location_lat
    originLng = location_lon
    destinationLat = destination_lat
    destinationLng = destination_lon
    apiKey = 'AIzaSyACh5R4n7riZPvRd7MHiXlByMvSjdP6zI4'

    ride_list_pickup = []
    new_ride_list = []

    try:
        response = requests.get(
            f'https://maps.googleapis.com/maps/api/directions/json?origin={originLat},{originLng}&destination={destinationLat},{destinationLng}&key={apiKey}'
        )
        data = response.json()
        encoded_polyline = data['routes'][0]['overview_polyline']['points']
        decoded_coordinates = polyline.decode(encoded_polyline)

        for ride in all_rides:

            for coordinate in decoded_coordinates:

                current_coordLat = f"{round(coordinate[0], 1)}"
                current_coordLng = f"{round(coordinate[1], 1)}"
                current_ride_PLat = f"{round(float(ride[13]), 1)}"
                current_ride_PLng = f"{round(float(ride[14]), 1)}"
                current_ride_DLat = f"{round(float(ride[15]), 1)}"
                current_ride_DLng = f"{round(float(ride[16]), 1)}"

                if (current_ride_PLat == current_coordLat and current_ride_PLng == current_coordLng and ride[19] == False and ride[26] == False):
                    ride_list_pickup.append(ride)
                    break;
                if (current_ride_DLat == current_coordLat and current_ride_DLng == current_coordLng and ride[19] == False):
                    break;

        for ride in ride_list_pickup:

            for coordinate in decoded_coordinates:

                current_coordLat = f"{round(coordinate[0], 1)}"
                current_coordLng = f"{round(coordinate[1], 1)}"
                current_ride_DLat = f"{round(float(ride[15]), 1)}"
                current_ride_DLng = f"{round(float(ride[16]), 1)}"

                if (current_ride_DLat == current_coordLat and current_ride_DLng == current_coordLng):
                    new_ride_list.append(ride)
                    break;

        return new_ride_list
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500






# from flask import jsonify
# import requests
# import polyline
# from sqlalchemy.orm import Session
# from app.models import CargoRide, Ride, UserType, User, Driver, base
# from database import Session
# import os

# def suggested_ride(userId=None):
#     apiKey = 'AIzaSyACh5R4n7riZPvRd7MHiXlByMvSjdP6zI4'
    
#     if not apiKey:
#         return jsonify({'error': 'Google Maps API key not found'}), 500

#     with Session() as session:
#         all_rides = session.query(
#             UserType.user_type, User.fname, User.photo,
#             CargoRide.contact_recipient, CargoRide.date, CargoRide.package_type,
#             CargoRide.weight, CargoRide.height, CargoRide.length, CargoRide.width,
#             CargoRide.truck_type, CargoRide.location, CargoRide.destination,
#             CargoRide.plat, CargoRide.plon, CargoRide.dlat, CargoRide.dlon,
#             CargoRide.id, CargoRide.driver_id, CargoRide.driver_confirmation,
#             CargoRide.cf_confirmation, CargoRide.finished, User.phone, User.lname,
#             CargoRide.driver_rejection, CargoRide.cf_rejection, CargoRide.special_request
#         )\
#         .join(User, UserType.user_id == User.id) \
#         .join(CargoRide, CargoRide.user_id == User.id) \
#         .all()

#         driver_ride = session.query(Ride).filter(Ride.user_id == userId).order_by(Ride.id.desc()).first()

#         if driver_ride is None:
#             return jsonify({'message': 'No ride found for user ID'}), 404

#         new_ride_list = matchRide(driver_ride, all_rides, apiKey)

#         ride_list = [format_ride_dict(ride) for ride in new_ride_list]
#         return jsonify(ride_list)

# def matchRide(driver_ride, all_rides, apiKey):
#     origin = f"{driver_ride.location_lat},{driver_ride.location_lon}"
#     destination = f"{driver_ride.destination_lat},{driver_ride.destination_lon}"

#     try:
#         response = requests.get(
#             f'https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={apiKey}'
#         )
#         data = response.json()
#         encoded_polyline = data['routes'][0]['overview_polyline']['points']
#         decoded_coordinates = polyline.decode(encoded_polyline)

#         ride_list_pickup = []
#         new_ride_list = []

#         for ride in all_rides:
#             for coord in decoded_coordinates:
#                 if matches_coordinate(ride, coord):
#                     ride_list_pickup.append(ride)
#                     break

#         for ride in ride_list_pickup:
#             if is_destination_match(ride, decoded_coordinates):
#                 new_ride_list.append(ride)

#         return new_ride_list
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# def matches_coordinate(ride, coord):
#     ride_plat = round(float(ride[13]), 1)
#     ride_plon = round(float(ride[14]), 1)
#     coord_lat = round(coord[0], 1)
#     coord_lon = round(coord[1], 1)
#     return (ride_plat == coord_lat and ride_plon == coord_lon and not ride[19] and not ride[18] and not ride[26] and not ride[21])

# def is_destination_match(ride, decoded_coordinates):
#     for coord in decoded_coordinates:
#         coord_lat = round(coord[0], 1)
#         coord_lon = round(coord[1], 1)
#         ride_dlat = round(float(ride[15]), 1)
#         ride_dlon = round(float(ride[16]), 1)
#         if ride_dlat == coord_lat and ride_dlon == coord_lon:
#             return True
#     return False

# def format_ride_dict(ride):
#     return {
#         'id': ride[17], 'contact_recipient': ride[3], 'date': ride[4], 'package_type': ride[5],
#         'weight': ride[6], 'height': ride[7], 'length': ride[8], 'width': ride[9],
#         'truck_type': ride[10], 'photo': ride[2], 'location': ride[11], 'destination': ride[12],
#         'plat': ride[13], 'plon': ride[14], 'dlat': ride[15], 'dlon': ride[16],
#         'actor': ride[0], 'fname': ride[1], 'lname': ride[23], 'phone': ride[22],
#         'driver_id': ride[18], 'driver_confirmation': ride[19], 'cf_confirmation': ride[20],
#         'finished': ride[21], 'driver_rejection': ride[24], 'cf_rejection': ride[25], 'special_request': ride[26],
#     }
