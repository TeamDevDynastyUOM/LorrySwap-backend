from flask import jsonify
from sqlalchemy.orm import Session
from app.models import CargoRide, RideStatus, UserType, User, base, Cargo
from database import Session
from sqlalchemy.exc import SQLAlchemyError
import os

def special_ride(userId=None):
    apiKey = 'AIzaSyACh5R4n7riZPvRd7MHiXlByMvSjdP6zI4'
    try:
        if not apiKey:
            return jsonify({'error': 'Google Maps API key not found'}), 500

        with Session() as session:
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

            # driver_ride = session.query(Ride).filter(Ride.user_id == userId).order_by(Ride.id.desc()).first()
            new_ride_list = []

            if all_rides:
                for ride in all_rides:
                    if (ride[19] == False) and (ride[20] == True) and (ride[24] == False) and (ride[21] == 0) and (ride[18] == userId) and (ride[26] == True):
                        new_ride_list.append(ride)

            ride_list = []
            ride_list = [format_ride_dict(ride) for ride in new_ride_list]
            return jsonify(ride_list)
        
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching special rides for Driver ID {userId}: {e}"), 500
        return {}

    finally:
        session.close()

def format_ride_dict(ride):
    return {
        'id': ride[17], 'contact_recipient': ride[3], 'date': ride[4], 'package_type': ride[5],
        'weight': ride[6], 'height': ride[7], 'length': ride[8], 'width': ride[9],
        'truck_type': ride[10], 'photo': ride[2], 'location': ride[11], 'destination': ride[12],
        'plat': ride[13], 'plon': ride[14], 'dlat': ride[15], 'dlon': ride[16],
        'actor': ride[0], 'fname': ride[1], 'lname': ride[23], 'phone': ride[22],
        'driver_id': ride[18], 'driver_confirmation': ride[19], 'cf_confirmation': ride[20],
        'finished': ride[21], 'driver_rejection': ride[24], 'cf_rejection': ride[25], 'special_request': ride[26],
        'cost' : ride[27],
    }

