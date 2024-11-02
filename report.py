from database import Session
from sqlalchemy import func, extract
from flask import jsonify
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError
from app.models import Order, EconomicCenter, Item
from sqlalchemy.orm import joinedload


def create_report(economic_center_id, name, year):
    session = Session()
    try:
        if not year or not economic_center_id or not name:
            return jsonify({"message": "Missing required parameters"}), 400

        # Query to fetch orders for the given economic_center_id, item name, and year
        orders = (
            session.query(Order)
            .options(joinedload(Order.economicCenter), joinedload(Order.item))
            .filter(
                Order.economic_center_id == economic_center_id,
                Order.name == name,
                extract("year", Order.dueDate) == year,
            )
            .all()
        )

        monthly_report = defaultdict(int)
        annual_report = defaultdict(int)

        for order in orders:
            month_key = (
                order.dueDate.month,
                order.item.name,
                order.economicCenter.name,
                order.dueDate.year,
            )
            monthly_report[month_key] += order.quantity
            year_key = (order.dueDate.year, order.item.name, order.economicCenter.name)
            annual_report[year_key] += order.quantity

        serialized_monthly_orders = []
        serialized_annual_orders = []

        for month_key, quantity_monthly in monthly_report.items():
            order_monthly = {
                "month": month_key[0],
                "year": month_key[3],
                "item": month_key[1],
                "economic_center_name": month_key[2],
                "quantity": quantity_monthly,
            }
            serialized_monthly_orders.append(order_monthly)

        for year_key, quantity_annual in annual_report.items():
            order_annual = {
                "year": year_key[0],
                "item": year_key[1],
                "economic_center_name": year_key[2],
                "quantity": quantity_annual,
            }
            serialized_annual_orders.append(order_annual)

        return (
            jsonify(
                {
                    "monthly_report": serialized_monthly_orders,
                    "annual_report": serialized_annual_orders,
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        return jsonify({"message": str(e)}), 500

    finally:
        session.close()
