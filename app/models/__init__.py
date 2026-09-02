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
from app.models.spamsi_unique_ref import SPAMSIUniqueRef
from app.models.spamso_outmodel_ref import SpamsoOutmodelRef
from app.models.linestat import LineStat
from app.models.crs import CRS
from app.models.att import ATT
from app.models.gms import GMS

from app.models.spamsi import SPAMSI
from app.models.spamso import SPAMSO
from app.models.insp2 import INSP2
from app.models.insp3_run import INSP3Run
from app.models.insp4 import INSP4

from app.models.line import Line
from app.models.module import Module
from app.models.tag import Tag
from app.models.area import Area
from app.models.packaging import Packaging

from app.models.shift import Shift

__all__ = [
    'db',
    'User', 'Line', 'Module', 'Tag', 'Area',
    'WorkSched', 'PartRef', 'ModelRef', 'SPAMSIUniqueRef', 'SpamsoOutmodelRef', 'LineStat', 'CRS', 'ATT', 'GMS',
    'SPAMSI', 'SPAMSO', 'INSP2', 'INSP3Run', 'INSP4', 'Packaging',
    'Shift'
]

from .transfer_slip import TransferSlip
