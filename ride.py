from app.models import Ride, Driver, User, RideStatus
from database import Session
from sqlalchemy import and_
from flask import jsonify
from auth import auth_token_required
from sqlalchemy.exc import SQLAlchemyError

@auth_token_required(roles_required=['Driver'])
def create_ride(token_info=None, user=None,body=None):
    print(body)

    session = Session()
    
    location = body.get('location')
    destination = body.get('destination')
    location_lat = body.get('location_lat')
    location_lon = body.get('location_lon')
    destination_lat = body.get('destination_lat')
    destination_lon = body.get('destination_lon')
    date = body.get('date')
    time = body.get('time')
    user_id = body.get('user_id')
    finished_ride = body.get('finished_ride')

    try:
        new_ride = Ride(
            location = location,
            destination = destination,
            location_lat=location_lat,
            location_lon=location_lon,
            destination_lat=destination_lat, 
            destination_lon=destination_lon,
            date=date, 
            time=time,
            user_id=user_id,
            finished_ride=finished_ride
        )
        session.add(new_ride)
        session.flush()

        session.commit()
        return jsonify({'message': "New ride successfully created"}), 200
    except Exception as e:
        session.rollback()
        print(f"Error creating newride: {e}")
        return jsonify({'message': "Error creating new ride, {e}"}), 500
    finally:
        session.close()

@auth_token_required(roles_required=['Driver'])
def get_all_rides(token_info=None, user=None):
    session = Session()
    try:
        # Use SQLAlchemy select to query all Rides objects
        all_rides = session.query(Ride).all()

        # Convert each Ride object to a dictionary
        rides_list = []
        for ride in all_rides:
            ride_dict = {
                'id': ride.id,
                'location_lat': ride.location_lat,
                'location_lon': ride.location_lon,
                'destination_lat': ride.destination_lat,
                'destination_lon': ride.destination_lon,
                'date': ride.date,
                'time': ride.time,
                'user_id': ride.user_id,
                'finished_ride' : ride.finished_ride
            }
            rides_list.append(ride_dict)

        # Return the list of dictionaries
        return rides_list
    
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching all ride. {e}"), 500
        return {}

    finally:
        session.close()


@auth_token_required(roles_required=['Driver'])
def get_current_ride(token_info=None, user=None,userId=None):
    session = Session()

    try:    
        # Query the database to find the ride with the given user ID
        driver_ride = session.query(Ride).filter(and_(Ride.user_id == userId, Ride.finished_ride == 0)).order_by(Ride.id.desc()).first()

        # If no ride is found, return None
        if not driver_ride:
            return {}

        # Convert the ride object to a dictionary
        ride_dict = {
            'id': driver_ride.id,
            'location_lat': driver_ride.location_lat,
            'location_lon': driver_ride.location_lon,
            'destination_lat': driver_ride.destination_lat,
            'destination_lon': driver_ride.destination_lon,
            'date': driver_ride.date,
            'time': driver_ride.time,
            'user_id': driver_ride.user_id,
            'location': driver_ride.location,
            'destination': driver_ride.destination,
            'finished_ride': driver_ride.finished_ride
        }

        # Return the dictionary representing the ride
        return ride_dict

    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching current ride for user ID {userId}: {e}"), 500
        return {}

    finally:
        session.close()

@auth_token_required(roles_required=['Driver'])
def delete_ride(token_info=None, user=None,userId=None):
    session = Session()

    try:
        # Query the database to find the ride with the given ID
        ride = session.query(Ride).filter(Ride.user_id == userId).order_by(Ride.id.desc()).first()

        # If the ride exists, delete it from the database
        if ride:
            session.delete(ride)
            session.commit()
            return True, 204  
        else:
            return False, 404

    except SQLAlchemyError as e:
        session.rollback()  
        print(f"Error deleting ride for user ID {userId}: {e}")
        return False, 500
    
    finally:
        session.close()

def update_driver_start_ride(userId, body):
    print(body)
    print(userId)
    session = Session()

    try:
        ride = session.query(Ride).filter(Ride.user_id == userId).order_by(Ride.id.desc()).first()

        if ride:
            # Update the driver confirmation and driver id
            ride.finished_ride = 2

            for ride_data in body:
                ride_id = ride_data.get('id')
                print(ride_id)
                confirmed_ride = session.query(RideStatus).filter(RideStatus.ride_id == ride_id).first()
                print(confirmed_ride)

                # Check if the ride exists
                if confirmed_ride:
                    confirmed_ride.finished = 2
                else:
                    print(f"Ride with id {ride_id} does not exist.")
                    return {'message': f"Ride with id {ride_id} does not exist."}, 404
                
        else:
            # Handle case where the ride does not exist
            print(f"userId with id {userId} has not any ride.")
            return jsonify({"message": "Ride does not exist", "ok":False}), 404
        
        session.commit()
        return jsonify({"message": "Driver confirmed successfully", "ok": True}), 200

    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        session.close()

def update_driver_finished_ride(userId=None):
    
    session = Session()

    try:
        driver_ride = session.query(Ride).filter(and_(Ride.user_id == userId)).order_by(Ride.id.desc()).first()
        print(driver_ride)
        # Check if the ride exists
        if driver_ride:
            # Update the cf rejection and driver id
            driver_ride.finished_ride = 1
            session.commit()
            return jsonify({"message": " Ride Finished", "ok":True}), 200
        else:
            # Handle case where the ride does not exist
            print(f"User with id {userId} does not exist.")
            return jsonify({"message": "user does not exist", "ok":False}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()
