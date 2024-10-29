import math
from io import StringIO

import pandas as pd
import requests

from nicegui import run, ui


class DataModel:
    def __init__(self):
        self.planes = None
        self.airports = None
        self.mean = None

    def load(self, planes, airports):
        self.planes = pd.read_csv(StringIO(planes.content.decode('utf-8')))
        self.airports = pd.read_csv(StringIO(airports.content.decode('utf-8')))

    def heavy_computation(self):
        """Run some heavy computation that updates the progress bar through the queue."""
        self.mean = self.planes.year.apply(lambda x: math.sqrt(x+1)).mean()


def download_data(URLs):
    response = {k: requests.get(v, timeout=3) for k, v in URLs.items()}
    return response


async def handle_click_async():
    n = ui.notification(message="Downloading Data", spinner=True, type="ongoing", timeout=None)
    response = await run.io_bound(download_data, URLs)
    n.message = "Loading model"
    await run.cpu_bound(myDataModelAsync.load, **response)
    n.message = "Performing calculation"
    await run.cpu_bound(myDataModelAsync.heavy_computation)
    n.message = 'Done!'
    n.spinner = False
    n.icon = 'done'
    n.timeout = 5.0


async def handle_click_normal():
    n = ui.notification(message="Downloading Data", spinner=True, type="ongoing", timeout=None)
    response = download_data(URLs)
    n.message = "Loading model"
    myDataModelNormal.load(**response)
    n.message = "Performing calculation"
    myDataModelNormal.heavy_computation()
    n.message = 'Done!'
    n.spinner = False
    n.icon = 'done'
    n.timeout = 5.0

myDataModelAsync = DataModel()
myDataModelNormal = DataModel()
URLs = {'planes': 'https://raw.githubusercontent.com/tidyverse/nycflights13/main/data-raw/planes.csv',
        'airports': 'https://raw.githubusercontent.com/tidyverse/nycflights13/main/data-raw/airports.csv'}

with ui.row():
    ui.button('Process NYCflights13 Async', on_click=handle_click_async)
    ui.label().bind_text_from(myDataModelAsync, 'mean',
                              backward=lambda x: "no data" if not x else str(x) + " average year")
with ui.row():
    ui.button('Process NYCflights13 Normally', on_click=handle_click_normal)
    ui.label().bind_text_from(myDataModelNormal, 'mean',
                              backward=lambda x: "no data" if not x else str(x) + " average year")

ui.run()
