from uvicorn.main import Config, Server
import os
from dotenv import load_dotenv

load_dotenv()


def __run_server():
    reload = os.environ.get("RELOAD", "false").lower() == "true"
    config = Config("asgi:app", port=int(
        os.environ.get("PORT")), host="0.0.0.0", reload=reload)
    server = Server(config)
    server.run()


if __name__ == "__main__":
    print('server running on port 8000')
    __run_server()
