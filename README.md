# 🔍 FastAPI Block Hunter

This is a tool to help you debug blocking calls in your FastAPI application.

It works by:

- 🔄 Adding a middleware to the FastAPI application that will store the current request URL in a context variable.
- 🛠️ Patching the `_format_handle` function from the `asyncio.base_events` module with a custom formatter to print a custom message when a blocking call is detected.

This allows you to identify the blocking call that has blocked the event loop and print the stack trace of the blocking call.

## 📦 Installation

```bash
pip install fastapi-block-hunter
```

## 🚀 Usage

To use the package, you need to add the middleware to your FastAPI application and set up the asyncio debug mode.

```python
from fastapi import FastAPI
from fastapi_block_hunter import add_block_hunter_middleware, setup_asyncio_debug_mode

# You may set up the asyncio debug mode by defining ASYNCIO_DEBUG_MODE=1 as an environment variable.
# Or by calling the setup_asyncio_debug_mode function in your app lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_asyncio_debug_mode(verbose=True)
    yield {}


app = FastAPI(lifespan=lifespan)
app = add_block_hunter_middleware(app, verbose=True)


```

You also need to make sure you use `asyncio` as your `FastAPI` event loop for the package to work. If you have `uvloop` installed, you will need to manually tell your web server to use `asyncio` instead of `uvloop`.

For uvicorn, set the `--loop` option to `asyncio`.

From the uvicorn command line:

```bash
uvicorn --loop asyncio # rest of your startup command
```

Or from your launch script:

```python
from fastapi import FastAPI
    import uvicorn

app = FastAPI()

# ... your FastAPI app setup

if __name__ == "__main__":
    uvicorn.run(app, loop="asyncio")
```

Or from the code:

```python
from fastapi import FastAPI
from fastapi_block_hunter import add_custom_slow_callback_logger

app = FastAPI()
app = add_custom_slow_callback_logger(app)
```

## 📚 Documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
