import sys

sys.path.append('../')


from src import start_server
from example.main import app

if __name__ == "__main__":
    start_server(app)