from flask import request, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from database import Session
from app.models import Order, User, FreshItem
from collections import defaultdict
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError


def create_order(buyer_id, body):
    session = Session()
    try:
        date = datetime.now()
        dueDate_str = body.get("dueDate")
        quantity = body.get("quantity")
        economic_center_id = body.get("economic_center_id")
        name = body.get("name")
        buyer_id = buyer_id
        seller_id = body.get("seller_id")

        dueDate = datetime.fromisoformat(dueDate_str).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        new_order = Order(
            date=date,
            dueDate=dueDate,
            quantity=quantity,
            economic_center_id=economic_center_id,
            name=name,
            buyer_id=buyer_id,
            seller_id=seller_id,
        )
        session.add(new_order)

        total_order = (
            session.query(func.sum(Order.quantity))
            .filter(
                Order.dueDate == dueDate,
                Order.economic_center_id == economic_center_id,
                Order.name == name,
                Order.seller_id == seller_id,
            )
            .scalar()
        )

        fresh_item = (
            session.query(FreshItem)
            .filter(
                FreshItem.date == dueDate,
                FreshItem.economic_center_id == economic_center_id,
                FreshItem.name == name,
                FreshItem.seller_id == seller_id,
            )
            .first()
        )

        if fresh_item:
            fresh_item.total_order = total_order

        session.commit()
        return jsonify({"success": "Order created successfully"}), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

    finally:
        session.close()


def read_order_for_ec_on_date(dueDate, buyer_id):
    session = Session()
    try:
        order = (
            session.query(Order)
            .options(joinedload(Order.economicCenter))
            .options(joinedload(Order.item))
            .filter(
                Order.dueDate == dueDate,
                Order.buyer_id == buyer_id,
            )
            .all()
        )

        total_order = defaultdict(int)

        for item in order:
            total = (
                item.economic_center_id,
                item.economicCenter.name,
                item.dueDate,
                item.buyer_id,
                item.item.name,
            )
            total_order[total] += item.quantity

        serialized_orders = []

        for total in total_order:
            serialized_order = {
                "date": total[2],
                "economic_center": total[1],
                "economic_center_id": total[0],
                "total_order": total_order[total],
                "name": total[4],
            }
            print(serialized_order)
            serialized_orders.append(serialized_order)

        return serialized_orders, 200

    except SQLAlchemyError as e:
        return jsonify({"message": str(e)}), 500

    finally:
        session.close()


def read_items_in_order(dueDate, economic_center_id, buyer_id):
    session = Session()
    try:
        orders = (
            session.query(Order)
            .options(joinedload(Order.item))
            .options(joinedload(Order.economicCenter))
            .options(joinedload(Order.seller))
            .filter(
                Order.dueDate == dueDate,
                Order.economic_center_id == economic_center_id,
                Order.buyer_id == buyer_id,
            )
            .all()
        )

        serialized_orders = []

        for order in orders:
            serialized_order = {
                "date": order.date,
                "brining_date": order.dueDate,
                "name": order.item.name,
                "item_id": order.name,
                "economic_center": order.economicCenter.name,
                "economic_center_id": order.economic_center_id,
                "seller": order.seller.fname + " " + order.seller.lname,
                "seller_id": order.seller_id,
                "total_order": order.quantity,
                "date": order.dueDate,
                "contact": order.seller.phone,
                "image": order.item.image,
                "id": order.id,
                "pickup_location": order.economicCenter.name,
                "plat": order.economicCenter.latitude,
                "plon": order.economicCenter.longitude,
                "buyer_id": order.buyer_id,
            }

            serialized_orders.append(serialized_order)

        return jsonify(serialized_orders), 200

    except SQLAlchemyError as e:
        return jsonify({"message": str(e)}), 500

    finally:
        session.close()


def update_order(id):
    session = Session()
    try:
        data = request.get_json()
        quantity = data.get("total_order")
        freshItem_id = data.get("freshItem_id")
        print(freshItem_id)

        order = session.query(Order).filter(Order.id == id).first()

        if order is None:
            return jsonify({"message": "Order not found"}), 404

        if quantity is not None:
            # Calculate the change in order quantity
            quantity_change = quantity - order.quantity
            order.quantity = quantity

            fresh_item = (
                session.query(FreshItem).filter(FreshItem.id == freshItem_id).first()
            )

            if fresh_item:
                # Update the total_order in FreshItem
                fresh_item.total_order += quantity_change

        session.commit()

        return (
            jsonify(
                {
                    "message": "Order updated successfully",
                    "order": {
                        "id": order.id,
                        "name": order.name,
                        "total_order": order.quantity,
                        "seller_id": order.seller_id,
                        "date": order.date,
                        "economic_center_id": order.economic_center_id,
                    },
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"message": str(e)}), 500

    finally:
        session.close()


def delete_order(id, freshItem_id):
    session = Session()
    try:
        order = session.query(Order).filter(Order.id == id).first()

        if order is None:
            return jsonify({"message": "Order not found"}), 404

        fresh_item = (
            session.query(FreshItem).filter(FreshItem.id == freshItem_id).first()
        )

        if fresh_item:
            fresh_item.total_order -= order.quantity

        session.delete(order)
        session.commit()
        return jsonify({"message": "Order deleted successfully"}), 200

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

    finally:
        session.close()
