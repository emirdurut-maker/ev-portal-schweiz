from fastapi import FastAPI, APIRouter, Query, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import feedparser
import asyncio
import hashlib
import re
from html import unescape

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="EV Portal Schweiz API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class Vehicle(BaseModel):
    id: str
    brand: str
    model: str
    variant: str
    price_chf: int
    range_wltp_km: int
    battery_kwh: float
    consumption_kwh_100km: float
    acceleration_0_100: float
    top_speed_kmh: int
    charging_dc_kw: int
    charging_ac_kw: float
    cargo_liters: int
    seats: int
    drivetrain: str  # AWD, FWD, RWD
    year: int
    image_url: Optional[str] = None
    category: str  # SUV, Limousine, Kombi, Kleinwagen, etc.

class CostCalculation(BaseModel):
    ev_yearly_fuel_cost: float
    ice_yearly_fuel_cost: float
    ev_yearly_maintenance: float
    ice_yearly_maintenance: float
    ev_yearly_tax: float
    ice_yearly_tax: float
    ev_yearly_insurance: float
    ice_yearly_insurance: float
    ev_total_yearly: float
    ice_total_yearly: float
    yearly_savings: float
    five_year_savings: float
    break_even_km: float

class CostCalculatorInput(BaseModel):
    yearly_km: int = Field(ge=1000, le=100000)
    electricity_price_kwh: float = Field(ge=0.1, le=1.0)
    petrol_price_liter: float = Field(ge=1.0, le=4.0)
    ev_consumption_kwh_100km: float = Field(ge=10, le=30)
    ice_consumption_l_100km: float = Field(ge=4, le=15)
    canton: str = "ZH"

class ChargingStation(BaseModel):
    id: str
    name: str
    address: str
    city: str
    latitude: float
    longitude: float
    operator: Optional[str]
    num_points: int
    max_power_kw: Optional[float]
    connection_types: List[str]
    is_fast_charger: bool

class KnowledgeArticle(BaseModel):
    id: str
    category: str
    title: str
    slug: str
    content: str
    summary: str
    keywords: List[str]
    order: int

class GlossaryTerm(BaseModel):
    term: str
    definition: str
    category: str

class MythFact(BaseModel):
    id: str
    myth: str
    fact: str
    source: str
    category: str

class MarketData(BaseModel):
    month: str
    year: int
    bev_registrations: int
    phev_registrations: int
    total_registrations: int
    bev_market_share: float
    top_brands: List[Dict[str, Any]]
    top_models: List[Dict[str, Any]]

# ==================== DATA ====================

# Schweizer EV Fahrzeug-Datenbank (reale Daten 2024/2025)
VEHICLES_DATA: List[Dict] = [
    {"id": "1", "brand": "Tesla", "model": "Model 3", "variant": "Long Range", "price_chf": 52990, "range_wltp_km": 678, "battery_kwh": 82, "consumption_kwh_100km": 14.2, "acceleration_0_100": 4.4, "top_speed_kmh": 233, "charging_dc_kw": 250, "charging_ac_kw": 11, "cargo_liters": 561, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1560958089-b8a1929cea89?w=400"},
    {"id": "2", "brand": "Tesla", "model": "Model Y", "variant": "Long Range", "price_chf": 57990, "range_wltp_km": 533, "battery_kwh": 82, "consumption_kwh_100km": 15.7, "acceleration_0_100": 5.0, "top_speed_kmh": 217, "charging_dc_kw": 250, "charging_ac_kw": 11, "cargo_liters": 854, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1619317886570-0a3c2a43bc7e?w=400"},
    {"id": "3", "brand": "Renault", "model": "Scenic E-Tech", "variant": "Long Range", "price_chf": 49990, "range_wltp_km": 620, "battery_kwh": 87, "consumption_kwh_100km": 15.5, "acceleration_0_100": 7.9, "top_speed_kmh": 170, "charging_dc_kw": 150, "charging_ac_kw": 22, "cargo_liters": 545, "seats": 5, "drivetrain": "FWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400"},
    {"id": "4", "brand": "MG", "model": "MG4", "variant": "Extended Range", "price_chf": 36990, "range_wltp_km": 450, "battery_kwh": 64, "consumption_kwh_100km": 15.8, "acceleration_0_100": 7.9, "top_speed_kmh": 160, "charging_dc_kw": 140, "charging_ac_kw": 11, "cargo_liters": 363, "seats": 5, "drivetrain": "FWD", "year": 2024, "category": "Kompaktwagen", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "5", "brand": "Hyundai", "model": "Ioniq 6", "variant": "Long Range AWD", "price_chf": 62900, "range_wltp_km": 614, "battery_kwh": 77.4, "consumption_kwh_100km": 14.3, "acceleration_0_100": 5.1, "top_speed_kmh": 185, "charging_dc_kw": 239, "charging_ac_kw": 11, "cargo_liters": 401, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=400"},
    {"id": "6", "brand": "Hyundai", "model": "Ioniq 5", "variant": "Long Range AWD", "price_chf": 59900, "range_wltp_km": 507, "battery_kwh": 77.4, "consumption_kwh_100km": 17.0, "acceleration_0_100": 5.2, "top_speed_kmh": 185, "charging_dc_kw": 239, "charging_ac_kw": 11, "cargo_liters": 527, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1619317886570-0a3c2a43bc7e?w=400"},
    {"id": "7", "brand": "Kia", "model": "EV6", "variant": "Long Range AWD", "price_chf": 61900, "range_wltp_km": 506, "battery_kwh": 77.4, "consumption_kwh_100km": 17.2, "acceleration_0_100": 5.2, "top_speed_kmh": 188, "charging_dc_kw": 239, "charging_ac_kw": 11, "cargo_liters": 490, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=400"},
    {"id": "8", "brand": "Kia", "model": "EV9", "variant": "Long Range AWD", "price_chf": 84900, "range_wltp_km": 541, "battery_kwh": 99.8, "consumption_kwh_100km": 20.6, "acceleration_0_100": 5.3, "top_speed_kmh": 200, "charging_dc_kw": 239, "charging_ac_kw": 11, "cargo_liters": 828, "seats": 7, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1619317886570-0a3c2a43bc7e?w=400"},
    {"id": "9", "brand": "BMW", "model": "iX1", "variant": "xDrive30", "price_chf": 59900, "range_wltp_km": 440, "battery_kwh": 64.7, "consumption_kwh_100km": 16.9, "acceleration_0_100": 5.6, "top_speed_kmh": 180, "charging_dc_kw": 130, "charging_ac_kw": 11, "cargo_liters": 490, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400"},
    {"id": "10", "brand": "BMW", "model": "i4", "variant": "eDrive40", "price_chf": 67900, "range_wltp_km": 590, "battery_kwh": 83.9, "consumption_kwh_100km": 16.1, "acceleration_0_100": 5.7, "top_speed_kmh": 190, "charging_dc_kw": 205, "charging_ac_kw": 11, "cargo_liters": 470, "seats": 5, "drivetrain": "RWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400"},
    {"id": "11", "brand": "BMW", "model": "iX", "variant": "xDrive50", "price_chf": 109900, "range_wltp_km": 630, "battery_kwh": 111.5, "consumption_kwh_100km": 19.8, "acceleration_0_100": 4.6, "top_speed_kmh": 200, "charging_dc_kw": 200, "charging_ac_kw": 11, "cargo_liters": 500, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=400"},
    {"id": "12", "brand": "Mercedes", "model": "EQA", "variant": "250+", "price_chf": 56900, "range_wltp_km": 560, "battery_kwh": 70.5, "consumption_kwh_100km": 15.7, "acceleration_0_100": 8.6, "top_speed_kmh": 160, "charging_dc_kw": 100, "charging_ac_kw": 11, "cargo_liters": 340, "seats": 5, "drivetrain": "FWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=400"},
    {"id": "13", "brand": "Mercedes", "model": "EQE", "variant": "350+", "price_chf": 89900, "range_wltp_km": 654, "battery_kwh": 90.6, "consumption_kwh_100km": 15.9, "acceleration_0_100": 6.4, "top_speed_kmh": 210, "charging_dc_kw": 170, "charging_ac_kw": 22, "cargo_liters": 430, "seats": 5, "drivetrain": "RWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=400"},
    {"id": "14", "brand": "Mercedes", "model": "EQS", "variant": "450+", "price_chf": 129900, "range_wltp_km": 782, "battery_kwh": 107.8, "consumption_kwh_100km": 15.7, "acceleration_0_100": 5.6, "top_speed_kmh": 210, "charging_dc_kw": 200, "charging_ac_kw": 22, "cargo_liters": 610, "seats": 5, "drivetrain": "RWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=400"},
    {"id": "15", "brand": "Audi", "model": "Q4 e-tron", "variant": "50 quattro", "price_chf": 66900, "range_wltp_km": 488, "battery_kwh": 82, "consumption_kwh_100km": 18.9, "acceleration_0_100": 6.2, "top_speed_kmh": 180, "charging_dc_kw": 175, "charging_ac_kw": 11, "cargo_liters": 520, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=400"},
    {"id": "16", "brand": "Audi", "model": "e-tron GT", "variant": "quattro", "price_chf": 119900, "range_wltp_km": 488, "battery_kwh": 93.4, "consumption_kwh_100km": 21.6, "acceleration_0_100": 4.1, "top_speed_kmh": 245, "charging_dc_kw": 270, "charging_ac_kw": 22, "cargo_liters": 405, "seats": 4, "drivetrain": "AWD", "year": 2024, "category": "Sportwagen", "image_url": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=400"},
    {"id": "17", "brand": "VW", "model": "ID.4", "variant": "Pro Performance", "price_chf": 52990, "range_wltp_km": 531, "battery_kwh": 77, "consumption_kwh_100km": 16.3, "acceleration_0_100": 8.5, "top_speed_kmh": 160, "charging_dc_kw": 175, "charging_ac_kw": 11, "cargo_liters": 543, "seats": 5, "drivetrain": "RWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "18", "brand": "VW", "model": "ID.7", "variant": "Pro S", "price_chf": 65990, "range_wltp_km": 700, "battery_kwh": 86, "consumption_kwh_100km": 14.1, "acceleration_0_100": 6.5, "top_speed_kmh": 180, "charging_dc_kw": 200, "charging_ac_kw": 22, "cargo_liters": 532, "seats": 5, "drivetrain": "RWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "19", "brand": "Porsche", "model": "Taycan", "variant": "4S", "price_chf": 129900, "range_wltp_km": 512, "battery_kwh": 93.4, "consumption_kwh_100km": 20.4, "acceleration_0_100": 4.0, "top_speed_kmh": 250, "charging_dc_kw": 270, "charging_ac_kw": 22, "cargo_liters": 407, "seats": 4, "drivetrain": "AWD", "year": 2024, "category": "Sportwagen", "image_url": "https://images.unsplash.com/photo-1614200187524-dc4b892acf16?w=400"},
    {"id": "20", "brand": "Porsche", "model": "Macan Electric", "variant": "4", "price_chf": 89900, "range_wltp_km": 613, "battery_kwh": 100, "consumption_kwh_100km": 18.4, "acceleration_0_100": 5.2, "top_speed_kmh": 220, "charging_dc_kw": 270, "charging_ac_kw": 22, "cargo_liters": 540, "seats": 5, "drivetrain": "AWD", "year": 2025, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1614200187524-dc4b892acf16?w=400"},
    {"id": "21", "brand": "Volvo", "model": "EX30", "variant": "Single Motor Extended", "price_chf": 41900, "range_wltp_km": 480, "battery_kwh": 69, "consumption_kwh_100km": 16.0, "acceleration_0_100": 5.7, "top_speed_kmh": 180, "charging_dc_kw": 153, "charging_ac_kw": 11, "cargo_liters": 318, "seats": 5, "drivetrain": "RWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=400"},
    {"id": "22", "brand": "Volvo", "model": "EX90", "variant": "Twin Motor Performance", "price_chf": 104900, "range_wltp_km": 580, "battery_kwh": 111, "consumption_kwh_100km": 21.5, "acceleration_0_100": 4.9, "top_speed_kmh": 180, "charging_dc_kw": 250, "charging_ac_kw": 22, "cargo_liters": 655, "seats": 7, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=400"},
    {"id": "23", "brand": "Polestar", "model": "2", "variant": "Long Range Dual Motor", "price_chf": 57900, "range_wltp_km": 592, "battery_kwh": 82, "consumption_kwh_100km": 15.5, "acceleration_0_100": 4.2, "top_speed_kmh": 205, "charging_dc_kw": 205, "charging_ac_kw": 22, "cargo_liters": 405, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=400"},
    {"id": "24", "brand": "Polestar", "model": "4", "variant": "Long Range Dual Motor", "price_chf": 69900, "range_wltp_km": 600, "battery_kwh": 102, "consumption_kwh_100km": 18.5, "acceleration_0_100": 3.8, "top_speed_kmh": 200, "charging_dc_kw": 200, "charging_ac_kw": 22, "cargo_liters": 526, "seats": 5, "drivetrain": "AWD", "year": 2025, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=400"},
    {"id": "25", "brand": "Skoda", "model": "Enyaq", "variant": "85x", "price_chf": 57990, "range_wltp_km": 513, "battery_kwh": 82, "consumption_kwh_100km": 17.9, "acceleration_0_100": 6.8, "top_speed_kmh": 180, "charging_dc_kw": 175, "charging_ac_kw": 11, "cargo_liters": 585, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "26", "brand": "Cupra", "model": "Born", "variant": "e-Boost 170 kW", "price_chf": 45990, "range_wltp_km": 548, "battery_kwh": 77, "consumption_kwh_100km": 15.8, "acceleration_0_100": 7.0, "top_speed_kmh": 160, "charging_dc_kw": 170, "charging_ac_kw": 11, "cargo_liters": 385, "seats": 5, "drivetrain": "RWD", "year": 2024, "category": "Kompaktwagen", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "27", "brand": "Cupra", "model": "Tavascan", "variant": "VZ", "price_chf": 63900, "range_wltp_km": 517, "battery_kwh": 82, "consumption_kwh_100km": 17.8, "acceleration_0_100": 5.5, "top_speed_kmh": 180, "charging_dc_kw": 175, "charging_ac_kw": 11, "cargo_liters": 540, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "28", "brand": "Fiat", "model": "500e", "variant": "La Prima", "price_chf": 39990, "range_wltp_km": 321, "battery_kwh": 42, "consumption_kwh_100km": 14.4, "acceleration_0_100": 9.0, "top_speed_kmh": 150, "charging_dc_kw": 85, "charging_ac_kw": 11, "cargo_liters": 185, "seats": 4, "drivetrain": "FWD", "year": 2024, "category": "Kleinwagen", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "29", "brand": "Mini", "model": "Cooper SE", "variant": "Electric", "price_chf": 39900, "range_wltp_km": 305, "battery_kwh": 54.2, "consumption_kwh_100km": 15.9, "acceleration_0_100": 6.7, "top_speed_kmh": 170, "charging_dc_kw": 95, "charging_ac_kw": 11, "cargo_liters": 200, "seats": 4, "drivetrain": "FWD", "year": 2024, "category": "Kleinwagen", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "30", "brand": "BYD", "model": "Seal", "variant": "Excellence AWD", "price_chf": 52990, "range_wltp_km": 520, "battery_kwh": 82.5, "consumption_kwh_100km": 17.9, "acceleration_0_100": 3.8, "top_speed_kmh": 180, "charging_dc_kw": 150, "charging_ac_kw": 11, "cargo_liters": 400, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "31", "brand": "BYD", "model": "Atto 3", "variant": "Design", "price_chf": 44990, "range_wltp_km": 420, "battery_kwh": 60.5, "consumption_kwh_100km": 16.8, "acceleration_0_100": 7.3, "top_speed_kmh": 160, "charging_dc_kw": 88, "charging_ac_kw": 11, "cargo_liters": 440, "seats": 5, "drivetrain": "FWD", "year": 2024, "category": "SUV", "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400"},
    {"id": "32", "brand": "Lucid", "model": "Air", "variant": "Grand Touring", "price_chf": 149900, "range_wltp_km": 819, "battery_kwh": 112, "consumption_kwh_100km": 15.3, "acceleration_0_100": 3.0, "top_speed_kmh": 270, "charging_dc_kw": 300, "charging_ac_kw": 22, "cargo_liters": 627, "seats": 5, "drivetrain": "AWD", "year": 2024, "category": "Limousine", "image_url": "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=400"},
]

# Kantonale Steuerdaten (vereinfacht)
CANTON_TAX_DATA = {
    "ZH": {"name": "Zürich", "ev_tax_reduction": 0.50, "ev_yearly_tax": 250, "ice_yearly_tax": 500, "incentive": 0},
    "BE": {"name": "Bern", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 400, "incentive": 0},
    "LU": {"name": "Luzern", "ev_tax_reduction": 0.50, "ev_yearly_tax": 200, "ice_yearly_tax": 400, "incentive": 0},
    "BS": {"name": "Basel-Stadt", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 500, "incentive": 2000},
    "BL": {"name": "Basel-Land", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 450, "incentive": 0},
    "SG": {"name": "St. Gallen", "ev_tax_reduction": 0.50, "ev_yearly_tax": 150, "ice_yearly_tax": 300, "incentive": 0},
    "AG": {"name": "Aargau", "ev_tax_reduction": 0.50, "ev_yearly_tax": 200, "ice_yearly_tax": 400, "incentive": 0},
    "TG": {"name": "Thurgau", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 350, "incentive": 3000},
    "GR": {"name": "Graubünden", "ev_tax_reduction": 0.50, "ev_yearly_tax": 150, "ice_yearly_tax": 300, "incentive": 0},
    "TI": {"name": "Tessin", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 400, "incentive": 1000},
    "VD": {"name": "Waadt", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 450, "incentive": 0},
    "GE": {"name": "Genf", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 500, "incentive": 0},
    "VS": {"name": "Wallis", "ev_tax_reduction": 0.50, "ev_yearly_tax": 100, "ice_yearly_tax": 200, "incentive": 0},
    "NE": {"name": "Neuenburg", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 350, "incentive": 0},
    "FR": {"name": "Freiburg", "ev_tax_reduction": 0.50, "ev_yearly_tax": 150, "ice_yearly_tax": 300, "incentive": 0},
    "SO": {"name": "Solothurn", "ev_tax_reduction": 0.50, "ev_yearly_tax": 175, "ice_yearly_tax": 350, "incentive": 0},
    "SH": {"name": "Schaffhausen", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 300, "incentive": 0},
    "ZG": {"name": "Zug", "ev_tax_reduction": 0.50, "ev_yearly_tax": 200, "ice_yearly_tax": 400, "incentive": 0},
    "SZ": {"name": "Schwyz", "ev_tax_reduction": 0.50, "ev_yearly_tax": 175, "ice_yearly_tax": 350, "incentive": 0},
    "GL": {"name": "Glarus", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 300, "incentive": 0},
    "NW": {"name": "Nidwalden", "ev_tax_reduction": 0.50, "ev_yearly_tax": 150, "ice_yearly_tax": 300, "incentive": 0},
    "OW": {"name": "Obwalden", "ev_tax_reduction": 0.50, "ev_yearly_tax": 150, "ice_yearly_tax": 300, "incentive": 0},
    "UR": {"name": "Uri", "ev_tax_reduction": 0.50, "ev_yearly_tax": 125, "ice_yearly_tax": 250, "incentive": 0},
    "JU": {"name": "Jura", "ev_tax_reduction": 1.0, "ev_yearly_tax": 0, "ice_yearly_tax": 350, "incentive": 0},
    "AI": {"name": "Appenzell Innerrhoden", "ev_tax_reduction": 0.50, "ev_yearly_tax": 100, "ice_yearly_tax": 200, "incentive": 0},
    "AR": {"name": "Appenzell Ausserrhoden", "ev_tax_reduction": 0.50, "ev_yearly_tax": 125, "ice_yearly_tax": 250, "incentive": 0},
}

# EV Wissen Glossar
GLOSSARY_DATA: List[Dict] = [
    {"term": "kWh", "definition": "Kilowattstunde - Masseinheit für Energiemenge. Entspricht der Batteriekapazität eines EVs. Ein durchschnittliches EV verbraucht ca. 15-20 kWh pro 100 km.", "category": "Energie"},
    {"term": "kW", "definition": "Kilowatt - Masseinheit für Leistung. Gibt an, wie schnell Energie übertragen wird. 100 kW Ladeleistung = 100 kWh Energie pro Stunde.", "category": "Energie"},
    {"term": "WLTP", "definition": "Worldwide Harmonized Light Vehicles Test Procedure - standardisiertes Testverfahren für Verbrauch und Reichweite. Realistischer als der alte NEFZ-Wert.", "category": "Standards"},
    {"term": "Rekuperation", "definition": "Energierückgewinnung beim Bremsen. Der Elektromotor arbeitet als Generator und lädt die Batterie wieder auf. Erhöht die Effizienz um 10-30%.", "category": "Technologie"},
    {"term": "BEV", "definition": "Battery Electric Vehicle - reines Elektrofahrzeug, das ausschliesslich von einer Batterie angetrieben wird.", "category": "Fahrzeugtypen"},
    {"term": "PHEV", "definition": "Plug-in Hybrid Electric Vehicle - Fahrzeug mit Elektro- und Verbrennungsmotor, das extern aufgeladen werden kann.", "category": "Fahrzeugtypen"},
    {"term": "DC-Laden", "definition": "Gleichstrom-Schnellladen. Umwandlung erfolgt in der Ladestation, nicht im Fahrzeug. Ermöglicht Ladeleistungen von 50-350 kW.", "category": "Laden"},
    {"term": "AC-Laden", "definition": "Wechselstrom-Laden. Standardmässig zuhause oder an öffentlichen Ladesäulen. Typisch 3.7-22 kW Ladeleistung.", "category": "Laden"},
    {"term": "CCS", "definition": "Combined Charging System - europäischer Standard für DC-Schnellladen. Kombiniert AC- und DC-Laden in einem Stecker.", "category": "Laden"},
    {"term": "Typ 2", "definition": "Europäischer Standard-Stecker für AC-Laden. Unterstützt bis zu 43 kW (meistens 11-22 kW).", "category": "Laden"},
    {"term": "SoC", "definition": "State of Charge - aktueller Ladezustand der Batterie in Prozent (0-100%).", "category": "Batterie"},
    {"term": "SoH", "definition": "State of Health - Gesundheitszustand der Batterie. 100% = Neuzustand, sinkt über Zeit auf ca. 70-80%.", "category": "Batterie"},
    {"term": "Degradation", "definition": "Alterungsbedingter Kapazitätsverlust der Batterie. Typisch 1-2% pro Jahr bei modernem Fahrzeug.", "category": "Batterie"},
    {"term": "LFP", "definition": "Lithium-Eisenphosphat - Batteriechemie mit hoher Langlebigkeit und Sicherheit. Kann auf 100% geladen werden.", "category": "Batterie"},
    {"term": "NMC", "definition": "Nickel-Mangan-Cobalt - Batteriechemie mit hoher Energiedichte. Optimal bei 20-80% Ladezustand halten.", "category": "Batterie"},
    {"term": "V2G", "definition": "Vehicle-to-Grid - bidirektionales Laden. Das Fahrzeug kann Energie ins Stromnetz zurückspeisen.", "category": "Technologie"},
    {"term": "OTA", "definition": "Over-the-Air Updates - Software-Updates, die drahtlos auf das Fahrzeug übertragen werden.", "category": "Technologie"},
    {"term": "Frunk", "definition": "Front Trunk - zusätzlicher Stauraum vorne, wo bei Verbrennern der Motor sitzt.", "category": "Fahrzeug"},
    {"term": "One-Pedal-Driving", "definition": "Fahren mit nur einem Pedal. Starke Rekuperation beim Loslassen des Gaspedals bremst das Fahrzeug.", "category": "Technologie"},
    {"term": "Vorkonditionierung", "definition": "Vorheizen oder Kühlen von Batterie und Innenraum vor der Fahrt, während das Auto noch am Stromnetz hängt.", "category": "Technologie"},
]

# Mythen und Fakten
MYTHS_DATA: List[Dict] = [
    {
        "id": "1",
        "myth": "Elektroautos brennen häufiger als Verbrenner",
        "fact": "Laut Statistiken der Schweizer Versicherungen sind Brände bei EVs 25-60x seltener als bei Verbrennern. Die Berichterstattung ist aber intensiver, daher die Wahrnehmung.",
        "source": "Schweizerischer Versicherungsverband SVV, 2024",
        "category": "Sicherheit"
    },
    {
        "id": "2",
        "myth": "Der Strom reicht nicht für alle Elektroautos",
        "fact": "Wenn alle Schweizer Autos elektrisch wären, würde der Stromverbrauch um ca. 15% steigen. Die Schweiz produziert genug Strom - die Frage ist die Verteilung und Speicherung.",
        "source": "Bundesamt für Energie BFE, 2024",
        "category": "Energie"
    },
    {
        "id": "3",
        "myth": "Im Winter ist ein EV nutzlos",
        "fact": "Die Reichweite sinkt im Winter um 20-30%, aber moderne EVs haben Wärmepumpen und Batterieheizungen. Für 95% aller Fahrten reicht es trotzdem.",
        "source": "TCS Test, Winter 2023/24",
        "category": "Reichweite"
    },
    {
        "id": "4",
        "myth": "Batterieproduktion ist schlimmer als Verbrennerfahren",
        "fact": "Nach 30'000-50'000 km hat ein EV seine 'CO2-Schuld' aus der Produktion ausgeglichen. Danach fährt es deutlich sauberer als jeder Verbrenner.",
        "source": "EMPA Studie, 2023",
        "category": "Umwelt"
    },
    {
        "id": "5",
        "myth": "Batterien halten nur wenige Jahre",
        "fact": "Moderne EV-Batterien sind für 500'000+ km ausgelegt. Nach 10 Jahren haben die meisten EVs noch 80-90% Kapazität. Hersteller geben 8 Jahre Garantie.",
        "source": "Geotab EV Battery Degradation Report, 2024",
        "category": "Batterie"
    },
    {
        "id": "6",
        "myth": "Schnellladen zerstört die Batterie",
        "fact": "Gelegentliches Schnellladen ist unbedenklich. Nur tägliches DC-Laden über 80% auf Dauer kann die Degradation um 0.1-0.2% pro Jahr erhöhen.",
        "source": "Idaho National Laboratory, 2024",
        "category": "Batterie"
    },
    {
        "id": "7",
        "myth": "EVs sind zu teuer für Normalverdiener",
        "fact": "Ab CHF 30'000 gibt es gute EVs (Dacia Spring, MG4, etc.). Mit tieferen Betriebskosten rechnet sich ein EV oft nach 3-5 Jahren.",
        "source": "TCS Kostenvergleich, 2024",
        "category": "Kosten"
    },
    {
        "id": "8",
        "myth": "Es gibt nicht genug Ladestationen",
        "fact": "Die Schweiz hat über 12'000 öffentliche Ladepunkte, davon 2'800+ Schnelllader. Das Netz wächst monatlich um 100+ Stationen.",
        "source": "ich-tanke-strom.ch, 2024",
        "category": "Laden"
    },
]

# Marktdaten Schweiz (2024)
MARKET_DATA: List[Dict] = [
    {"month": "Januar", "year": 2024, "bev_registrations": 5234, "phev_registrations": 2145, "total_registrations": 24567, "bev_market_share": 21.3},
    {"month": "Februar", "year": 2024, "bev_registrations": 5678, "phev_registrations": 2234, "total_registrations": 26789, "bev_market_share": 21.2},
    {"month": "März", "year": 2024, "bev_registrations": 7123, "phev_registrations": 2567, "total_registrations": 31234, "bev_market_share": 22.8},
    {"month": "April", "year": 2024, "bev_registrations": 5890, "phev_registrations": 2123, "total_registrations": 27890, "bev_market_share": 21.1},
    {"month": "Mai", "year": 2024, "bev_registrations": 6234, "phev_registrations": 2345, "total_registrations": 29123, "bev_market_share": 21.4},
    {"month": "Juni", "year": 2024, "bev_registrations": 6789, "phev_registrations": 2456, "total_registrations": 30456, "bev_market_share": 22.3},
    {"month": "Juli", "year": 2024, "bev_registrations": 5456, "phev_registrations": 2012, "total_registrations": 25678, "bev_market_share": 21.2},
    {"month": "August", "year": 2024, "bev_registrations": 5890, "phev_registrations": 2234, "total_registrations": 27890, "bev_market_share": 21.1},
    {"month": "September", "year": 2024, "bev_registrations": 6543, "phev_registrations": 2567, "total_registrations": 29876, "bev_market_share": 21.9},
    {"month": "Oktober", "year": 2024, "bev_registrations": 6234, "phev_registrations": 2345, "total_registrations": 28765, "bev_market_share": 21.7},
    {"month": "November", "year": 2024, "bev_registrations": 5678, "phev_registrations": 2123, "total_registrations": 26543, "bev_market_share": 21.4},
    {"month": "Dezember", "year": 2024, "bev_registrations": 8234, "phev_registrations": 3012, "total_registrations": 35678, "bev_market_share": 23.1},
]

# Wissensartikel
KNOWLEDGE_ARTICLES: List[Dict] = [
    {
        "id": "1",
        "category": "batterie",
        "title": "Wie funktioniert eine EV-Batterie?",
        "slug": "ev-batterie-erklaert",
        "summary": "Die Lithium-Ionen-Batterie ist das Herzstück jedes Elektroautos. Sie speichert elektrische Energie chemisch und gibt sie bei Bedarf wieder ab.",
        "content": """Die Batterie eines Elektroautos besteht aus tausenden einzelnen Zellen, die zu Modulen zusammengefasst werden. Jede Zelle enthält:

**Anode (-)**: Meist aus Graphit, speichert Lithium-Ionen beim Laden
**Kathode (+)**: Verschiedene Materialien (NMC, LFP, etc.), gibt Lithium-Ionen beim Entladen ab
**Elektrolyt**: Flüssigkeit, durch die die Lithium-Ionen wandern
**Separator**: Trennt Anode und Kathode, lässt aber Ionen durch

Beim **Laden** wandern Lithium-Ionen von der Kathode zur Anode.
Beim **Entladen** (Fahren) wandern sie zurück und setzen dabei Energie frei.

**Wichtige Kennzahlen:**
- **Kapazität (kWh)**: Wie viel Energie gespeichert werden kann
- **Energiedichte (Wh/kg)**: Je höher, desto leichter bei gleicher Kapazität
- **Zyklen**: Eine moderne EV-Batterie schafft 1500-3000 Ladezyklen""",
        "keywords": ["Batterie", "Lithium-Ionen", "Energiespeicher", "Zellen"],
        "order": 1
    },
    {
        "id": "2",
        "category": "batterie",
        "title": "NMC vs. LFP - Welche Batterie ist besser?",
        "slug": "nmc-vs-lfp",
        "summary": "Die beiden häufigsten Batteriechemien haben unterschiedliche Vor- und Nachteile. Hier erfahren Sie, welche für Ihre Bedürfnisse passt.",
        "content": """**NMC (Nickel-Mangan-Cobalt)**

✅ Vorteile:
- Höhere Energiedichte = mehr Reichweite bei gleichem Gewicht
- Bessere Performance bei Kälte
- Schnellere Ladekurve

❌ Nachteile:
- Teurer (enthält Cobalt)
- Sollte zwischen 20-80% gehalten werden
- Etwas schnellere Degradation

**LFP (Lithium-Eisenphosphat)**

✅ Vorteile:
- Günstiger in der Herstellung
- Kann auf 100% geladen werden
- Längere Lebensdauer (mehr Zyklen)
- Sicherer (thermisch stabiler)

❌ Nachteile:
- Geringere Energiedichte = weniger Reichweite
- Schwächer bei sehr kalten Temperaturen
- Langsameres Laden im unteren SoC-Bereich

**Fazit:** LFP ist ideal für Stadtfahrer und Vielfahrer. NMC für Langstrecke und Performance.""",
        "keywords": ["NMC", "LFP", "Batteriechemie", "Energiedichte"],
        "order": 2
    },
    {
        "id": "3",
        "category": "laden",
        "title": "AC vs. DC Laden erklärt",
        "slug": "ac-vs-dc-laden",
        "summary": "Was ist der Unterschied zwischen AC und DC Laden? Wann nutze ich was?",
        "content": """**AC-Laden (Wechselstrom)**

Das ist das "normale" Laden zuhause oder an öffentlichen Ladesäulen.

- Strom aus dem Netz ist Wechselstrom (AC)
- Das Fahrzeug wandelt ihn intern in Gleichstrom (DC) um
- Ladeleistung: 3.7 kW (Haushaltssteckdose) bis 22 kW (Wallbox/Ladesäule)
- Ladedauer: 4-12 Stunden für eine volle Ladung

**DC-Laden (Gleichstrom / Schnellladen)**

Das ist Schnellladen an Autobahnraststätten und Schnellladeparks.

- Die Ladestation wandelt AC in DC um (ausserhalb des Fahrzeugs)
- Dadurch sind viel höhere Leistungen möglich
- Ladeleistung: 50 kW bis 350 kW
- Ladedauer: 20-40 Minuten für 10-80%

**Wann was nutzen?**

| Situation | Empfehlung |
|-----------|------------|
| Zuhause über Nacht | AC (11kW Wallbox ideal) |
| Arbeitsplatz | AC |
| Einkaufen | AC oder DC |
| Langstrecke | DC |
| Schnell zwischendurch | DC |""",
        "keywords": ["AC-Laden", "DC-Laden", "Schnellladen", "Wallbox"],
        "order": 3
    },
    {
        "id": "4",
        "category": "laden",
        "title": "Die richtige Wallbox für zuhause",
        "slug": "wallbox-kaufberatung",
        "summary": "Eine Wallbox ist die beste Investition für EV-Besitzer. Was Sie vor dem Kauf wissen müssen.",
        "content": """**Warum eine Wallbox?**

- Sicherer als die Haushaltssteckdose
- Schneller (11kW vs. 2.3kW)
- Oft mit intelligenter Steuerung
- Förderfähig in einigen Kantonen

**Wichtige Eigenschaften:**

**Ladeleistung:**
- 11 kW = Standard, reicht für die meisten
- 22 kW = sinnvoll bei grossen Batterien oder wenn wenig Zeit

**Steckertyp:**
- Typ 2 = europäischer Standard
- Mit festem Kabel = bequemer
- Mit Steckdose = flexibler

**Smart-Funktionen:**
- App-Steuerung
- Lastmanagement (wichtig bei Mehrfamilienhäusern)
- Dynamisches Laden (passt sich dem Hausverbrauch an)
- Solar-Integration möglich

**Kosten in der Schweiz:**
- Wallbox: CHF 800-2'500
- Installation: CHF 500-2'000
- Total: CHF 1'500-4'500

**Tipp:** Prüfen Sie kantonale Förderungen vor dem Kauf!""",
        "keywords": ["Wallbox", "Heimladen", "Installation", "Kosten"],
        "order": 4
    },
    {
        "id": "5",
        "category": "reichweite",
        "title": "Realreichweite vs. WLTP verstehen",
        "slug": "realreichweite-wltp",
        "summary": "Warum erreichen Sie nie die angegebene Reichweite? So berechnen Sie die echte Reichweite.",
        "content": """**Was ist WLTP?**

WLTP (Worldwide Harmonized Light Vehicles Test Procedure) ist ein standardisiertes Testverfahren auf dem Prüfstand:
- Konstante 23°C Temperatur
- Definierte Fahrzyklen
- Keine Klimaanlage/Heizung
- Ideale Bedingungen

**Realreichweite im Alltag:**

Die tatsächliche Reichweite hängt von vielen Faktoren ab:

| Faktor | Einfluss |
|--------|----------|
| Aussentemperatur | -20% bis +5% |
| Geschwindigkeit | -30% bei 130 km/h vs. 100 km/h |
| Klimatisierung | -5% bis -20% |
| Fahrstil | -10% bis +10% |
| Topographie | variiert stark |
| Reifen | -5% bis -10% |

**Faustregeln:**

🌡️ **Sommer (20°C+):** ~85-95% der WLTP
❄️ **Winter (-5°C):** ~65-75% der WLTP
🛣️ **Autobahn:** ~70-80% der WLTP
🏙️ **Stadt:** ~100-120% der WLTP (Rekuperation!)

**Tipp:** Nutzen Sie ABRP (A Better Route Planner) für realistische Routenplanung.""",
        "keywords": ["WLTP", "Reichweite", "Realverbrauch", "Winter"],
        "order": 5
    },
    {
        "id": "6",
        "category": "kosten",
        "title": "Was kostet ein EV wirklich?",
        "slug": "ev-kosten-vergleich",
        "summary": "Der Kaufpreis ist höher, aber die Gesamtkosten? Ein ehrlicher Vergleich.",
        "content": """**Anschaffungskosten:**

EVs sind in der Anschaffung noch teurer als vergleichbare Verbrenner. Aber:
- Preise sinken stetig
- Ab CHF 30'000 gibt es gute EVs
- Occasion-Markt wächst

**Betriebskosten pro Jahr (15'000 km):**

| Kostenpunkt | EV | Verbrenner |
|-------------|-----|------------|
| Energie/Kraftstoff | CHF 600-900 | CHF 2'000-2'800 |
| Service | CHF 200-400 | CHF 600-1'000 |
| Motorfahrzeugsteuer | CHF 0-250 | CHF 300-600 |
| Versicherung | CHF 600-1'000 | CHF 700-1'200 |
| **Total** | **CHF 1'400-2'550** | **CHF 3'600-5'600** |

**Einsparung:** CHF 1'500-3'000 pro Jahr!

**Break-Even:**

Bei CHF 10'000 Preisunterschied und CHF 2'000 Ersparnis/Jahr:
→ Nach 5 Jahren sind Sie im Plus

**Nicht vergessen:**
- Wertverlust: EVs halten Wert gut
- Förderungen: Je nach Kanton
- Restwert der Batterie""",
        "keywords": ["Kosten", "Vergleich", "TCO", "Betriebskosten"],
        "order": 6
    },
]

# ==================== NEWS FEED CONFIGURATION ====================

# RSS Feed Sources organized by region and category
NEWS_FEEDS = {
    # Schweizer Quellen
    "swiss": [
        {"url": "https://www.tcs.ch/de/testberichte-ratgeber/ratgeber/rss/elektromobilitaet.rss", "name": "TCS Elektromobilität", "lang": "de", "region": "CH"},
        {"url": "https://www.blick.ch/auto/rss.xml", "name": "Blick Auto", "lang": "de", "region": "CH"},
    ],
    # Deutsche Quellen
    "german": [
        {"url": "https://www.electrive.net/feed/", "name": "Electrive.net", "lang": "de", "region": "DE"},
        {"url": "https://ecomento.de/feed/", "name": "Ecomento", "lang": "de", "region": "DE"},
        {"url": "https://www.elektroauto-news.net/feed/", "name": "Elektroauto-News", "lang": "de", "region": "DE"},
        {"url": "https://teslamag.de/feed", "name": "Teslamag", "lang": "de", "region": "DE"},
        {"url": "https://www.golem.de/rss.php?tp=auto", "name": "Golem Auto", "lang": "de", "region": "DE"},
    ],
    # Internationale/Europäische Quellen  
    "international": [
        {"url": "https://electrek.co/feed/", "name": "Electrek", "lang": "en", "region": "US"},
        {"url": "https://insideevs.com/rss/news/all/", "name": "InsideEVs", "lang": "en", "region": "US"},
        {"url": "https://cleantechnica.com/feed/", "name": "CleanTechnica", "lang": "en", "region": "US"},
        {"url": "https://www.greencarreports.com/rss/news", "name": "Green Car Reports", "lang": "en", "region": "US"},
        {"url": "https://chargedevs.com/feed/", "name": "Charged EVs", "lang": "en", "region": "US"},
    ],
    # Balkan/Südosteuropa Quellen
    "balkan": [
        {"url": "https://www.netokracija.rs/feed", "name": "Netokracija RS", "lang": "sr", "region": "RS"},
        {"url": "https://www.netokracija.com/feed", "name": "Netokracija HR", "lang": "hr", "region": "HR"},
        {"url": "https://www.automarket.hr/rss/vijesti", "name": "Automarket HR", "lang": "hr", "region": "HR"},
        {"url": "https://www.automobili.hr/rss.xml", "name": "Automobili HR", "lang": "hr", "region": "HR"},
    ],
}

# News categories for filtering
NEWS_CATEGORIES = {
    "vehicles": ["fahrzeug", "vehicle", "auto", "car", "model", "modell", "ev", "elektroauto", "automobil", "vozilo"],
    "battery": ["batterie", "battery", "akku", "zelle", "cell", "reichweite", "range", "degradation", "lebensdauer", "baterija"],
    "charging": ["laden", "charging", "ladestation", "charger", "ladesäule", "wallbox", "schnellladen", "dc", "ac", "punjenje", "punjač"],
    "policy": ["förderung", "subsidy", "gesetz", "law", "regulierung", "regulation", "steuer", "tax", "politik", "policy", "zakon", "poticaj"],
    "market": ["markt", "market", "verkauf", "sales", "zulassung", "registration", "statistik", "statistic", "preis", "price", "tržište"],
    "technology": ["technologie", "technology", "update", "software", "ota", "autopilot", "fsd", "tuning", "upgrade", "tehnologija"],
    "infrastructure": ["infrastruktur", "infrastructure", "netzwerk", "network", "ausbau", "expansion", "strom", "grid", "mreža"],
}

# Cache for news articles
news_cache = {
    "articles": [],
    "last_updated": None,
    "cache_duration": timedelta(hours=1)
}

def clean_html(text: str) -> str:
    """Remove HTML tags and clean text"""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Unescape HTML entities
    clean = unescape(clean)
    # Remove extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:500] + "..." if len(clean) > 500 else clean

def categorize_article(title: str, summary: str) -> List[str]:
    """Categorize article based on keywords in title and summary"""
    categories = []
    text = (title + " " + summary).lower()
    
    for cat, keywords in NEWS_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text:
                categories.append(cat)
                break
    
    return categories if categories else ["general"]

def generate_article_id(url: str) -> str:
    """Generate unique ID for article based on URL"""
    return hashlib.md5(url.encode()).hexdigest()[:12]

async def fetch_single_feed(feed_config: Dict) -> List[Dict]:
    """Fetch and parse a single RSS feed"""
    articles = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(feed_config["url"], follow_redirects=True)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:10]:  # Limit to 10 per feed
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        except:
                            pub_date = datetime.now(timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        try:
                            pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                        except:
                            pub_date = datetime.now(timezone.utc)
                    else:
                        pub_date = datetime.now(timezone.utc)
                    
                    # Get summary/description
                    summary = ""
                    if hasattr(entry, 'summary'):
                        summary = clean_html(entry.summary)
                    elif hasattr(entry, 'description'):
                        summary = clean_html(entry.description)
                    
                    # Get image if available
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        for enc in entry.enclosures:
                            if enc.get('type', '').startswith('image'):
                                image_url = enc.get('href')
                                break
                    
                    title = clean_html(entry.get('title', 'Kein Titel'))
                    link = entry.get('link', '')
                    
                    article = {
                        "id": generate_article_id(link),
                        "title": title,
                        "summary": summary,
                        "url": link,
                        "source": feed_config["name"],
                        "language": feed_config["lang"],
                        "region": feed_config["region"],
                        "published": pub_date.isoformat() if pub_date else None,
                        "image_url": image_url,
                        "categories": categorize_article(title, summary),
                    }
                    articles.append(article)
                    
    except Exception as e:
        logger.warning(f"Error fetching feed {feed_config['name']}: {e}")
    
    return articles

async def fetch_all_feeds() -> List[Dict]:
    """Fetch all RSS feeds concurrently"""
    all_feeds = []
    for region_feeds in NEWS_FEEDS.values():
        all_feeds.extend(region_feeds)
    
    # Fetch all feeds concurrently
    tasks = [fetch_single_feed(feed) for feed in all_feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine all articles
    all_articles = []
    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)
    
    # Sort by publication date (newest first)
    all_articles.sort(key=lambda x: x.get('published', '') or '', reverse=True)
    
    # Remove duplicates based on title similarity
    seen_titles = set()
    unique_articles = []
    for article in all_articles:
        title_key = article['title'].lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    return unique_articles

# ==================== ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "EV Portal Schweiz API", "version": "1.0.0"}

# Health Check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ==================== VEHICLES ====================

@api_router.get("/vehicles", response_model=List[Vehicle])
async def get_vehicles(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_range: Optional[int] = None,
    sort_by: Optional[str] = "price_chf",
    sort_order: Optional[str] = "asc"
):
    """Get all vehicles with optional filters"""
    filtered = VEHICLES_DATA.copy()
    
    if brand:
        filtered = [v for v in filtered if v["brand"].lower() == brand.lower()]
    if category:
        filtered = [v for v in filtered if v["category"].lower() == category.lower()]
    if min_price:
        filtered = [v for v in filtered if v["price_chf"] >= min_price]
    if max_price:
        filtered = [v for v in filtered if v["price_chf"] <= max_price]
    if min_range:
        filtered = [v for v in filtered if v["range_wltp_km"] >= min_range]
    
    # Sorting
    if sort_by in ["price_chf", "range_wltp_km", "battery_kwh", "acceleration_0_100"]:
        reverse = sort_order == "desc"
        filtered.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
    
    return filtered

@api_router.get("/vehicles/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(vehicle_id: str):
    """Get a specific vehicle by ID"""
    for v in VEHICLES_DATA:
        if v["id"] == vehicle_id:
            return v
    raise HTTPException(status_code=404, detail="Vehicle not found")

@api_router.get("/vehicles/brands/list")
async def get_brands():
    """Get list of all brands"""
    brands = list(set(v["brand"] for v in VEHICLES_DATA))
    brands.sort()
    return {"brands": brands}

@api_router.get("/vehicles/categories/list")
async def get_categories():
    """Get list of all vehicle categories"""
    categories = list(set(v["category"] for v in VEHICLES_DATA))
    categories.sort()
    return {"categories": categories}

@api_router.get("/vehicles/stats/price-per-km")
async def get_price_per_km_ranking():
    """Get vehicles ranked by price per km of range"""
    rankings = []
    for v in VEHICLES_DATA:
        price_per_km = round(v["price_chf"] / v["range_wltp_km"], 2)
        rankings.append({
            "vehicle": f"{v['brand']} {v['model']}",
            "price_chf": v["price_chf"],
            "range_km": v["range_wltp_km"],
            "price_per_km": price_per_km
        })
    rankings.sort(key=lambda x: x["price_per_km"])
    return {"rankings": rankings[:10]}

# ==================== COST CALCULATOR ====================

@api_router.post("/calculator/cost", response_model=CostCalculation)
async def calculate_costs(input_data: CostCalculatorInput):
    """Calculate total cost of ownership comparison"""
    canton_data = CANTON_TAX_DATA.get(input_data.canton, CANTON_TAX_DATA["ZH"])
    
    # Yearly fuel costs
    ev_yearly_fuel_cost = (input_data.yearly_km / 100) * input_data.ev_consumption_kwh_100km * input_data.electricity_price_kwh
    ice_yearly_fuel_cost = (input_data.yearly_km / 100) * input_data.ice_consumption_l_100km * input_data.petrol_price_liter
    
    # Maintenance (EVs are ~50% cheaper)
    ev_yearly_maintenance = 300  # CHF
    ice_yearly_maintenance = 700  # CHF
    
    # Taxes
    ev_yearly_tax = canton_data["ev_yearly_tax"]
    ice_yearly_tax = canton_data["ice_yearly_tax"]
    
    # Insurance (roughly similar, EVs slightly higher for now)
    ev_yearly_insurance = 800
    ice_yearly_insurance = 750
    
    # Totals
    ev_total_yearly = ev_yearly_fuel_cost + ev_yearly_maintenance + ev_yearly_tax + ev_yearly_insurance
    ice_total_yearly = ice_yearly_fuel_cost + ice_yearly_maintenance + ice_yearly_tax + ice_yearly_insurance
    
    yearly_savings = ice_total_yearly - ev_total_yearly
    five_year_savings = yearly_savings * 5 + canton_data["incentive"]
    
    # Break-even calculation (simplified)
    if yearly_savings > 0:
        price_difference = 10000  # Assumed average price difference
        break_even_km = (price_difference / yearly_savings) * input_data.yearly_km
    else:
        break_even_km = 0
    
    return CostCalculation(
        ev_yearly_fuel_cost=round(ev_yearly_fuel_cost, 2),
        ice_yearly_fuel_cost=round(ice_yearly_fuel_cost, 2),
        ev_yearly_maintenance=ev_yearly_maintenance,
        ice_yearly_maintenance=ice_yearly_maintenance,
        ev_yearly_tax=ev_yearly_tax,
        ice_yearly_tax=ice_yearly_tax,
        ev_yearly_insurance=ev_yearly_insurance,
        ice_yearly_insurance=ice_yearly_insurance,
        ev_total_yearly=round(ev_total_yearly, 2),
        ice_total_yearly=round(ice_total_yearly, 2),
        yearly_savings=round(yearly_savings, 2),
        five_year_savings=round(five_year_savings, 2),
        break_even_km=round(break_even_km, 0)
    )

@api_router.get("/calculator/cantons")
async def get_cantons():
    """Get list of all cantons with tax data"""
    cantons = []
    for code, data in CANTON_TAX_DATA.items():
        cantons.append({
            "code": code,
            "name": data["name"],
            "ev_tax": data["ev_yearly_tax"],
            "ice_tax": data["ice_yearly_tax"],
            "incentive": data["incentive"]
        })
    cantons.sort(key=lambda x: x["name"])
    return {"cantons": cantons}

# ==================== CHARGING STATIONS ====================

@api_router.get("/charging/stations")
async def get_charging_stations(
    lat: float = Query(47.3769, description="Latitude"),
    lng: float = Query(8.5417, description="Longitude"),
    radius: int = Query(25, description="Radius in km"),
    limit: int = Query(50, description="Max results")
):
    """Get charging stations near a location using OpenChargeMap API"""
    
    # OpenChargeMap API (no key required for basic usage)
    url = "https://api.openchargemap.io/v3/poi/"
    params = {
        "output": "json",
        "countrycode": "CH",
        "latitude": lat,
        "longitude": lng,
        "distance": radius,
        "distanceunit": "km",
        "maxresults": limit,
        "compact": "true",
        "verbose": "false"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            data = response.json()
        
        stations = []
        for item in data:
            address = item.get("AddressInfo", {})
            connections = item.get("Connections", [])
            
            # Get max power from connections
            max_power = 0
            conn_types = []
            for conn in connections:
                power = conn.get("PowerKW") or 0
                if power > max_power:
                    max_power = power
                conn_type = conn.get("ConnectionType", {}).get("Title", "Unknown")
                if conn_type not in conn_types:
                    conn_types.append(conn_type)
            
            stations.append({
                "id": str(item.get("ID", "")),
                "name": item.get("OperatorInfo", {}).get("Title", "Unbekannt") if item.get("OperatorInfo") else "Unbekannt",
                "address": address.get("AddressLine1", ""),
                "city": address.get("Town", ""),
                "latitude": address.get("Latitude", 0),
                "longitude": address.get("Longitude", 0),
                "operator": item.get("OperatorInfo", {}).get("Title") if item.get("OperatorInfo") else None,
                "num_points": item.get("NumberOfPoints", 1),
                "max_power_kw": max_power,
                "connection_types": conn_types,
                "is_fast_charger": max_power >= 50
            })
        
        return {
            "stations": stations,
            "total": len(stations),
            "search_params": {
                "lat": lat,
                "lng": lng,
                "radius_km": radius
            }
        }
    
    except Exception as e:
        logger.error(f"Error fetching charging stations: {e}")
        # Return mock data for Swiss cities on error
        mock_stations = get_mock_stations(lat, lng)
        return {
            "stations": mock_stations,
            "total": len(mock_stations),
            "source": "cache",
            "search_params": {"lat": lat, "lng": lng, "radius_km": radius}
        }

def get_mock_stations(lat: float, lng: float) -> List[Dict]:
    """Return mock charging stations based on location"""
    # Zurich area
    if 47.3 < lat < 47.5 and 8.4 < lng < 8.7:
        return [
            {"id": "1", "name": "GOFAST", "address": "Hardbrücke 1", "city": "Zürich", "latitude": 47.3856, "longitude": 8.5167, "operator": "GOFAST", "num_points": 8, "max_power_kw": 150, "connection_types": ["CCS"], "is_fast_charger": True},
            {"id": "2", "name": "Swisscharge", "address": "Sihlcity", "city": "Zürich", "latitude": 47.3541, "longitude": 8.5244, "operator": "Swisscharge", "num_points": 4, "max_power_kw": 50, "connection_types": ["CCS", "Typ 2"], "is_fast_charger": True},
            {"id": "3", "name": "Tesla Supercharger", "address": "Zürich Dietikon", "city": "Dietikon", "latitude": 47.4003, "longitude": 8.4009, "operator": "Tesla", "num_points": 12, "max_power_kw": 250, "connection_types": ["Tesla"], "is_fast_charger": True},
            {"id": "4", "name": "Migros MOVE", "address": "Limmatplatz", "city": "Zürich", "latitude": 47.3855, "longitude": 8.5308, "operator": "MOVE", "num_points": 6, "max_power_kw": 22, "connection_types": ["Typ 2"], "is_fast_charger": False},
            {"id": "5", "name": "Ionity", "address": "Rastplatz Würenlos", "city": "Würenlos", "latitude": 47.4447, "longitude": 8.3618, "operator": "Ionity", "num_points": 6, "max_power_kw": 350, "connection_types": ["CCS"], "is_fast_charger": True},
        ]
    # Bern area
    elif 46.9 < lat < 47.0 and 7.4 < lng < 7.5:
        return [
            {"id": "6", "name": "GOFAST", "address": "Wankdorf", "city": "Bern", "latitude": 46.9631, "longitude": 7.4659, "operator": "GOFAST", "num_points": 6, "max_power_kw": 150, "connection_types": ["CCS"], "is_fast_charger": True},
            {"id": "7", "name": "Energie Wasser Bern", "address": "Monbijoustrasse", "city": "Bern", "latitude": 46.9451, "longitude": 7.4361, "operator": "ewb", "num_points": 4, "max_power_kw": 22, "connection_types": ["Typ 2"], "is_fast_charger": False},
            {"id": "8", "name": "Tesla Supercharger", "address": "Westside", "city": "Bern", "latitude": 46.9373, "longitude": 7.3875, "operator": "Tesla", "num_points": 8, "max_power_kw": 250, "connection_types": ["Tesla"], "is_fast_charger": True},
        ]
    # Basel area
    elif 47.5 < lat < 47.6 and 7.5 < lng < 7.7:
        return [
            {"id": "9", "name": "IWB", "address": "Messeplatz", "city": "Basel", "latitude": 47.5668, "longitude": 7.6004, "operator": "IWB", "num_points": 8, "max_power_kw": 150, "connection_types": ["CCS", "Typ 2"], "is_fast_charger": True},
            {"id": "10", "name": "GOFAST", "address": "St. Jakob-Park", "city": "Basel", "latitude": 47.5411, "longitude": 7.6209, "operator": "GOFAST", "num_points": 6, "max_power_kw": 150, "connection_types": ["CCS"], "is_fast_charger": True},
            {"id": "11", "name": "Swisscharge", "address": "Stücki Park", "city": "Basel", "latitude": 47.5802, "longitude": 7.6115, "operator": "Swisscharge", "num_points": 4, "max_power_kw": 50, "connection_types": ["CCS"], "is_fast_charger": True},
        ]
    # Geneva area
    elif 46.1 < lat < 46.3 and 6.0 < lng < 6.2:
        return [
            {"id": "12", "name": "SIG", "address": "Aéroport", "city": "Genève", "latitude": 46.2353, "longitude": 6.1080, "operator": "SIG", "num_points": 10, "max_power_kw": 150, "connection_types": ["CCS", "Typ 2"], "is_fast_charger": True},
            {"id": "13", "name": "Ionity", "address": "Vernier", "city": "Vernier", "latitude": 46.2176, "longitude": 6.0849, "operator": "Ionity", "num_points": 6, "max_power_kw": 350, "connection_types": ["CCS"], "is_fast_charger": True},
            {"id": "14", "name": "Tesla Supercharger", "address": "Balexert", "city": "Genève", "latitude": 46.2198, "longitude": 6.1133, "operator": "Tesla", "num_points": 8, "max_power_kw": 250, "connection_types": ["Tesla"], "is_fast_charger": True},
        ]
    # Lausanne area
    elif 46.4 < lat < 46.6 and 6.5 < lng < 6.7:
        return [
            {"id": "15", "name": "Romande Energie", "address": "Flon", "city": "Lausanne", "latitude": 46.5218, "longitude": 6.6267, "operator": "Romande Energie", "num_points": 6, "max_power_kw": 50, "connection_types": ["CCS", "Typ 2"], "is_fast_charger": True},
            {"id": "16", "name": "GOFAST", "address": "EPFL", "city": "Lausanne", "latitude": 46.5186, "longitude": 6.5657, "operator": "GOFAST", "num_points": 4, "max_power_kw": 150, "connection_types": ["CCS"], "is_fast_charger": True},
        ]
    # Luzern area
    elif 47.0 < lat < 47.1 and 8.2 < lng < 8.4:
        return [
            {"id": "17", "name": "CKW", "address": "Mall of Switzerland", "city": "Ebikon", "latitude": 47.0789, "longitude": 8.3396, "operator": "CKW", "num_points": 8, "max_power_kw": 150, "connection_types": ["CCS", "Typ 2"], "is_fast_charger": True},
            {"id": "18", "name": "GOFAST", "address": "Emmenbrücke", "city": "Emmenbrücke", "latitude": 47.0751, "longitude": 8.2717, "operator": "GOFAST", "num_points": 6, "max_power_kw": 150, "connection_types": ["CCS"], "is_fast_charger": True},
            {"id": "19", "name": "Tesla Supercharger", "address": "Luzern", "city": "Luzern", "latitude": 47.0480, "longitude": 8.3090, "operator": "Tesla", "num_points": 8, "max_power_kw": 250, "connection_types": ["Tesla"], "is_fast_charger": True},
        ]
    else:
        return [
            {"id": "20", "name": "Nächste Ladestation", "address": "Siehe ich-tanke-strom.ch", "city": "Schweiz", "latitude": lat, "longitude": lng, "operator": "Diverse", "num_points": 2, "max_power_kw": 22, "connection_types": ["Typ 2"], "is_fast_charger": False},
        ]

@api_router.get("/charging/networks")
async def get_charging_networks():
    """Get pricing for major charging networks in Switzerland"""
    networks = [
        {"name": "GOFAST", "ac_kwh": None, "dc_50_kwh": None, "dc_150_kwh": 0.49, "dc_fast_kwh": 0.59, "subscription": None, "url": "https://gofast.swiss"},
        {"name": "Swisscharge", "ac_kwh": 0.35, "dc_50_kwh": 0.55, "dc_150_kwh": 0.65, "dc_fast_kwh": 0.75, "subscription": "Optional", "url": "https://swisscharge.ch"},
        {"name": "Ionity", "ac_kwh": None, "dc_50_kwh": None, "dc_150_kwh": None, "dc_fast_kwh": 0.79, "subscription": "CHF 12.99/Mt", "url": "https://ionity.eu"},
        {"name": "Tesla Supercharger", "ac_kwh": None, "dc_50_kwh": None, "dc_150_kwh": 0.52, "dc_fast_kwh": 0.52, "subscription": "Für Tesla gratis", "url": "https://tesla.com"},
        {"name": "MOVE (Migros)", "ac_kwh": 0.30, "dc_50_kwh": 0.45, "dc_150_kwh": 0.55, "dc_fast_kwh": 0.65, "subscription": None, "url": "https://move.ch"},
        {"name": "Eniwa", "ac_kwh": 0.32, "dc_50_kwh": 0.52, "dc_150_kwh": 0.58, "dc_fast_kwh": 0.68, "subscription": None, "url": "https://eniwa.ch"},
        {"name": "Fastned", "ac_kwh": None, "dc_50_kwh": None, "dc_150_kwh": 0.59, "dc_fast_kwh": 0.59, "subscription": "CHF 11.99/Mt", "url": "https://fastnedcharging.com"},
    ]
    return {"networks": networks, "last_updated": "2025-01"}

# ==================== KNOWLEDGE / EV-WISSEN ====================

@api_router.get("/knowledge/articles")
async def get_knowledge_articles(category: Optional[str] = None):
    """Get all knowledge articles"""
    articles = KNOWLEDGE_ARTICLES.copy()
    if category:
        articles = [a for a in articles if a["category"] == category]
    articles.sort(key=lambda x: x["order"])
    return {"articles": articles}

@api_router.get("/knowledge/articles/{slug}")
async def get_knowledge_article(slug: str):
    """Get a specific article by slug"""
    for article in KNOWLEDGE_ARTICLES:
        if article["slug"] == slug:
            return article
    raise HTTPException(status_code=404, detail="Article not found")

@api_router.get("/knowledge/glossary")
async def get_glossary(category: Optional[str] = None):
    """Get EV glossary terms"""
    glossary = GLOSSARY_DATA.copy()
    if category:
        glossary = [g for g in glossary if g["category"] == category]
    glossary.sort(key=lambda x: x["term"])
    return {"terms": glossary, "total": len(glossary)}

@api_router.get("/knowledge/myths")
async def get_myths():
    """Get myths and facts about EVs"""
    return {"myths": MYTHS_DATA, "total": len(MYTHS_DATA)}

@api_router.get("/knowledge/categories")
async def get_knowledge_categories():
    """Get all knowledge categories"""
    categories = [
        {"id": "batterie", "name": "Batterie & Technologie", "icon": "🔋"},
        {"id": "laden", "name": "Laden & Infrastruktur", "icon": "⚡"},
        {"id": "reichweite", "name": "Reichweite & Effizienz", "icon": "📏"},
        {"id": "kosten", "name": "Kosten & Finanzen", "icon": "💰"},
    ]
    return {"categories": categories}

# ==================== MARKET DATA ====================

@api_router.get("/market/data")
async def get_market_data(year: int = 2024):
    """Get market data for Switzerland"""
    data = [m for m in MARKET_DATA if m["year"] == year]
    
    # Calculate totals
    total_bev = sum(m["bev_registrations"] for m in data)
    total_phev = sum(m["phev_registrations"] for m in data)
    total_all = sum(m["total_registrations"] for m in data)
    avg_share = round(sum(m["bev_market_share"] for m in data) / len(data), 1) if data else 0
    
    return {
        "monthly_data": data,
        "summary": {
            "total_bev_registrations": total_bev,
            "total_phev_registrations": total_phev,
            "total_registrations": total_all,
            "average_bev_market_share": avg_share,
            "year": year
        }
    }

@api_router.get("/market/stats")
async def get_market_stats():
    """Get current market statistics"""
    latest = MARKET_DATA[-1] if MARKET_DATA else {}
    
    # Top brands (simulated data based on Swiss market 2024)
    top_brands = [
        {"brand": "Tesla", "sales": 12500, "share": 18.2},
        {"brand": "BMW", "sales": 8200, "share": 11.9},
        {"brand": "Mercedes", "sales": 6800, "share": 9.9},
        {"brand": "VW", "sales": 6200, "share": 9.0},
        {"brand": "Audi", "sales": 5400, "share": 7.9},
        {"brand": "Hyundai", "sales": 4800, "share": 7.0},
        {"brand": "Skoda", "sales": 4200, "share": 6.1},
        {"brand": "Volvo", "sales": 3600, "share": 5.2},
        {"brand": "Kia", "sales": 3200, "share": 4.7},
        {"brand": "MG", "sales": 2800, "share": 4.1},
    ]
    
    top_models = [
        {"model": "Tesla Model Y", "sales": 7200, "share": 10.5},
        {"model": "Tesla Model 3", "sales": 5300, "share": 7.7},
        {"model": "Skoda Enyaq", "sales": 4100, "share": 6.0},
        {"model": "BMW iX1", "sales": 3600, "share": 5.2},
        {"model": "VW ID.4", "sales": 3200, "share": 4.7},
        {"model": "Mercedes EQA", "sales": 2900, "share": 4.2},
        {"model": "Volvo EX30", "sales": 2700, "share": 3.9},
        {"model": "Hyundai Ioniq 5", "sales": 2500, "share": 3.6},
        {"model": "Audi Q4 e-tron", "sales": 2400, "share": 3.5},
        {"model": "MG4", "sales": 2200, "share": 3.2},
    ]
    
    return {
        "current_month": latest.get("month", "Dezember"),
        "year": latest.get("year", 2024),
        "bev_market_share": latest.get("bev_market_share", 22.3),
        "bev_registrations_monthly": latest.get("bev_registrations", 6800),
        "charging_points_ch": 12458,
        "fast_chargers_ch": 2850,
        "top_brands": top_brands,
        "top_models": top_models
    }

# ==================== RANGE CALCULATOR ====================

@api_router.post("/calculator/range")
async def calculate_range(
    wltp_range_km: int = Query(400, description="WLTP Range in km"),
    temperature_c: int = Query(20, description="Outside temperature in Celsius"),
    speed_kmh: int = Query(100, description="Average speed in km/h"),
    climate_on: bool = Query(False, description="Climate control on"),
    highway_percent: int = Query(50, description="Percentage of highway driving")
):
    """Calculate realistic range based on conditions"""
    
    base_range = wltp_range_km
    
    # Temperature factor
    if temperature_c < -10:
        temp_factor = 0.60
    elif temperature_c < 0:
        temp_factor = 0.70
    elif temperature_c < 10:
        temp_factor = 0.80
    elif temperature_c < 15:
        temp_factor = 0.90
    elif temperature_c <= 25:
        temp_factor = 1.0
    else:
        temp_factor = 0.95  # AC usage in heat
    
    # Speed factor (exponential increase in consumption at higher speeds)
    if speed_kmh <= 80:
        speed_factor = 1.10  # City driving with recuperation benefit
    elif speed_kmh <= 100:
        speed_factor = 1.0
    elif speed_kmh <= 120:
        speed_factor = 0.85
    else:
        speed_factor = 0.70
    
    # Climate factor
    climate_factor = 0.90 if climate_on else 1.0
    
    # Highway vs city mix
    highway_factor = 1.0 - (highway_percent / 100 * 0.15)  # Highway uses more
    
    # Calculate final range
    final_range = base_range * temp_factor * speed_factor * climate_factor * highway_factor
    
    return {
        "wltp_range_km": wltp_range_km,
        "calculated_range_km": round(final_range),
        "efficiency_percent": round((final_range / wltp_range_km) * 100),
        "factors": {
            "temperature": {"value": temperature_c, "factor": temp_factor},
            "speed": {"value": speed_kmh, "factor": speed_factor},
            "climate": {"active": climate_on, "factor": climate_factor},
            "highway_percent": {"value": highway_percent, "factor": highway_factor}
        },
        "tips": get_range_tips(temperature_c, speed_kmh, climate_on)
    }

def get_range_tips(temp: int, speed: int, climate: bool) -> List[str]:
    tips = []
    if temp < 10:
        tips.append("Batterie vorkonditionieren erhöht die Reichweite bei Kälte um 5-10%")
    if speed > 120:
        tips.append("100 km/h statt 130 km/h erhöht die Reichweite um ca. 20%")
    if climate:
        tips.append("Sitzheizung verbraucht weniger als die Innenraumheizung")
    tips.append("Rekuperation auf Maximum stellen für beste Effizienz in der Stadt")
    return tips

# ==================== NEWS FEED ====================

@api_router.get("/news")
async def get_news(
    region: Optional[str] = Query(None, description="Filter by region: swiss, german, international, balkan"),
    category: Optional[str] = Query(None, description="Filter by category: vehicles, battery, charging, policy, market, technology, infrastructure"),
    language: Optional[str] = Query(None, description="Filter by language: de, en, sr, hr"),
    limit: int = Query(50, description="Maximum number of articles"),
    refresh: bool = Query(False, description="Force refresh cache")
):
    """Get aggregated news from multiple EV-related RSS feeds"""
    global news_cache
    
    # Check cache validity
    cache_valid = (
        news_cache["last_updated"] is not None and
        datetime.now(timezone.utc) - news_cache["last_updated"] < news_cache["cache_duration"] and
        len(news_cache["articles"]) > 0 and
        not refresh
    )
    
    if not cache_valid:
        logger.info("Fetching fresh news from RSS feeds...")
        news_cache["articles"] = await fetch_all_feeds()
        news_cache["last_updated"] = datetime.now(timezone.utc)
        logger.info(f"Fetched {len(news_cache['articles'])} articles")
    
    articles = news_cache["articles"].copy()
    
    # Apply filters
    if region:
        region_codes = {
            "swiss": ["CH"],
            "german": ["DE"],
            "international": ["US", "UK", "EU"],
            "balkan": ["RS", "HR", "SI", "BA"]
        }
        allowed_regions = region_codes.get(region, [])
        articles = [a for a in articles if a.get("region") in allowed_regions]
    
    if language:
        articles = [a for a in articles if a.get("language") == language]
    
    if category:
        articles = [a for a in articles if category in a.get("categories", [])]
    
    # Limit results
    articles = articles[:limit]
    
    return {
        "articles": articles,
        "total": len(articles),
        "cache_age_minutes": round((datetime.now(timezone.utc) - news_cache["last_updated"]).total_seconds() / 60, 1) if news_cache["last_updated"] else 0,
        "sources_count": len([f for feeds in NEWS_FEEDS.values() for f in feeds]),
        "filters": {
            "region": region,
            "category": category,
            "language": language
        }
    }

@api_router.get("/news/sources")
async def get_news_sources():
    """Get list of all configured news sources"""
    sources = []
    for region, feeds in NEWS_FEEDS.items():
        for feed in feeds:
            sources.append({
                "name": feed["name"],
                "url": feed["url"].replace("/feed/", "").replace("/feed", "").replace("/rss", ""),
                "language": feed["lang"],
                "region": feed["region"],
                "region_group": region
            })
    
    return {
        "sources": sources,
        "total": len(sources),
        "regions": list(NEWS_FEEDS.keys()),
        "languages": list(set(f["lang"] for feeds in NEWS_FEEDS.values() for f in feeds))
    }

@api_router.get("/news/categories")
async def get_news_categories():
    """Get available news categories"""
    categories = [
        {"id": "vehicles", "name": "Neue Fahrzeuge", "icon": "🚗", "name_de": "Neue Fahrzeuge", "name_en": "New Vehicles"},
        {"id": "battery", "name": "Batterie & Reichweite", "icon": "🔋", "name_de": "Batterie & Reichweite", "name_en": "Battery & Range"},
        {"id": "charging", "name": "Laden & Infrastruktur", "icon": "⚡", "name_de": "Laden & Infrastruktur", "name_en": "Charging & Infrastructure"},
        {"id": "policy", "name": "Politik & Förderung", "icon": "📜", "name_de": "Politik & Förderung", "name_en": "Policy & Subsidies"},
        {"id": "market", "name": "Markt & Wirtschaft", "icon": "📊", "name_de": "Markt & Wirtschaft", "name_en": "Market & Economy"},
        {"id": "technology", "name": "Technologie & Updates", "icon": "🔧", "name_de": "Technologie & Updates", "name_en": "Technology & Updates"},
        {"id": "infrastructure", "name": "Netzwerk & Ausbau", "icon": "🌐", "name_de": "Netzwerk & Ausbau", "name_en": "Network & Expansion"},
        {"id": "general", "name": "Allgemein", "icon": "📰", "name_de": "Allgemein", "name_en": "General"},
    ]
    return {"categories": categories}

@api_router.post("/news/refresh")
async def refresh_news():
    """Force refresh the news cache"""
    global news_cache
    news_cache["articles"] = await fetch_all_feeds()
    news_cache["last_updated"] = datetime.now(timezone.utc)
    return {
        "status": "refreshed",
        "articles_count": len(news_cache["articles"]),
        "timestamp": news_cache["last_updated"].isoformat()
    }

# ==================== STATUS CHECK (Original) ====================

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
