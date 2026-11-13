"""
Módulo de Modelos de Datos (models.py)
Define esquemas de Pydantic y adaptadores para ObjectId de MongoDB.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

class _ObjectIdPydanticAnnotation:
    """Adaptador para validar y serializar ObjectId de MongoDB en Pydantic v2"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(v):
            if isinstance(v, ObjectId):
                return str(v)
            if isinstance(v, str) and ObjectId.is_valid(v):
                return v
            raise ValueError("ID invalido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )

# Tipo de dato reutilizable para Pydantic
PyObjectId = Annotated[str, _ObjectIdPydanticAnnotation]


class OrdenServicioBase(BaseModel):
    placa_vehiculo: str = Field(
        ...,
        min_length=5,
        max_length=10,
        description="Placa del vehículo ingresado al taller",
        example="ABC-123"
    )
    descripcion_falla: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Descripción detallada de la falla o servicio requerido",
        example="Cambio de kit de embrague y revisión general de frenos"
    )
    costo_estimado: float = Field(
        ...,
        gt=0,
        description="Costo estimado de la reparación en pesos (COP)",
        example=450000.0
    )
    reparado: bool = Field(
        default=False,
        description="Estado de reparación del vehículo"
    )


class OrdenServicioCreate(OrdenServicioBase):
    """Modelo utilizado para recibir solicitudes POST de creación"""
    pass


class OrdenServicioUpdate(BaseModel):
    """Modelo para solicitudes PUT (Campos opcionales para edición)"""
    placa_vehiculo: Optional[str] = Field(None, min_length=5, max_length=10)
    descripcion_falla: Optional[str] = Field(None, min_length=5, max_length=500)
    costo_estimado: Optional[float] = Field(None, gt=0)
    reparado: Optional[bool] = None


class OrdenServicio(OrdenServicioBase):
    """Modelo completo de respuesta que incluye el ID de MongoDB y la fecha"""
    id: PyObjectId = Field(alias="_id", description="Identificador único ObjectId de MongoDB")
    fecha_creacion: datetime = Field(default_factory=datetime.now, description="Fecha de registro")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "654321789abcdef012345678",
                "placa_vehiculo": "ABC-123",
                "descripcion_falla": "Cambio de kit de embrague y revisión general de frenos",
                "costo_estimado": 450000.0,
                "reparado": False,
                "fecha_creacion": "2026-11-13T10:30:00"
            }
        }
    )