import logging
import requests
import json

from fastapi import FastAPI, HTTPException
from typing import List
from classes import Item
from alloy_logging_handler import AlloyHandler

from prometheus_fastapi_instrumentator import Instrumentator

# OTel Imports
from opentelemetry.sdk.resources import DEPLOYMENT_ENVIRONMENT, SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import (
    get_tracer_provider,
    set_tracer_provider,
    get_current_span,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(AlloyHandler())

app = FastAPI()
Instrumentator().instrument(app).expose(app)

# In-memory storage for items
items_db = []

def setup_tracing(resource: Resource):
    span_exporter = OTLPSpanExporter(insecure=True, endpoint="http://tempo:4317") # Exports spans to the Open Telemetry Collector (Alloy in this case)
    span_processor = SimpleSpanProcessor(span_exporter) # Processes spans and hands them over to the exporter. In production we would use a BatchSpanProcessor to minimize network load
    trace_provider = TracerProvider(resource=resource) # A factory for tracer objects
    trace_provider.add_span_processor(span_processor)
    set_tracer_provider(trace_provider)

resource = Resource(
    attributes={
        SERVICE_NAME: "api",
        DEPLOYMENT_ENVIRONMENT: "dev",
    }
)

setup_tracing(resource)
tracer = get_tracer_provider().get_tracer(__name__)


@app.post("/items/", response_model=Item)
def create_item(item: Item):
    item.id = len(items_db) + 1
    items_db.append(item)
    return item


@app.get("/items/", response_model=List[Item])
def read_items(skip: int = 0, limit: int = 10):
    logger.info("/items/ endpoint was called")
    return items_db[skip : skip + limit]


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    for item in items_db:
        logger.info(f"Checking item id '{item.id}'")
        if item.id == item_id:
            logger.info("Found the desired item!")
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: Item):
    for index, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            items_db[index] = item
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/items/{item_id}", response_model=Item)
def delete_item(item_id: int):
    for index, item in enumerate(items_db):
        if item.id == item_id:
            deleted_item = items_db.pop(index)
            return deleted_item
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/pokemon_name/", response_model=str)
@tracer.start_as_current_span("get-pokemon-name")
def get_pokemon_name(id: int):
    URL = f"https://pokeapi.co/api/v2/pokemon/{id}"
    response = requests.get(URL)
    logger.info("/get_poke_name/ endpoint was called")
    span = get_current_span()

    if not response.ok:
        span.set_attribute("error", response.content)
        raise HTTPException(
            status_code=500,
            detail=f"PokeAPI did not return a successful response. Details: {response.content}",
        )

    poke_name = json.loads(response.content).get("name")

    if not poke_name:
        span.set_attribute("error", response.content)
        raise HTTPException(
            status_code=500,
            detail=f"PokeAPI response does not include 'name' property. Details: {response.content}",
        )

    span.set_attribute("poke_name", poke_name)
    return poke_name
