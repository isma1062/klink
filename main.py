

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel
from datetime import datetime
import os

# -------------------
# CONFIGURACIÓN DB POSTGRESQL (Railway)
# -------------------
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", 5432)
DB_NAME = os.environ.get("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------
# MODELO SQL
# -------------------
class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, index=True)
    product = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# -------------------
# SCHEMAS PYDANTIC
# -------------------
class PurchaseCreate(BaseModel):
    user_name: str
    product: str
    amount: float

class PurchaseResponse(PurchaseCreate):
    id: int
    timestamp: str
    class Config:
        from_attributes = True

# -------------------
# CONFIGURACIÓN FASTAPI
# -------------------
app = FastAPI(title="Postpago API Pública")

# -------------------
# TOKEN DE SEGURIDAD
# -------------------
API_TOKEN = os.environ.get("API_TOKEN", "mi_super_secreto_token_123")  # definir en Railway

def verify_token(x_api_key: str = Header(...)):
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

# -------------------
# DEPENDENCIA DB
# -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------
# ENDPOINTS
# -------------------

# Bienvenida
@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Postpago Pública. Usa /v1/docs para explorar endpoints."}

# Prefijo /v1
from fastapi import APIRouter
router = APIRouter(prefix="/v1")

# Crear compra (POST)
@router.post("/purchases/", response_model=PurchaseResponse, dependencies=[Depends(verify_token)])
def create_purchase(purchase: PurchaseCreate, db: Session = Depends(get_db)):
    new_purchase = Purchase(
        user_name=purchase.user_name,
        product=purchase.product,
        amount=purchase.amount
    )
    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)
    return new_purchase

# Listar compras (GET)
@router.get("/purchases/", response_model=list[PurchaseResponse], dependencies=[Depends(verify_token)])
def get_purchases(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Purchase).offset(skip).limit(limit).all()

# Registrar router
app.include_router(router)
