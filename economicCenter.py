from flask import jsonify
from database import Session
from app.models import EconomicCenter


def read_all_economic_centers():
    # Start the session to interact with the database
    session = Session()

    try:
        # Query all EconomicCenter objects and retrieve their names
        economic_centers = session.query(EconomicCenter).all()

        # Serialize the list of EconomicCenter objects to JSON
        economic_centers_json = [
            {"id": center.id, "name": center.name} for center in economic_centers
        ]

        return jsonify(economic_centers_json)
    except Exception as e:
        # Return error response if an exception occurs
        return (
            jsonify({"error": "Failed to fetch economic centers", "details": str(e)}),
            500,
        )
    finally:
        session.close()


def insert_ecseller(userId):
    session = Session()
    try:
        # Extract values from the request body
        owner_user_id = userId 

        # Debugging: Print extracted values
        print(f"Owner User ID: {owner_user_id}")

        # Check if owner_user_id is provided
        if not owner_user_id:
            return jsonify({"error": "UserID is required"}), 400

        # Check if the user already exists in the database
        owner = session.query(EC_Seller).filter_by(EC_seller_id=owner_user_id).first()

        if owner:
            session.rollback()
            return jsonify({"error": "ecseller is already in the database"}), 401

        # Create new owner instance
        new_ecseller = EC_Seller(
            EC_seller_id=owner_user_id
        )

        session.add(new_ecseller)
        session.commit()  # Commit to save the new owner

        return jsonify({"success": "ecseller added successfully"}), 201

    except Exception as e:
        session.rollback()
        print(e)
        return jsonify({"error": "Failed to add ecseller"}), 500

    finally:
        session.close()        
