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
from app.models.modelref import ModelRef
from app.models.partref import PartRef
from app.models.crs import CRS
from app.models.att import ATT
from app.models.gms import GMS
from app.models.spams import SPAMS
from app.models.cb_pcb import CBPCB
from app.models.insp2 import INSP2
from app.models.insp3_run import INSP3Run
from app.models.insp3_vib import INSP3Vib
from app.models.insp4 import INSP4
from app.models.repair import Repair
from app.models.line import Line
from app.models.module import Module
from app.models.tag import Tag

from app.models.audit import AuditLog

__all__ = [
    'db',
    'User', 'Line', 'Module', 'Tag',
    'WorkSched', 'ModelRef', 'PartRef', 'CRS', 'ATT', 'GMS',
    'SPAMS', 'CBPCB', 'INSP2', 'INSP3Run', 'INSP3Vib', 'INSP4', 'Repair',
    'AuditLog',
]
