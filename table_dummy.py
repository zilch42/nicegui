from datetime import datetime, timedelta

import pandas as pd

from nicegui import ui

df = pd.DataFrame({
    'Datetime_col': [datetime(2020, 1, 1)],
    'Timedelta_col': [timedelta(days=5)],
    'Complex_col': [1 + 2j],
    'Period_col': pd.Series([pd.Period('2021-01')]),
})


@ui.page('/')
def home():
    ui.table.from_pandas(df)


ui.run()
