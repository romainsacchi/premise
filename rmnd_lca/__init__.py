__all__ = (
    "InventorySet",
    "DatabaseCleaner",
    "RemindDataCollection",
    "NewDatabase",
    "Electricity",
    "BiofuelInventory",
    "CarmaCCSInventory",
    "Geomap",
    "DATA_DIR"
)
__version__ = (0, 1, 6)

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
INVENTORY_DIR = Path(__file__).resolve().parent / "data" / "additional_inventories"

from .activity_maps import InventorySet
from .clean_datasets import DatabaseCleaner
from .data_collection import RemindDataCollection
from .ecoinvent_modification import NewDatabase
from .electricity import Electricity
from .inventory_imports import CarmaCCSInventory, BiofuelInventory
from .geomap import Geomap
