from flask import jsonify
from app.models import FreshItem, Item
from database import Session


def read_all_fruit_items():
    # Start the session to interact with the database
    session = Session()

    try:
        # Get all the fruits from the database
        fruits = session.query(Item).filter(Item.type == "fruit").all()

        # Serialize the fruits data
        fruits_data = [fruit.serialize() for fruit in fruits]

        return jsonify({"fruits": fruits_data}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while getting the fruits"}), 500

    finally:
        # Close the session
        session.close()


def read_all_vegetable_items():
    # Start the session to interact with the database
    session = Session()

    try:
        # Get all the vegetables from the database
        vegetables = session.query(Item).filter(Item.type == "vegetable").all()

        # Serialize the vegetables data
        vegetables_data = [vegetable.serialize() for vegetable in vegetables]

        return jsonify({"vegetables": vegetables_data}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while getting the vegetables"}), 500

    finally:
        # Close the session
        session.close()


def read_all_leaf_items():
    # Start the session to interact with the database
    session = Session()

    try:
        # Get all the leaf from the database
        leaf = session.query(Item).filter(Item.type == "leaf").all()

        # Serialize the leaf data
        leaf_data = [leaf_item.serialize() for leaf_item in leaf]

        return jsonify({"leaf": leaf_data}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while getting the leaf"}), 500

    finally:
        # Close the session
        session.close()


def read_all_items():
    session = Session()

    try:
        items = session.query(Item).all()
        items_data = [item.serialize() for item in items]

        return jsonify({"items": items_data}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while getting the items"}), 500

    finally:
        session.close()
