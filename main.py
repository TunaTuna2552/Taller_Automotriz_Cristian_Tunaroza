"""
Módulo Principal de la Aplicación (main.py)
Instancia FastAPI, gestiona CORS, conexión asíncrona y expone el CRUD con Motor.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson import ObjectId
from datetime import datetime

from models import OrdenServicio, OrdenServicioCreate, OrdenServicioUpdate
from database import coleccion_ordenes, verificar_conexion

# Instancia principal de FastAPI
app = FastAPI(
    title="API Taller Automotriz Profesional - SENA ADSO",
    description="API RESTful asíncrona con FastAPI y MongoDB (FARM Stack).",
    version="1.0.0"
)

# Configuración de CORS para permitir conexión con clientes Frontend (React, Angular, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de inicio del servidor
@app.on_event("startup")
async def startup_db_client():
    await verificar_conexion()


# ============================================
# ENDPOINTS RESTful ASÍNCRONOS
# ============================================

@app.get("/", tags=["Raíz"])
async def root():
    return {
        "mensaje": "Bienvenido a la API de Taller Automotriz Asíncrona con MongoDB (SENA ADSO)",
        "documentacion": "/docs"
    }


@app.post(
    "/ordenes",
    response_model=OrdenServicio,
    status_code=status.HTTP_201_CREATED,
    tags=["Órdenes de Servicio"],
    summary="Crear una nueva orden de servicio en MongoDB"
)
async def create_orden(orden_in: OrdenServicioCreate):
    """
    Guarda una orden de servicio de forma asíncrona en la colección 'ordenes_taller' de MongoDB:
    - Asigna la fecha de creación actual.
    - Evita placas duplicadas (Lanza HTTP 400 Bad Request).
    """
    # 1. Validar que no exista otra orden con la misma placa de vehículo
    orden_existente = await coleccion_ordenes.find_one({"placa_vehiculo": orden_in.placa_vehiculo})
    if orden_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una orden registrada con la placa '{orden_in.placa_vehiculo}'."
        )

    # 2. Preparar el diccionario del documento
    nueva_orden = orden_in.model_dump()
    nueva_orden["fecha_creacion"] = datetime.now()

    # 3. Insertar asíncronamente en MongoDB
    resultado = await coleccion_ordenes.insert_one(nueva_orden)

    # 4. Recuperar el documento recién creado por su _id ObjectId
    orden_creada = await coleccion_ordenes.find_one({"_id": resultado.inserted_id})
    return orden_creada


@app.get(
    "/ordenes",
    response_model=List[OrdenServicio],
    status_code=status.HTTP_200_OK,
    tags=["Órdenes de Servicio"],
    summary="Listar todas las órdenes de servicio"
)
async def get_ordenes():
    """Recupera asíncronamente todos los documentos de la colección de MongoDB."""
    ordenes = []
    # Usar cursor asíncrono de Motor
    cursor = coleccion_ordenes.find()
    async for documento in cursor:
        ordenes.append(documento)
    return ordenes


@app.get(
    "/ordenes/{id}",
    response_model=OrdenServicio,
    status_code=status.HTTP_200_OK,
    tags=["Órdenes de Servicio"],
    summary="Buscar orden de servicio por ObjectId"
)
async def get_orden_por_id(id: str):
    """Busca una orden de servicio específica por su ObjectId de MongoDB."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido de MongoDB."
        )

    orden = await coleccion_ordenes.find_one({"_id": ObjectId(id)})
    if orden:
        return orden

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"La orden de servicio con ID '{id}' no fue encontrada en la base de datos."
    )


@app.put(
    "/ordenes/{id}",
    response_model=OrdenServicio,
    status_code=status.HTTP_200_OK,
    tags=["Órdenes de Servicio"],
    summary="Actualizar estado o campos de una orden de servicio"
)
async def update_orden(id: str, orden_update: OrdenServicioUpdate):
    """Actualiza los campos de un documento en MongoDB por su _id."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido."
        )

    # Extraer solo los datos enviados en la petición
    datos_a_actualizar = orden_update.model_dump(exclude_unset=True)

    if len(datos_a_actualizar) >= 1:
        resultado_actualizacion = await coleccion_ordenes.update_one(
            {"_id": ObjectId(id)},
            {"$set": datos_a_actualizar}
        )

        if resultado_actualizacion.modified_count == 1 or resultado_actualizacion.matched_count == 1:
            orden_modificada = await coleccion_ordenes.find_one({"_id": ObjectId(id)})
            return orden_modificada

    # Si no se modificó o no se encontró el ID
    orden_existente = await coleccion_ordenes.find_one({"_id": ObjectId(id)})
    if orden_existente:
        return orden_existente

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible actualizar. La orden de servicio con ID '{id}' no existe."
    )


@app.delete(
    "/ordenes/{id}",
    status_code=status.HTTP_200_OK,
    tags=["Órdenes de Servicio"],
    summary="Eliminar orden de servicio de MongoDB"
)
async def delete_orden(id: str):
    """Elimina permanentemente un documento de MongoDB por su ObjectId."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido."
        )

    resultado_eliminacion = await coleccion_ordenes.delete_one({"_id": ObjectId(id)})

    if resultado_eliminacion.deleted_count == 1:
        return {"mensaje": f"Orden de servicio con ID '{id}' eliminada exitosamente de MongoDB."}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible eliminar. La orden de servicio con ID '{id}' no existe en la base de datos."
    )