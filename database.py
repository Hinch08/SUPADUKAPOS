from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, ForeignKey,cast,Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import hashlib

# ── Setup ──
engine = create_engine("postgresql://postgres:Hinchjack08@localhost/supaduka_db")
Base = declarative_base()
session = sessionmaker(bind=engine)()

# ── Models ──
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    products = relationship("Product", back_populates="owner")
    sales = relationship("Sale", back_populates="owner")
    stocks = relationship("Stock", back_populates="owner")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100))
    buying_price = Column(Integer)
    selling_price = Column(Integer)
    owner = relationship("User", back_populates="products")
    sales = relationship("Sale", back_populates="product")
    stock = relationship("Stock", back_populates="product")

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    pid = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    owner = relationship("User", back_populates="sales")
    product = relationship("Product", back_populates="sales")

class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    pid = Column(Integer, ForeignKey('products.id'))
    stock_quantity = Column(Integer)
    owner = relationship("User", back_populates="stocks")
    product = relationship("Product", back_populates="stock")

Base.metadata.create_all(engine)


# ── Password Helper ──
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ── User Functions ──
def register(username, email, password, confirm_password):
    if password != confirm_password:
        print("Passwords do not match.")
        return None
    if session.query(User).filter((User.username == username) | (User.email == email)).first():
        print("User already exists.")
        return None
    session.add(User(username=username, email=email, password_hash=hash_password(password)))
    session.commit()
    print(f"{username} registered.")
    return True

def login(username, password):
    user = session.query(User).filter(User.username == username).first()
    if not user:
        return None
    if hash_password(password) == user.password_hash:
        return user
    return None

def all_users():
    return session.query(User.id, User.username, User.email).all()

def delete_user(username):
    user = session.query(User).filter(User.username == username).first()
    if user:
        session.delete(user)
        session.commit()
        print(f"{username} deleted.")


# ── Product Functions ──
def add_product(user_id, name, buying_price, selling_price):
    session.add(Product(user_id=user_id, name=name,
                        buying_price=buying_price,
                        selling_price=selling_price))
    session.commit()
    print(f"{name} added.")

def all_products(user_id):
    return session.query(Product).filter(Product.user_id == user_id).all()

# This must be above your route
# Must be defined BEFORE the route
def delete_product(user_id, product_id):
    product = session.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user_id
    ).first()
    if product:
        session.delete(product)
        session.commit()
        print(f"Product {product_id} deleted.")
    else:
        print("Product not found or does not belong to you.")
        
# ── Sale Functions ──
def add_sale(user_id, pid, quantity):
    session.add(Sale(user_id=user_id, pid=pid, quantity=quantity))
    session.commit()
    print(f"Sale recorded.")

def all_sales(user_id):
    return session.query(
        Sale.id,
        Sale.quantity,
        Sale.created_at,
        Product.name.label("product_name")
    ).join(Product, Product.id == Sale.pid)\
     .filter(Sale.user_id == user_id)\
     .order_by(Sale.id.desc())\
     .all()

def delete_sale(user_id, sale_id):                           
    sale = session.query(Sale).filter(
        Sale.id == sale_id,
        Sale.user_id == user_id
    ).first()
    if sale:
        session.delete(sale)
        session.commit()
        print(f"Sale {sale_id} deleted.")

def sales_per_product(user_id):
    return session.query(
        Product.name,
        func.sum(Product.selling_price * Sale.quantity).label("total")
    ).join(Sale, Product.id == Sale.pid).filter(Sale.user_id == user_id).group_by(Product.name).all()

def sales_per_day(user_id):
    return session.query(
        cast(Sale.created_at, Date).label("day"),
        func.sum(Sale.quantity * Product.selling_price).label("total")
    ).join(Product, Product.id == Sale.pid).filter(Sale.user_id == user_id).group_by("day").all()


# ── Profit Functions ──
def profit_per_product(user_id):
    return session.query(
        Product.name,
        func.sum((Product.selling_price - Product.buying_price) * Sale.quantity).label('profit')
    ).join(Sale).filter(Sale.user_id == user_id).group_by(Product.name).all()

def profit_per_day(user_id):
    from sqlalchemy import cast, Date
    return session.query(
        cast(Sale.created_at, Date).label('day'),
        func.sum((Product.selling_price - Product.buying_price) * Sale.quantity).label('profit')
    ).join(Product).filter(Sale.user_id == user_id).group_by('day').all()


# ── Stock Functions ──
def add_stock(user_id, pid, quantity):
    session.add(Stock(user_id=user_id, pid=pid,
                      stock_quantity=quantity))
    session.commit()
    print(f"Stock added.")

def all_stocks(user_id):                                     
    return session.query(Stock).filter(Stock.user_id == user_id).all()

def delete_stock(user_id, stock_id):                        
    stock = session.query(Stock).filter(
        Stock.id == stock_id,
        Stock.user_id == user_id
    ).first()
    if stock:
        session.delete(stock)
        session.commit()
        print(f"Stock {stock_id} deleted.")

def available_stock(user_id, pid):
    total = session.query(func.sum(Stock.stock_quantity)).filter(
        Stock.pid == pid, Stock.user_id == user_id).scalar() or 0
    sold = session.query(func.sum(Sale.quantity)).filter(
        Sale.pid == pid, Sale.user_id == user_id).scalar() or 0
    return total - sold