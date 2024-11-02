from app.models import CargoRide, RideStatus, UserType, User, base, Cargo
from database import Session
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify
import requests
import polyline

def confirm_ride(userId = None):

    try:
        all_rides = allRides(userId)

        ride_list = []
        seen_ids = set()

        for ride in all_rides:
            if (ride[19]==1 and ride[21]!=1 and ride[21]!=3 and ride[18]==userId) and (ride[0] != 'EconomicCenterSeller') and ride[17] not in seen_ids:
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
                print(ride_dict)
                
                ride_list.append(ride_dict)
                seen_ids.add(ride[17])
        return ride_list
    except SQLAlchemyError as e:
        print(f"Error fetching confirmed rides for Driver ID {userId}: {e}"), 500
        return {}

def update_driver_confirmation(userId, body):
    print(body)
    print(userId)
    session = Session()

    try:
        for ride_data in body:
            ride_id = ride_data.get('id')
            print(ride_id)
            confirmed_ride = session.query(RideStatus).filter(RideStatus.ride_id == ride_id).first()
            confirmed_driver = session.query(CargoRide).filter(CargoRide.id == ride_id).first()
            print(confirmed_driver)

            # Check if the ride exists
            if confirmed_ride and confirmed_driver:
                # Update the driver confirmation and driver id
                confirmed_ride.driver_confirmation = True
                confirmed_driver.driver_id = userId
            else:
                print(f"Ride with id {ride_id} does not exist.")
                return {'message': f"Ride with id {ride_id} does not exist."}, 404
        
        session.commit()
        return jsonify({"message": "Driver confirmed successfully", "ok": True}), 200

    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        session.close()
 
def update_driver_rejection(body):
    
    print(body)
    session = Session()

    try:
        for ride_data in body:
            ride_id = ride_data.get('id')
            rejected_ride = session.query(RideStatus).filter(RideStatus.ride_id == ride_id).first()
            
            # Check if the ride exists
            if rejected_ride:
                # Update the driver confirmation and driver id
                rejected_ride.driver_rejection = True
                session.commit()
                return jsonify({"message": "Ride rejected successfully by driver", "ok":True}), 200
            else:
                # Handle case where the ride does not exist
                print(f"Ride with id {ride_id} does not exist.")
                return jsonify({"message": "Ride does not exist", "ok":False}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()


def allRides(userId):
    print(userId)
    session = Session()

    try:
        # all_rides = session.query(CargoRide).all()
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
            .filter(CargoRide.driver_id == userId) \
            .all()
        
        session.commit()
        print("driver rides", all_rides)
        return all_rides
    
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching all rides for Driver ID {userId}: {e}"), 500
        return {}

    finally:
        session.close()

def totalWeight(userId):
    print("id", userId)
    total_Weight = 0
    all_rides = allRides(userId)
    for ride in all_rides:    
        if (ride[19]==1 and ride[21]==0 and ride[18]==userId):
            total_Weight += ride[6]
    print("totalWeight", total_Weight)
    return total_Weight

def remainingWeight(totalWeight, maxWeight):
    return maxWeight - totalWeight