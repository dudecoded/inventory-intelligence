from sqlalchemy import String,Integer,Float,Boolean,ForeignKey,DateTime,func
from sqlalchemy.orm import Mapped,mapped_column
from app.core.database import Base
class User(Base):
 __tablename__="users"
 id:Mapped[int]=mapped_column(Integer,primary_key=True)
 email:Mapped[str]=mapped_column(String(255),unique=True,index=True)
 name:Mapped[str]=mapped_column(String(120))
 password_hash:Mapped[str]=mapped_column(String(255))
 company:Mapped[str]=mapped_column(String(160),default="My Workspace")
 role:Mapped[str]=mapped_column(String(40),default="Owner")
 created_at:Mapped[object]=mapped_column(DateTime,server_default=func.now())
class Product(Base):
 __tablename__="products"
 id:Mapped[int]=mapped_column(Integer,primary_key=True)
 sku:Mapped[str]=mapped_column(String(80),index=True)
 name:Mapped[str]=mapped_column(String(200))
 category:Mapped[str]=mapped_column(String(120),default="Uncategorized")
 stock:Mapped[int]=mapped_column(Integer,default=0)
 demand_30d:Mapped[float]=mapped_column(Float,default=0)
 unit_cost:Mapped[float]=mapped_column(Float,default=0)
 lead_time_days:Mapped[int]=mapped_column(Integer,default=7)
 active:Mapped[bool]=mapped_column(Boolean,default=True)
 owner_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
