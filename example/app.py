from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import httpx
import requests
import uvicorn
from fastapi import FastAPI
from fastapi_block_hunter import add_block_hunter_middleware, setup_asyncio_debug_mode


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict[Any, Any], Any]:
    await setup_asyncio_debug_mode()
    yield {}


app = FastAPI(lifespan=lifespan)
app = add_block_hunter_middleware(app)


@app.get("/posts")
async def get_posts():
    # Running a blocking call
    response = requests.get("https://jsonplaceholder.typicode.com/posts")
    return response.json()


@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    # This won't block the event loop
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")
    return response.json()


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=4320, reload=True, loop="asyncio")
