"""
PMPC Data Logger — SQLAlchemy ORM Models
All models for the plcdata schema.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from typing import Any

class BaseModel(DeclarativeBase):
    query: Any

class _CustomSQLAlchemy(SQLAlchemy):
    Model: type[BaseModel]  # type: ignore[assignment]

db = _CustomSQLAlchemy(model_class=BaseModel)
# Import all models so they register with SQLAlchemy metadata
from app.models.user import User
from app.models.worksched import WorkSched

from app.models.partref import PartRef
from app.models.modelref import ModelRef

from app.models.linestat import LineStat
from app.models.crs import CRS
from app.models.att import ATT
from app.models.gms import GMS

from app.models.spamsi import SPAMSI
from app.models.spamso import SPAMSO
from app.models.wci import WCI
from app.models.rit import RIT
from app.models.fit import FIT

from app.models.line import Line
from app.models.module import Module
from app.models.tag import Tag
from app.models.area import Area
from app.models.pit import PIT

from app.models.shift import Shift

__all__ = [
    'db',
    'User', 'Line', 'Module', 'Tag', 'Area',
    'WorkSched', 'PartRef', 'ModelRef', 'LineStat', 'CRS', 'ATT', 'GMS',
    'SPAMSI', 'SPAMSO', 'WCI', 'RIT', 'FIT', 'PIT',
    'Shift', 'TransferSlip'
]

from .transfer_slip import TransferSlip
