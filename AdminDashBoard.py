from flask import jsonify, request
from app.models import User, UserType, Driver, Driver_Reject, EC_Seller, CargoRide, RideStatus, Review
from database import Session
from sqlalchemy import func

def get_pending_user():
    session = Session()


    # try:
    #     # Query for unverified users (verified == 0)
    #     unverified_users = session.query(
    #         User.id,
    #         User.fname,
    #         User.lname,
    #         User.nic,
    #         UserType.user_type
    #
    #     ).distinct().outerjoin(
    #         UserType, User.id == UserType.user_id
    #     ).filter(
    #         User.verified == 0
    #     ).all()
    #
    #     # Create a list to store user data
    #     pending_users = []
    #
    #
    #     for user in unverified_users:
    #         user_id, fname, lname, nic, user_type = user
    #
    #         user_data = {
    #             'id':user_id,
    #             'fname':fname,
    #             'lname':lname,
    #             'nic':nic,
    #             'user_type' :user_type if user_type else 'N/A'
    #         }
    #         pending_users.append(user_data)
    #     # pending_user_count = len(pending_users)
    #     print(pending_users)
    #     return jsonify(pending_users)


    #this is for modify table
    try:
        # Query for unverified users (verified == 0)
        unverified_users = session.query(
            User.id,
            User.fname,
            User.lname,
            User.nic,
            Driver.residence

        ).distinct().outerjoin(
            Driver, User.id == Driver.user_id
        ).filter(
            Driver.verify == 2
        ).all()

        # Create a list to store user data
        pending_users = []

        for user in unverified_users:
            user_id, fname, lname, nic, residence = user

            user_data = {
                'id': user_id,
                'fname': fname,
                'lname': lname,
                'nic': nic,
                'user_type': residence if residence else 'Driver'
            }
            pending_users.append(user_data)
        # pending_user_count = len(pending_users)
        print(pending_users)
        return jsonify(pending_users)

    except Exception as e:
        print(f"Error fetching pending user details: {e}")
        return jsonify({'error': 'Failed to fetch pending user details'})

    finally:
        session.close()


def varified_driver(user_id):

    print(user_id)

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    session = Session()

    try:
        # Find driver ID and update verified status
        driver = session.query(Driver).filter_by(user_id=user_id).first()
        if driver:
            driver.verify = 1
            session.commit()
            return jsonify({'message': 'User verified successfully'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        print(f"Error verifying user: {e}")
        return jsonify({'error': 'Failed to verify user'}), 500

    finally:
        session.close()


def reject_driver(user_id, reject_reason):

    if not user_id or not reject_reason:
        return jsonify({'error': 'User ID and reject reason are required'}), 400

    print(user_id, reject_reason)

    session = Session()

    try :
        # Update Driver table - set verified to 0
        driver = session.query(Driver).filter_by(user_id=user_id).first()
        if driver:
            driver.verify = 0
            session.commit()
        else:
            return jsonify({'error': 'Driver not found'}), 404

        # Create entry in DriverReject table
        driver_reject = Driver_Reject(driver_id=user_id, rejected_reason=reject_reason)
        session.add(driver_reject)
        session.commit()

        return jsonify({'message': 'Driver rejected successfully'}), 200

    except Exception as e:
        print(f"Error rejecting driver: {e}")
        session.rollback()
        return jsonify({'error': 'Failed to reject driver'}), 500

    finally:
        session.close()

def driver_details():
    session = Session()

    try:
        drivers=session.query(
            User.id,
            User.fname,
            User.lname,
            User.email,
            User.age,
            User.phone,
            User.nic,
            User.gender,
            Driver.verify
        ).join(Driver, User.id == Driver.user_id).all()

        # Create a list to store user data
        allDrivers = []

        for driver in drivers:
            user_id, fname, lname, email, age, phone, nic, gender, verify = driver

            user_data = {
                'id': user_id,
                'fname': fname,
                'lname': lname,
                'emai': nic,
                'age' : age,
                'phone': phone,
                'nic' : nic,
                'gender' : gender,
                'varified' : verify,
            }
            allDrivers.append(user_data)
        print(allDrivers)
        return jsonify(allDrivers)

    except Exception as e:
        print(f"Error fetching pending user details: {e}")
        return jsonify({'error': 'Failed to fetch pending user details'})

    finally:
        session.close()



def get_all_driver_data(id):
    session = Session()

    try:
        average_rating_subquery = session.query(
            func.avg(Review.rating).label('average_rating')
            ).filter(Review.receiver == id).subquery()

        driver = session.query(
            User.id,
            User.fname,
            User.lname,
            User.email,
            User.age,
            User.phone,
            User.nic,
            User.gender,
            Driver.verify,
            Driver.residence,
            average_rating_subquery.c.average_rating
        ).join(Driver, User.id == Driver.user_id).filter(User.id==id).first()

        if driver:
            user_data = {
                'id': driver.id,
                'fname': driver.fname,
                'lname': driver.lname,
                'email': driver.email,
                'age': driver.age,
                'phone': driver.phone,
                'nic': driver.nic,
                'gender': driver.gender,
                'verified': driver.verify,
                'residence': driver.residence,
                'average_rating': driver.average_rating if driver.average_rating is not None else 0
            }
            print(driver)
            return user_data
        else:
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        session.close()


def get_ec_seller():
    session = Session()

    try:
        ec_sellers = session.query(
            User.id,
            User.fname,
            User.lname,
            User.email,
            User.gender,
            User.nic,
            User.age,
            User.phone,
            EC_Seller.verified,
        ).join(EC_Seller, User.id == EC_Seller.EC_seller_id).all()

        # Creating a list to hold the results
        seller_details = []

        # Iterating over the results to format them into dictionaries
        for seller in ec_sellers:
            seller_info = {
                'id': seller.id,
                'fname': seller.fname,
                'lname': seller.lname,
                'email': seller.email,
                'phone': seller.phone,
                'age': seller.age,
                'gender': seller.gender,
                'nic': seller.nic,
                # 'created_at': seller.created_at,
                # 'username': seller.username,
                # 'user_verified': seller.user_verified,
                # 'photo': seller.photo,
                'verified': seller.verified
            }
            seller_details.append(seller_info)

        print(seller_details)
        return seller_details


    except Exception as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        session.close()


# def get_cargo_finder():
#     session = Session()
#
#     try:
#         cargo_finder = session.query(
#             User.id,
#             User.fname,
#             User.lname,
#             User.email,
#             User.gender,
#             User.nic,
#             EC_Seller.verified,
#         ).join(EC_Seller, User.id == EC_Seller.EC_seller_id).filter(EC_Seller.verified == '0').all()
#
#         # Creating a list to hold the results
#         cargo_finders = []
#
#         # Iterating over the results to format them into dictionaries
#         for c_finder in cargo_finder:
#             seller_info = {
#                 'id': c_finder.id,
#                 'fname': c_finder.fname,
#                 'lname': c_finder.lname,
#                 'email': c_finder.email,
#                 # 'phone': seller.phone,
#                 # 'age': seller.age,
#                 'gender': c_finder.gender,
#                 'nic': c_finder.nic,
#                 # 'created_at': seller.created_at,
#                 # 'username': seller.username,
#                 # 'user_verified': seller.user_verified,
#                 # 'photo': seller.photo,
#                 'verified': seller.verified
#             }
#             seller_details.append(seller_info)
#
#         print(seller_details)
#         return seller_details
#
#
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return []
#
#     finally:
#         session.close()

def get_ec_seller_details(user_id):
    session = Session()

    try:
        ec_seller = session.query(
            User.id,
            User.fname,
            User.lname,
            User.email,
            User.age,
            User.phone,
            User.nic,
            User.gender,
            User.created_at,
            EC_Seller.verified,
        ).join(EC_Seller, User.id == EC_Seller.EC_seller_id).filter(User.id==user_id).first()

        if ec_seller:
            user_data = {
                'id': ec_seller.id,
                'fname': ec_seller.fname,
                'lname': ec_seller.lname,
                'email': ec_seller.email,
                'age': ec_seller.age,
                'phone': ec_seller.phone,
                'nic': ec_seller.nic,
                'gender': ec_seller.gender,
                'verified': ec_seller.verified,
                'created':ec_seller.created_at
                # Add other fields as necessary
            }
            print(ec_seller)
            return user_data
        else:
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        session.close()

def verified_ec_seller(user_id):
    print(user_id)

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    session = Session()

    try:
        # Find driver ID and update verified status
        ec_seller = session.query(EC_Seller).filter_by(EC_seller_id=user_id).first()
        if ec_seller:
            ec_seller.verified = 1
            session.commit()
            return jsonify({'message': 'User verified successfully'}), 200
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        print(f"Error verifying user: {e}")
        return jsonify({'error': 'Failed to verify user'}), 500

    finally:
        session.close()

def get_cargo_finders():
    session = Session()

    try:
        cargo_finders = session.query(
            User.id,
            User.fname,
            User.lname,
            User.email,
            User.age,
            User.phone,
            User.nic,
            User.gender,
            User.created_at,
        ).join(UserType, User.id == UserType.user_id).filter(UserType.user_type == 'CF').all()

        if cargo_finders:
            user_data_list = []
            for cargo_finder in cargo_finders:
                user_data = {
                    'id': cargo_finder.id,
                    'fname': cargo_finder.fname,
                    'lname': cargo_finder.lname,
                    'email': cargo_finder.email,
                    'age': cargo_finder.age,
                    'phone': cargo_finder.phone,
                    'nic': cargo_finder.nic,
                    'gender': cargo_finder.gender,
                    'created_at': cargo_finder.created_at
                }
                user_data_list.append(user_data)

            print(user_data_list)
            return user_data_list


        else:
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        session.close()


def get_all_users_count():
    session = Session()

    try:
        users_count = session.query(User).count()
        return users_count
    except Exception as e:
        print(f"Error retrieving user count: {e}")
        return None
    finally:
        session.close()



# Query to get all cargo rides with their ride status
def cargo_ride_details():

    session = Session()

    try:
        cargo_rides_with_status = session.query(
            CargoRide.id,
            CargoRide.user_id,
            CargoRide.date,
            CargoRide.package_type,
            CargoRide.truck_type,
            CargoRide.weight,
            CargoRide.width,
            CargoRide.height,
            CargoRide.length,
            CargoRide.location,
            CargoRide.destination,
            CargoRide.special_request,
            RideStatus.driver_confirmation
        ).join(RideStatus, CargoRide.id == RideStatus.ride_id).all()

        if cargo_rides_with_status:
            cargo_ride_list = []
            for cargo_ride in cargo_rides_with_status:
                cargo_ride_data = {
                    'id': cargo_ride.id,
                    'user_id': cargo_ride.user_id,
                    'date': cargo_ride.date,
                    'package_type': cargo_ride.package_type,
                    'weight': cargo_ride.weight,
                    'height': cargo_ride.height,
                    'length': cargo_ride.length,
                    'width': cargo_ride.width,
                    'truck_type': cargo_ride.truck_type,
                    'location': cargo_ride.location,
                    'destination': cargo_ride.destination,
                    'special_request': cargo_ride.special_request,
                    'driver_confirmation': cargo_ride.driver_confirmation
                }
                cargo_ride_list.append(cargo_ride_data)

            print(cargo_ride_list)
            return cargo_ride_list
        else:
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        session.close()


def get_cargo_finder_details(user_id):
    session = Session()

    try:
        cargo_finder = session.query(
            User.id,
            User.fname,
            User.lname,
            User.email,
            User.age,
            User.phone,
            User.nic,
            User.gender,
            User.created_at,
        ).filter(User.id==user_id).first()

        if cargo_finder:
            user_data = {
                'id': cargo_finder.id,
                'fname': cargo_finder.fname,
                'lname': cargo_finder.lname,
                'email': cargo_finder.email,
                'age': cargo_finder.age,
                'phone': cargo_finder.phone,
                'nic': cargo_finder.nic,
                'gender': cargo_finder.gender,
                'created':cargo_finder.created_at
                # Add other fields as necessary
            }
            print(cargo_finder)
            return user_data
        else:
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        session.close()

def all_reviews():
    session = Session()

    try:
        reviews = session.query(
            Review.id,
            Review.ride_id,
            Review.sender,
            Review.receiver,
            Review.title,
            Review.comment,
            Review.date,
            Review.rating,
        ).all()

        if reviews:
            review_list =[]
            for review in reviews:
                review_data = {
                    'id': review.id,
                    'ride_id':review.ride_id,
                    'sender': review.sender,
                    'receiver': review.receiver,
                    'rating': review.rating,
                    'title': review.title,
                    'comment': review.comment,
                    'date': review.date
                }
                review_list.append(review_data)

            print(review_list)
            return review_list
        else:
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    finally:
        session.close()



