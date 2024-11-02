# from app.models import PackageDetails
from flask import jsonify
from app.models import CargoRide,RideStatus, UserType, User, Cargo, Order, EconomicCenter
from database import Session
from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy.orm import aliased

def create_packageDetails(body):
    # Print the body of the request to check its contents
    session = Session()

    # Extract data from the request body
    package_type = body.get('package_type')
    weight = body.get('weight')
    height = body.get('height')
    length = body.get('length')
    width = body.get('width')
    truck_type = body.get('truck_type')
    location = body.get('location')
    destination = body.get('destination')
    plat = body.get('plat')
    plon = body.get('plon')
    dlat = body.get('dlat')
    dlon = body.get('dlon')
    date = body.get('date')
    user_id = body.get('user_id')
    contact_recipient = body.get('contact_recipient')
    cost = body.get('cost')

    try:
        # Create a new PackageDetails object with the extracted data
        new_package = CargoRide(
            package_type = package_type,
            weight = weight,
            truck_type = truck_type,
            location = location,
            destination = destination,
            plat = plat,
            plon = plon,
            dlat = dlat,
            dlon = dlon,
            date = date,
            user_id = user_id,
            contact_recipient = contact_recipient,
            cost = cost
        )
        session.add(new_package)
        session.flush()

        # Fetch the ID of the newly created CargoRide object
        new_package_id = new_package.id
        print(new_package_id)

        new_cargo = Cargo(
            ride_id=new_package.id,
            height = height,
            length = length,
            width = width,
        )
        session.add(new_cargo)
        session.flush()

        new_ride_status = RideStatus(
            ride_id=new_package.id,
        )
        session.add(new_ride_status)
        session.flush()
        session.commit()

        # Return the new_package_id as JSON response
        return jsonify({'order_id': new_package_id , 'message': "New ride successfully created"}), 200

    except Exception as e:
        session.rollback()
        print(f"Error creating new package: {e}")
        return jsonify({'message': "Error creating new package, {e}"}), 500
    finally:
        session.close()

def create_MSDetails(body):
    # Print the body of the request to check its contents
    session = Session()

    # Extract data from the request body
    package_type = body.get('package_type')
    weight = body.get('weight')
    truck_type = body.get('truck_type')
    location = body.get('location')
    destination = body.get('destination')
    plat = body.get('plat')
    plon = body.get('plon')
    dlat = body.get('dlat')
    dlon = body.get('dlon')
    date = body.get('date')
    user_id = body.get('user_id')
    contact_recipient = body.get('contact_recipient')
    cost = body.get('cost')

    try:
        # Create a new PackageDetails object with the extracted data
        new_package = CargoRide(
            package_type=package_type,
            weight=weight,
            truck_type=truck_type,
            location=location,
            destination=destination,
            plat=plat,
            plon=plon,
            dlat=dlat,
            dlon=dlon,
            date=date,
            user_id=user_id,
            contact_recipient=contact_recipient,
            cost=cost
        )
        session.add(new_package)
        session.flush()

        # Fetch the ID of the newly created CargoRide object
        new_package_id = new_package.id
        print(new_package_id)

        new_ride_status = RideStatus(
            ride_id=new_package.id,
        )
        session.add(new_ride_status)
        session.flush()
        session.commit()

        order = (
            session.query(Order)
            .join(EconomicCenter, Order.economic_center_id == EconomicCenter.id)
            .filter(
                Order.seller_id == user_id,
                Order.dueDate == date,
                EconomicCenter.name == location,
            )
            .first()
        )

        if order:
            order.cargo_ride_id = new_package_id

        session.commit()
        # Return the new_package_id as JSON response
        return jsonify({'order_id': new_package_id, 'message': "New ride successfully created"}), 200

    except Exception as e:
        session.rollback()
        print(f"Error creating new package: {e}")
        return jsonify({'message': f"Error creating new package, {e}"}), 500
    finally:
        session.close()

def update_cf_confirmation(body):
    
    print(body)
    session = Session()

    try:
        for ride_data in body:
            ride_id = ride_data.get('id')
            print(ride_id)
            confirmed_ride = session.query(RideStatus).filter(RideStatus.ride_id == ride_id).first()

            # Check if the ride exists
            if confirmed_ride:
                # Update the cf confirmation
                confirmed_ride.cf_confirmation = True
                session.commit()
                return jsonify({"message": "CF confirmed successfully", "ok":True}), 200
            else:
                # Handle case where the ride does not exist
                print(f"Ride with id {ride_id} does not exist.")
                return {'message': f"Ride with id {ride_id} does not exist."}, 404
                
    except Exception as e:
        session.rollback()
        return {'error': str(e)}, 500
    finally:
        session.close()

def update_cf_rejection(body):
    
    print(body)
    session = Session()

    try:
        for ride_data in body:
            ride_id = ride_data.get('id')
            rejected_ride = session.query(RideStatus).filter(RideStatus.ride_id == ride_id).first()
            confirmed_driver = session.query(CargoRide).filter(CargoRide.id == ride_id).first()
            
            # Check if the ride exists
            if rejected_ride:
                # Update the cf rejection and driver id
                # rejected_ride.cf_rejection = True
                rejected_ride.driver_confirmation = False
                confirmed_driver.driver_id = None
                session.commit()
                return jsonify({"message": "Request rejected successfully by CF", "ok":True}), 200
            else:
                # Handle case where the ride does not exist
                print(f"Ride with id {ride_id} does not exist.")
                return jsonify({"message": "Ride does not exist", "ok":False}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()

def update_retry(body):
    
    print(body)
    session = Session()

    try:
        for ride_data in body:
            ride_id = ride_data.get('id')
            ride = session.query(RideStatus).filter(RideStatus.ride_id == ride_id).first()
            requested_driver = session.query(CargoRide).filter(CargoRide.id == ride_id).first()
            
            # Check if the ride exists
            if ride:
                # Update the cf rejection and driver id
                ride.cf_confirmation = False
                ride.driver_rejection = False
                requested_driver.special_request = False
                requested_driver.driver_id = None
                session.commit()
                return jsonify({"message": "Clear confirmations", "ok":True}), 200
            else:
                # Handle case where the ride does not exist
                print(f"Ride with id {ride_id} does not exist.")
                return jsonify({"message": "Ride does not exist", "ok":False}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()

def get_current_package(userId=None):
    print(userId)
    session = Session()
    try:
        my_packages = myPackages(userId)

        print(my_packages)

        current_packages = []

        for package in my_packages:
            if package[20] != 1:
                current_packageDetails = format_packageDetails(package)

                current_packages.append(current_packageDetails)
        return current_packages
    
    except SQLAlchemyError as e:
        print(f"Error retrieving current my rides (packages): {e}")
        return jsonify({"error": "Failed to retrieve current my rides (packages)"}), 500

    finally:
        if session:
            session.close()

def get_finished_package(userId=None):
    print(userId)
    try:
        my_packages = myPackages(userId)

        finished_packages = []

        for package in my_packages:
            if package[20] == 1:
                finished_packageDetails = format_packageDetails(package)

                finished_packages.append(finished_packageDetails)
        return finished_packages
    
    except SQLAlchemyError as e:
        print(f"Error retrieving finished my rides (packages): {e}")
        return jsonify({"error": "Failed to retrieve finished my rides (packages)"}), 500

def delete_ride(rideId=None):
    print(rideId)
    session = Session()

    try:
        # Query the database to find the ride with the given IDfor ride_data in body:
        rideStatus = session.query(RideStatus).filter(RideStatus.ride_id == rideId).first()
        ride = session.query(CargoRide).filter(CargoRide.id == rideId).first()
        cargo = session.query(Cargo).filter(Cargo.ride_id == rideId).first()
            
        if ride and rideStatus:
            session.delete(rideStatus)
            session.commit()

            session.delete(cargo)
            session.commit()
        
            session.delete(ride)
            session.commit()

            return jsonify({"message": "Ride deleted successfully"}), 204
        else:
            return jsonify({"message": "Ride not found"}), 404

    except SQLAlchemyError as e:
        session.rollback()  
        print(f"Error deleting ride: {e}")
        return False, 500
    
    finally:
        session.close()

def pickup_drop_details(rideId=None):
    print(rideId)
    session = Session()

    try:
        ride_details = session.query(
            UserType.user_type, User.fname, User.photo, CargoRide.contact_recipient, 
            CargoRide.date, CargoRide.package_type, CargoRide.weight, Cargo.height,
            Cargo.length, Cargo.width, CargoRide.truck_type,
            CargoRide.location, CargoRide.destination, CargoRide.plat, CargoRide.plon,
            CargoRide.dlat, CargoRide.dlon, CargoRide.id, CargoRide.driver_id,
            RideStatus.driver_confirmation, RideStatus.cf_confirmation,
            RideStatus.finished, User.phone, User.lname, RideStatus.driver_rejection,
            RideStatus.cf_rejection, CargoRide.special_request, CargoRide.cost, CargoRide.user_id
            )\
            .join(User, UserType.user_id == User.id) \
            .join(CargoRide, CargoRide.user_id == User.id) \
            .join(RideStatus, RideStatus.ride_id == CargoRide.id) \
            .join(Cargo, Cargo.ride_id == CargoRide.id) \
            .filter(CargoRide.id == rideId)\
            .all()

        print("ride", ride_details)
        
        session.commit()

        ride_details_list = []

        for ride in ride_details:
            if ride[21] != 1:
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
                    'cost' : ride[27], 'user_id': ride[28]
                }
            ride_details_list.append(ride_dict)
        return ride_details_list
    
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching ride details {rideId}: {e}"), 500
        return {}

    finally:
        session.close()

def update_finished(rideId=None):
    
    print(rideId)
    session = Session()

    try:
        rideStatus = session.query(RideStatus).filter(RideStatus.ride_id == rideId).first()
        ride = session.query(CargoRide).filter(CargoRide.id == rideId).first()
        
        # Check if the ride exists
        if ride:
            # Update the cf rejection and driver id
            rideStatus.finished = 1
            session.commit()
            return jsonify({"message": " Ride Finished", "ok":True}), 200
        else:
            # Handle case where the ride does not exist
            print(f"Ride with id {rideId} does not exist.")
            return jsonify({"message": "Ride does not exist", "ok":False}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()

def update_pickup(rideId=None):
    
    print(rideId)
    session = Session()

    try:
        rideStatus = session.query(RideStatus).filter(RideStatus.ride_id == rideId).first()
        ride = session.query(CargoRide).filter(CargoRide.id == rideId).first()
        
        # Check if the ride exists
        if ride:
            # Update the cf rejection and driver id
            rideStatus.finished = 3
            session.commit()
            return jsonify({"message": " Package picked up", "ok":True}), 200
        else:
            # Handle case where the ride does not exist
            print(f"Ride with id {rideId} does not exist.")
            return jsonify({"message": "Ride does not exist", "ok":False}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()

def send_special_request(body):

    print(body)

    rideId = body.get('rideId')
    driver_id = body.get('driver_id')

    session = Session()

    try:
        rideStatus = session.query(RideStatus).filter(RideStatus.ride_id == rideId).first()
        ride = session.query(CargoRide).filter(CargoRide.id == rideId).first()
        
        if ride:

            rideStatus.cf_confirmation = 1
            ride.driver_id = driver_id
            ride.special_request = 1
            session.commit()
            return jsonify({"message": "Special Request sent", "ok":True}), 200
        else:

            print(f"Ride with id {rideId} does not exist.")
            return jsonify({"message": "Ride does not exist", "ok":False}), 404

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"Internal server error. Please try again later. Error: {e}"}), 500
    finally:
        session.close()


def myPackages(userId):
    print(userId)
    session = Session()

    try:
        
        # all_rides = session.query(CargoRide).all()
        my_packages = session.query(
            User.fname, User.photo, CargoRide.contact_recipient, 
            CargoRide.date, CargoRide.package_type, CargoRide.weight, Cargo.height,
            Cargo.length, Cargo.width, CargoRide.truck_type,
            CargoRide.location, CargoRide.destination, CargoRide.plat, CargoRide.plon,
            CargoRide.dlat, CargoRide.dlon, CargoRide.id, CargoRide.driver_id,
            RideStatus.driver_confirmation, RideStatus.cf_confirmation,
            RideStatus.finished, User.phone, User.lname, RideStatus.driver_rejection,
            RideStatus.cf_rejection, CargoRide.special_request, CargoRide.cost
            )\
            .select_from(CargoRide) \
            .outerjoin(User, CargoRide.driver_id == User.id) \
            .join(RideStatus, RideStatus.ride_id == CargoRide.id) \
            .join(Cargo, Cargo.ride_id == CargoRide.id) \
            .filter(CargoRide.user_id == userId) \
            .all()
        
        session.commit()
        return my_packages
    
    except SQLAlchemyError as e:
        # Handle any database-related errors
        print(f"Error fetching all rides for Cargo finder ID {userId}: {e}"), 500
        return {}

    finally:
        session.close()

def format_packageDetails(package):
    return {
        'id': package[16], 'contact_recipient': package[2], 'date': package[3],
        'package_type': package[4], 'weight': package[5], 'height': package[6],
        'length': package[7], 'width': package[8], 'truck_type': package[9],
        'photo': package[1], 'location': package[10], 'destination': package[11],
        'plat': package[12], 'plon': package[13], 'dlat': package[14],
        'dlon': package[15], 'fname': package[0],'lname': package[22], 
        'phone': package[21], 'driver_id': package[17], 
        'driver_confirmation': package[18], 'cf_confirmation': package[19], 
        'finished': package[20],'driver_rejection': package[23], 
        'cf_rejection': package[24], 'special_request': package[25],
        'cost': package[26],
    }

def get_packageId():
    session = Session()

    # Use SQLAlchemy select to query all Rides objects
    last_OrderId = session.query(CargoRide).order_by(CargoRide.id.desc()).first()

     # Close the session
    session.close()

    # Check if a ride was found
    if last_OrderId:
        return last_OrderId.id
    else:
        return None  # Return None if no ride was found


def getDriverIdByOrderId(orderId=None):
    session = Session()
    try:
        cargo_ride = session.query(CargoRide).filter_by(id=orderId).first()
        if not cargo_ride:
            return jsonify({'message': 'Order not found'}), 404
        driver_id = cargo_ride.driver_id
        return jsonify({'driverId': driver_id}), 200
    except Exception as e:
        return jsonify({'message': 'Internal server error. Please try again later.', 'error': str(e)}), 500
