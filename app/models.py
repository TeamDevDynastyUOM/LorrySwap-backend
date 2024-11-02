from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Boolean, INTEGER, func, Text, DATE, Float, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# this is the base class for the models and it is used to create the tables in the database
base = declarative_base()
metadata = base.metadata

class User(base):
    # table name should be here
    __tablename__ = 'user'

    # all the columns and their properties should be here 
    id = Column(Integer, primary_key=True)
    fname = Column(String(50), nullable=False)
    lname = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False ,unique=True)
    phone = Column(String(12), nullable=False ,unique=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(1), nullable=False)
    nic = Column(String(15), nullable=False ,unique=True)
    created_at = Column(DateTime, server_default=func.now())
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(256), nullable=False)
    verified = Column(Boolean, default=False)
    photo = Column(String(500), nullable=True)

    def __repr__(self):
        return f"id={self.id}, fname={self.fname}, lname={self.lname}, email={self.email}, phone={self.phone}, age={self.age}, gender={self.gender}, nic={self.nic}, user_type={self.user_type}"


class TempUser(base):
    __tablename__ = 'temp_user'
    email = Column(String(255), primary_key=True)
    otp = Column(Integer, nullable=False)
    fname = Column(String(255), nullable=False)
    lname = Column(String(255), nullable=False)
    contact_no = Column(String(20), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(1), nullable=False)
    nic = Column(String(20), nullable=False)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    roles = Column(String(255), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


class Driver(base):
    __tablename__ = 'driver'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)
    Organization_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    residence = Column(String(50), nullable=False)
    licence_side1 = Column(String(500), nullable=True, unique=True)
    licence_side2 = Column(String(500), nullable=True, unique=True)
    Vehicleno = Column(String(8), ForeignKey('vehicle.Vehicleno') , nullable=True)
    verify = Column(Integer, nullable=False, server_default="2")


class DriverLocation(base):
    __tablename__ = 'driverlocation'

    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)


class Vehicle(base):
    __tablename__ = 'vehicle'

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    Vehicleno = Column(String(8), nullable=False ,unique=True)
    brand = Column(String(30), nullable=False)
    model = Column(String(30), nullable=False)
    type = Column(String(30), nullable=False)
    length = Column(String(10), nullable=False)
    width = Column(String(10), nullable=False)
    height = Column(String(10), nullable=False)
    tonnage = Column(String(10), nullable=False)
    verify = Column(Integer, nullable=False, server_default="2")

# class Owner(base):
#     __tablename__ = 'owner'

#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

class Authentication(base):
    __tablename__ = 'authentication'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    token = Column(Text, nullable=False) 
    created_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, onupdate=func.now()) 
    is_active = Column(Boolean, default=True)
    token_type = Column(String(50), nullable=True) 

    def __repr__(self):
        return f"<Authentication(id={self.id}, user_id={self.user_id}, token_type={self.token_type}, is_active={self.is_active})>"


# this is the user type model and it represents the user type table in the database
class UserType(base):
    __tablename__ = 'user_type'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_type = Column(String(50), nullable=False)


class Ride(base):
    __tablename__ = "ride"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    location = Column(String(300), nullable=False)
    destination = Column(String(300), nullable=False)
    location_lat = Column(String(50), nullable=False)
    location_lon = Column(String(50), nullable=False)
    destination_lat = Column(String(50), nullable=False)
    destination_lon = Column(String(150), nullable=False)
    date = Column(DATE, nullable=False)
    time = Column(String(150), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    finished_ride = Column(Integer, nullable=False, server_default='0')


class Cargo(base):
    __tablename__ = "cargo"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    ride_id = Column(Integer, ForeignKey('cargoRide.id'), nullable=False)
    height = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    width = Column(Float, nullable=False)

class CargoRide(base):
    __tablename__ = "cargoRide"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    contact_recipient = Column(String(15), nullable=False)
    date = Column(DATE, nullable=False)
    package_type = Column(String(50), nullable=False)
    weight = Column(Float, nullable=False)
    truck_type = Column(String(50), nullable=False)
    location = Column(String(120), nullable=False)
    destination = Column(String(120), nullable=False)
    plat = Column(String(50), nullable=False)
    plon = Column(String(50), nullable=False)
    dlat = Column(String(50), nullable=False)
    dlon = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    driver_id = Column(Integer, ForeignKey('user.id'), nullable=True, server_default=None)
    special_request = Column(Boolean, nullable=False, server_default='false')
    cost = Column(Float, nullable=False, server_default='0.0')

    def __str__(self):
        return (
            f"CargoRide("
            f"id={self.id}, "
            f"contact_recipient={self.contact_recipient}, "
            f"date={self.date}, "
            f"package_type={self.package_type}, "
            f"weight={self.weight}, "
            f"height={self.height}, "
            f"length={self.length}, "
            f"width={self.width}, "
            f"truck_type={self.truck_type}, "
            f"location={self.location}, "
            f"destination={self.destination}, "
            f"plat={self.plat}, "
            f"plon={self.plon}, "
            f"dlat={self.dlat}, "
            f"dlon={self.dlon}, "
            f"user_id={self.user_id}, "
            f"driver_id={self.driver_id}, "
            f")"
        )

class RideStatus(base):
    __tablename__ = "rideStatus"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    ride_id = Column(Integer, ForeignKey('cargoRide.id'), nullable=False)
    driver_confirmation = Column(Boolean, nullable=False, server_default='false')
    cf_confirmation = Column(Boolean, nullable=False, server_default='false')
    driver_rejection = Column(Boolean, nullable=False, server_default='false')
    cf_rejection = Column(Boolean, nullable=False, server_default='false')
    finished = Column(Integer, nullable=False, server_default='0')

# this is the package details model and it represents the package details in the database
# class PackageDetails(base):
#     _tablename_ = 'package_details'
#
#     id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
#     user_type = Column(String(50), nullable=False)
#     package_type = Column(String(20), nullable=False)
#     weight = Column(Integer, nullable=False)
#     height = Column(Integer, nullable=False)
#     length = Column(Integer, nullable=False)
#     width = Column(Integer, nullable=False)
#     truck_type = Column(String(10), nullable=False)
#     photo = Column(String(255),)
#     plat = Column(String(50), nullable=False)
#     plon = Column(String(50), nullable=False)
#     dlat = Column(String(50), nullable=False)
#     dlon = Column(String(50), nullable=False)
#     # user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
#     location = Column(String(15))
#     destination = Column(String(15))

class Review(base):
    __tablename__ = "review"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    ride_id = Column(Integer, ForeignKey("cargoRide.id"), nullable=False)
    sender = Column(Integer, ForeignKey("user.id"), nullable=False)
    receiver = Column(Integer, ForeignKey("user.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String(50), nullable=True)
    comment = Column(String(200), nullable=True)
    date = Column(DateTime, default=func.now(), nullable=False)


class EconomicCenter(base):
    __tablename__ = "economicCenter"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    longitude = Column(String(100))
    latitude = Column(String(100))


class Item(base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    image = Column(String(100))

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
        }


class FreshItem(base):
    __tablename__ = "freshItem"

    id = Column(Integer, primary_key=True, autoincrement=True)
    weight = Column(Integer)
    date = Column(DateTime)
    additionalNote = Column(String(200))

    seller_id = Column(Integer, ForeignKey("user.id"))
    seller = relationship("User")

    economic_center_id = Column(Integer, ForeignKey("economicCenter.id"))
    economicCenter = relationship("EconomicCenter")

    name = Column(Integer, ForeignKey("item.id"))
    item = relationship("Item")

    total_order = Column(Integer)


class Order(base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime)
    quantity = Column(Integer)
    dueDate = Column(DateTime)

    economic_center_id = Column(Integer, ForeignKey("economicCenter.id"))
    economicCenter = relationship("EconomicCenter")

    name = Column(Integer, ForeignKey("item.id"))
    item = relationship("Item")

    seller_id = Column(Integer, ForeignKey("user.id"))
    seller = relationship("User")

    buyer_id = Column(Integer)

    cargo_ride_id = Column(Integer, ForeignKey("cargoRide.id"), nullable=True)
    CargoRide = relationship("CargoRide")


class EC_Seller(base):
    __tablename__ = 'Economic_center_seller'

    id = Column(Integer, autoincrement=True, primary_key=True)
    EC_seller_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    verified = Column(Integer, nullable=False, server_default="0")


# this is the driver reject model it represents reject driver table in the database
class Driver_Reject(base):
    __tablename__ = 'driver_reject'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    driver_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    rejected_reason = Column(String(500), nullable=False)
