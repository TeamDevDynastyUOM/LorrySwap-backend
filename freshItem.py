from flask import jsonify
from sqlalchemy.orm import joinedload
from app.models import FreshItem, Item, EconomicCenter, User, Order
from database import Session
from collections import defaultdict
from datetime import datetime
from flask import request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func


def create_fresh_item(seller_id, body):
    session = Session()
    try:
        name = body.get("name")
        weight = body.get("weight")
        date_str = body.get("date")
        additionalNote = body.get("additionalNote")
        seller_id = seller_id
        economic_center_id = body.get("value")

        date = datetime.fromisoformat(date_str).replace(hour=0, minute=0, second=0, microsecond=0)

        fresh_item = (
            session.query(FreshItem)
            .filter(
                FreshItem.date == date,
                FreshItem.name == name,
                FreshItem.economic_center_id == economic_center_id,
                FreshItem.seller_id == seller_id,
            )
            .first()
        )

        if fresh_item:
            fresh_item.weight += weight
        else:
            new_item = FreshItem(
                name=name,
                weight=weight,
                date=date,
                additionalNote=additionalNote,
                seller_id=seller_id,
                economic_center_id=economic_center_id,
            )
            session.add(new_item)

        session.commit()

        return (
            jsonify(
                {
                    "success": "Fresh item created/updated successfully",
                }
            ),
            200,
        )

    except Exception as e:
        session.rollback()
        print(e)
        return jsonify({"error": "Failed to create fresh item"}), 500

    finally:
        session.close()


def read_freshItem_for_seller(seller_id):
    session = Session()
    try:
        today_date = datetime.now().date()

        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.item))
            .options(joinedload(FreshItem.economicCenter))
            .filter(FreshItem.seller_id == seller_id)
            .filter(FreshItem.date >= today_date)
            .all()
        )

        serialized_items = []
        for item in fresh_items:
            serialized_item = {
                "id": item.id,
                "weight": item.weight,
                "date": item.date.strftime("%Y-%m-%d"),
                "additionalNote": item.additionalNote,
                "economic_center_name": (
                    item.economicCenter.name if item.economicCenter else None
                ),
                "name": item.item.name,
                "economic_center_id": item.economic_center_id,
                "additionalNote": item.additionalNote,
                "image": item.item.image,
            }
            serialized_items.append(serialized_item)

        return serialized_items

    except Exception as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        session.close()


def read_freshItem_on_date(date):
    session = Session()
    try:
        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(date=date)
            .all()
        )
        print ("fresh items are" , fresh_items)
        total_weight = defaultdict(int)
        total_order = defaultdict(int)

        for item in fresh_items:
            if item.weight is not None:
                total = (
                    item.economicCenter.id,
                    item.item.id,
                    item.name,
                    item.item.image,
                    item.date,
                    item.item.name,
                )
                total_weight[total] += item.weight

        orders = session.query(Order).filter_by(dueDate=date).all()

        for order in orders:
            order_key = (order.economicCenter.id, order.item.id, order.dueDate)
            total_order[order_key] += order.quantity

        serialized_items = []

        for total in total_weight:
            order_key = (total[0], total[1], total[4])  
            total_remain = total_weight[total] - total_order.get(order_key, 0)
            serialized_item = {
                "total_weight": total_weight[total],
                "economic_center_id": total[0],
                "name": total[5],
                "item_id": total[1],
                "total_remain": total_remain,
                "seller_id": fresh_items[0].seller_id,  
                "image": total[3],
            }
            serialized_items.append(serialized_item)
            print(serialized_item)

        return serialized_items

    except SQLAlchemyError as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def read_freshItem_for_ec_on_date(date, economic_center_id):
    session = Session()
    try:
        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(economic_center_id=economic_center_id)
            .options(joinedload(FreshItem.item))
            .filter_by(date=date)
            .all()
        )

        total_weight = defaultdict(int)
        total_order = defaultdict(int)

        for item in fresh_items:
            if item.weight is not None:
                total = (
                    item.economicCenter.id,
                    item.item.id,
                    item.name,
                    item.item.image,
                    item.date,
                    item.item.name,
                )
                total_weight[total] += item.weight

        orders = (
            session.query(Order)
            .filter_by(economic_center_id=economic_center_id)
            .filter_by(dueDate=date)
            .all()
        )

        for order in orders:
            order_key = (order.economicCenter.id, order.item.id, order.dueDate)
            total_order[order_key] += order.quantity

        if not orders:
            print(
                f"No orders found for economic_center_id={economic_center_id} on date={date}"
            )

        serialized_items = []

        for total in total_weight:
            order_key = (total[0], total[1], total[4]) 
            total_remain = total_weight[total] - total_order.get(order_key, 0)
            serialized_item = {
                "total_weight": total_weight[total],
                "economic_center_id": total[0],
                "name": total[5],
                "item_id": total[1],
                "total_remain": total_remain,
                "seller_id": item.seller_id, 
                "image": total[3],
            }
            print(serialized_item)
            serialized_items.append(serialized_item)

        return serialized_items

    except SQLAlchemyError as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def read_freshItem_for_item_on_date(name, date):
    session = Session()
    try:
        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(name=name)
            .filter_by(date=date)
            .all()
        )

        total_weight = defaultdict(int)

        for item in fresh_items:
            total = (item.economicCenter.id, item.id, item.date)
            total_weight[total] += item.weight

        serialized_items = []

        for total in total_weight:
            serialized_item = {
                "name": total[1],
                "seller_id": item.seller_id,
                "phone": item.seller.phone,
                "total_weight": total_weight[total],
                "economic_center_id": item.economicCenter.id,
                "item_id": item.name,
                "image": item.item.image,
            }
            serialized_items.append(serialized_item)

        return serialized_items

    except SQLAlchemyError as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def read_ec_seller_list(date, economic_center_id, name):
    session = Session()
    try:
        # Query all FreshItems for the given date and economic center
        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(economic_center_id=economic_center_id)
            .filter_by(date=date)
            .filter_by(name=name)
            .all()
        )

        total_weight = defaultdict(int)
        total_order = defaultdict(int)

        for item in fresh_items:
            if item.weight is not None:
                total = (
                    item.economicCenter.id,
                    item.item.id,
                    item.seller_id,
                    item.name,
                    item.date,
                    item.item.name,
                    item.seller.fname,
                    item.seller.lname,
                    item.seller.phone,
                    item.additionalNote,
                    item.item.image,
                )
                total_weight[total] += item.weight

        # Query all Orders for the given date and economic center
        orders = (
            session.query(Order)
            .options(joinedload(Order.item))
            .options(joinedload(Order.economicCenter))
            .options(joinedload(Order.seller))
            .filter_by(economic_center_id=economic_center_id)
            .filter_by(dueDate=date)
            .filter_by(name=name)
            .all()
        )

        # Calculate the total order quantity
        for order in orders:
            order_key = (
                order.economicCenter.id,
                order.item.id,
                order.seller_id,
                order.dueDate,
            )
            total_order[order_key] += order.quantity

        serialized_items = []

        # Create the serialized items list
        for total in total_weight:
            order_key = (total[0], total[1], total[2], total[4])  # Matching keys
            total_remain = total_weight[total] - total_order.get(order_key, 0)

            serialized_item = {
                "name": total[5],
                "fname": total[6],
                "lname": total[7],
                "contact": total[8],
                "total_weight": total_weight[total],  # Include total_weight here
                "economic_center_id": total[0],
                "item_id": total[1],
                "total_remain": total_remain,
                "additionalNote": total[9],
                "seller_id": total[2],
                "image": total[10],
            }
            serialized_items.append(serialized_item)

        return jsonify(serialized_items)

    except SQLAlchemyError as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def read_freshItem_for_ec_on_date_for_seller(seller_id, economic_center_id, date):
    session = Session()
    try:
        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(economic_center_id=economic_center_id)
            .filter_by(date=date)
            .all()
        )

        total_weight = defaultdict(int)
        contribution = defaultdict(int)
        percentage = {}

        for item in fresh_items:
            total = (item.economicCenter.id, item.item.name, item.date)
            total_weight[total] += item.weight

        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(economic_center_id=economic_center_id)
            .filter_by(date=date)
            .filter_by(seller_id=seller_id)
            .all()
        )

        for item in fresh_items:
            own_total = (
                item.economicCenter.id,
                item.item.name,
                item.date,
                item.seller_id,
            )
            contribution[own_total] += item.weight

        serialized_items = []

        for total in total_weight:
            for own_total in contribution:
                if own_total[0:3] == total:
                    if total_weight[total] != 0:
                        percentage[own_total] = round(
                            (contribution[own_total] / total_weight[total]) * 100, 2
                        )
                    else:
                        percentage[own_total] = 0
                    serialized_item = {
                        "name": own_total[1],
                        "total_weight": total_weight[total],
                        "contribution": contribution[own_total],
                        "percentage": percentage[own_total],
                        "economic_center_id": item.economicCenter.id,
                        "order": item.total_order,
                        "image": item.item.image,
                    }
                    serialized_items.append(serialized_item)

        return serialized_items

    except SQLAlchemyError as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def read_freshItem_for_date_for_seller(seller_id, date):
    session = Session()
    try:
        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(date=date)
            .all()
        )

        total_weight = defaultdict(int)
        contribution = defaultdict(int)
        percentage = {}

        for item in fresh_items:
            total = (item.economicCenter.id, item.item.name, item.date)
            total_weight[total] += item.weight

        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(date=date)
            .filter_by(seller_id=seller_id)
            .all()
        )

        for item in fresh_items:
            own_total = (
                item.economicCenter.id,
                item.item.name,
                item.date,
                item.seller_id,
            )
            contribution[own_total] += item.weight

        serialized_items = []

        for total in total_weight:
            for own_total in contribution:
                if own_total[0:3] == total:
                    if total_weight[total] != 0:
                        percentage[own_total] = round(
                            (contribution[own_total] / total_weight[total]) * 100, 2
                        )
                    else:
                        percentage[own_total] = 0
                    serialized_item = {
                        "name": own_total[1],
                        "total_weight": total_weight[total],
                        "contribution": contribution[own_total],
                        "percentage": percentage[own_total],
                        "economic_center_id": own_total[0],  # fixed to use own_total
                        "order": item.total_order,
                        "image": item.item.image,
                    }
                    serialized_items.append(serialized_item)

        return serialized_items

    except SQLAlchemyError as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def read_freshItem_for_ec_on_date_name_for_EC_id_seller(
    date, economic_center_id, name, seller_id
):
    session = Session()
    try:
        fresh_items = (
            session.query(FreshItem)
            .options(joinedload(FreshItem.seller))
            .options(joinedload(FreshItem.economicCenter))
            .options(joinedload(FreshItem.item))
            .filter_by(economic_center_id=economic_center_id)
            .filter_by(date=date)
            .filter_by(name=name)
            .filter_by(seller_id=seller_id)
            .all()
        )

        total_weight = defaultdict(int)
        total_order = defaultdict(int)

        for item in fresh_items:
            if item.weight is not None:
                total = (
                    item.economicCenter.id,
                    item.item.id,
                    item.seller_id,
                    item.name,
                    item.date,
                    item.item.name,
                    item.seller.fname,
                    item.seller.lname,
                    item.seller.phone,
                    item.additionalNote,
                    item.item.image,
                    item.id,
                )
                total_weight[total] += item.weight

        orders = (
            session.query(Order)
            .options(joinedload(Order.item))
            .options(joinedload(Order.economicCenter))
            .options(joinedload(Order.seller))
            .filter_by(economic_center_id=economic_center_id)
            .filter_by(dueDate=date)
            .filter_by(name=name)
            .filter_by(seller_id=seller_id)
            .all()
        )

        for order in orders:
            order_key = (
                order.economicCenter.id,
                order.item.id,
                order.seller_id,
                order.dueDate,
            )
            total_order[order_key] += order.quantity

        serialized_items = []

        for total in total_weight:
            order_key = (total[0], total[1], total[2], total[4]) 
            total_remain = total_weight[total] - total_order.get(order_key, 0)

            serialized_item = {
                "name": total[5],
                "fname": total[6],
                "lname": total[7],
                "contact": total[8],
                "total_weight": total_weight[total],
                "economic_center_id": total[0],
                "item_id": total[1],
                "total_remain": total_remain,
                "additionalNote": total[9],
                "seller_id": total[2],
                "id": total[11],
                "date": total[4],
            }

            serialized_items.append(serialized_item)

        return jsonify(serialized_items)

    except SQLAlchemyError as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def update_freshItem_for_ec_on_date_for_seller(id):
    session = Session()
    try:
        data = request.get_json()
        weight = data.get("weight")
        additionalNote = data.get("additionalNote")

        # Fetch the FreshItem by id
        fresh_item = session.query(FreshItem).filter_by(id=id).first()
        if not fresh_item:
            return jsonify({"error": "Fresh item not found"}), 404

        # Update the attributes
        if weight is not None:
            fresh_item.weight = weight
        if additionalNote is not None:
            fresh_item.additionalNote = additionalNote

        # Commit the changes to the database
        session.commit()

        return jsonify({"message": "Fresh item updated successfully"}), 200

    except SQLAlchemyError as e:
        print(f"Error updating fresh item: {e}")
        session.rollback()
        return jsonify({"error": "Failed to update fresh item"}), 500

    finally:
        session.close()


def delete_freshItem_for_seller(id):
    session = Session()
    try:
        fresh_item = session.query(FreshItem).filter_by(id=id).first()
        if not fresh_item:
            return jsonify({"error": "Fresh item not found"}), 404

        session.delete(fresh_item)
        session.commit()

        return jsonify({"message": "Fresh item deleted successfully"}), 200

    except SQLAlchemyError as e:
        print(f"Error deleting fresh item: {e}")
        session.rollback()
        return jsonify({"error": "Failed to delete fresh item"}), 500

    finally:
        session.close()
