from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, ForeignKey
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

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer,primary_key=True)
    name = Column(String(100))
    buying_price = Column(Integer)
    selling_price = Column(Integer)
    sales = relationship('sale',back_populates = "products")
    stock = relationship('stock',back_populates = "products")

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer,primary_key = True)
    pid = Column(Integer,ForeignKey('products.id'))
    quantity = Column(Integer)
    created_at = Column(DateTime,default=func.now())
    product = relationship("product",back_populates = "sales")

class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer,primary_key = True)
    pid = Column(Integer,ForeignKey('products.id'))
    stock_quantity = Column(Integer)
    product = relationship("product",back_populates = "stock")

Base.metadata.create_all(engine)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

#User functions
def register(username,email,password):
    if session.query(User).filter((User.username == username) |(User.email == email)).first():
        return "User already exists"
    session.add(User(username=username, email=email, password_hash=hash_password(password)))
    session.commit()
    print(f"{username}")

def login(username,password):
    user = session.qury(User).filter(User.username == username).first()
    if not user:
        return print("User not found!")
    if hash_password(password) == user.password_hash:
        print(f"welcome {user.username}!")
        return user
    print("Wrong Password!")

def all_users():
    return session.query(User.id,User.username,User.email).all()

def delete_user(username):
    user = session.query(User).filter(User.username == username).first()
    if user:
        session.delete(user)
        session.commit()
        print(f"{username}deleted.")

#production functions
def add_products(name, buying_price, selling_price):
    session.add(Product(name=name,buying_price = buying_price,selling_price = selling_price))
    session.commit()
    print(f"{name}added.")

def all_products():
    return session.query(Product).all()

#sale functions
def add_sale(pid,quantity):
    session.add(Sale(pid=pid,quantity=quantity))
    session.commit()
    print(f"Sale recorded.")

def sales_per_day():
    from sqlalchemy import cast, Date
    return session.query(
        cast(Sale.created_at, Date).label('day'),
        func.sum(Sale.quantity * Product.selling_price).label('total')
    ).join(Product).group_by('day').all()    

def sales_per_product():
    return session.query(
        Product.name,
        func.sum(Product.selling_price * Sale.quantity).label('total')
    ).join(Product).group_by('day').all()

def profit_per_product():
    return session.query(
        Product.name,
        func.sum((Product.selling_price - Product.buying_price)*Sale.quantity).label('profit')
    ).join(Product).group_by('day').all()

def add_stock(pid,quantity):
    session.add(pid=pid,quantity=quantity)
    session.commit()
    print(f"Stock added.")

def available_stock(pid):
    total = session.query(func.sum(Stock.stock_quantity)).filter(Stock.pid == pid).scalar or 0
    sold = session.query(func.sum(Sale.quantity)).filter(Sale.pid == pid).scalar or 0
    return total - sold
    