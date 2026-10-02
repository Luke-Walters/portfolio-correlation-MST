"""
Universe-selection widgets for the MST notebook.

Adapted from Bloomberg BQuant example code. Only the pieces used by
MST.ipynb are kept: a UniversePicker that switches between Index, Fund,
Ticker List, Global Macro Movers and Portfolio inputs.
"""
import ipywidgets as widgets

import bloomberg.bquant.portfolio as bqp


class GenericUniverse(widgets.VBox):
    """Single-ticker input resolved to members/holdings via BQL."""

    def __init__(self, bq_univ_func, univ_label, yellow_key):
        super().__init__()
        self._yellow_key = yellow_key
        self._bq_univ_func = bq_univ_func

        self._input = widgets.Text(
            description=f'Enter {univ_label} Ticker',
            style={'description_width': '115px'},
            layout={'width': '300px'}
        )
        self.children = [self._input]

    def _append_yellow_key(self, ticker):
        return (
            ticker if ticker.upper().endswith(self._yellow_key.upper())
            else f'{ticker} {self._yellow_key}'
        )

    @property
    def value(self):
        ticker = self._append_yellow_key(self._input.value.strip())
        return self._bq_univ_func(ticker).translatesymbols(targetidtype='composite')

    @value.setter
    def value(self, value):
        self._input.value = value


class TickerListUniverse(widgets.VBox):
    """Free-text list of identifiers, one per line."""

    def __init__(self, preset_tickers=None):
        super().__init__()
        self._ticker_input = widgets.Textarea(
            description='Enter Tickers',
            placeholder=('Add a list of identifiers - tickers, ISINs, '
                         'FIGIs, CUSIPs etc ensuring each identifier has '
                         'a yellow key suffix'),
            rows=10,
            style={'description_width': '115px'},
            layout={'width': '300px'}
        )

        clear_button = widgets.Button(
            description='Clear Ticker List',
            layout={'width': '175px', 'margin': '0 0 0 125px', 'height': '27px'},
            style={'font_size': '10px'}
        )
        clear_button.on_click(self._clear_tickers)

        if preset_tickers:
            self.value = preset_tickers

        self.children = [self._ticker_input, clear_button]

    def _clear_tickers(self, event=None):
        self._ticker_input.value = ''

    @property
    def value(self):
        tickers = filter(None, self._ticker_input.value.split('\n'))
        return [x.strip() for x in tickers]

    @value.setter
    def value(self, value):
        if isinstance(value, list):
            self._ticker_input.value = "\n".join(value)
        else:
            self._ticker_input.value = str(value)


class PortfolioUniverse(widgets.HBox):
    """Dropdown of the user's PORT portfolios (loaded on first use).

    The notebook reads the selected portfolio id and label from
    ``_dropdown`` and loads positions/weights itself.
    """

    def __init__(self):
        super().__init__()
        self._portfolios_loaded = False
        self._dropdown = widgets.Dropdown(
            description='Select Portfolio',
            options=[('Loading portfolios...', None)],
            style={'description_width': '115px'},
            layout={'width': '300px'}
        )
        self.children = [self._dropdown]

    def load_portfolios(self):
        if self._portfolios_loaded:
            return
        try:
            ports = bqp.list_portfolios()
            self._dropdown.options = list(zip(
                ports['portfolio_name'], ports['portfolio_id']
            ))
            self._portfolios_loaded = True
        except Exception:
            self._dropdown.options = [('Unable to load portfolios', None)]

    @property
    def value(self):
        return self._dropdown.value

    @value.setter
    def value(self, value):
        self.load_portfolios()
        self._dropdown.value = value

    @property
    def label(self):
        return self._dropdown.label


GLOBAL_MACRO_TICKERS = [
    "SPX Index", "SX5E Index", "UKX Index", "NKY Index", "HSI Index",
    "CL1 Comdty", "GC1 Comdty",
    "EURUSD Curncy", "USDJPY Curncy", "DXY Curncy",
    "USGG10YR Index", "VIX Index",
]


class UniversePicker(widgets.HBox):
    """Dropdown of universe types plus the matching input widget."""

    def __init__(self, bq, univ_types, value=None,
                 description='Select Universe Type', layout=None):
        super().__init__()

        self._univ_types = [univ_type.title() for univ_type in univ_types]
        self._univ_pickers = self._create_pickers(bq)

        self._picker_type_dropdown = widgets.Dropdown(
            description=description,
            options=self._univ_pickers,
            style={'description_width': 'initial'},
            layout=layout or {'width': 'auto'}
        )
        self._picker_type_dropdown.observe(self._update_univ_type, names='value')

        self._univ_picker_box = widgets.HBox([self._picker_type_dropdown.value])
        if value is not None:
            self.value = value
        self.children = [self._picker_type_dropdown, self._univ_picker_box]

    def _create_pickers(self, bq):
        factory = {
            'Index': lambda: GenericUniverse(
                bq_univ_func=bq.univ.members,
                univ_label='Index',
                yellow_key='Index'
            ),
            'Fund': lambda: GenericUniverse(
                bq_univ_func=bq.univ.holdings,
                univ_label='Fund',
                yellow_key='Equity'
            ),
            'Ticker List': TickerListUniverse,
            'Global Macro Movers': lambda: TickerListUniverse(
                preset_tickers=GLOBAL_MACRO_TICKERS
            ),
            'Portfolio': PortfolioUniverse,
        }
        return {ut: factory[ut]() for ut in self._univ_types}

    def _update_univ_type(self, event=None):
        univ_object = self._picker_type_dropdown.value
        self._univ_picker_box.children = [univ_object]
        # Only load the list of portfolios when it is needed
        if isinstance(univ_object, PortfolioUniverse):
            univ_object.load_portfolios()

    @property
    def value(self):
        return self._picker_type_dropdown.value.value

    @value.setter
    def value(self, value):
        self._picker_type_dropdown.value.value = value

    @property
    def universe_type(self):
        return self._picker_type_dropdown.label
