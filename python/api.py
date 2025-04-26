import logging

from fastapi import FastAPI, HTTPException
from typing import List
from classes import Item
from alloy_logging_handler import AlloyHandler

from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry import trace

# Set up OpenTelemetry tracing
tracer_provider = TracerProvider()
trace.set_tracer_provider(tracer_provider)

# Configure exporter 
otlp_exporter = OTLPSpanExporter(endpoint="http://tempo:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(AlloyHandler())

app = FastAPI()
Instrumentator().instrument(app).expose(app)
# FastAPIInstrumentor.instrument(app)

# In-memory storage for items
items_db = []


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
