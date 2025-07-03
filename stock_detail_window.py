from stock_detail import Ui_Form
from PyQt6.QtWidgets import QDialog, QSizePolicy
from PyQt6.QtCore import Qt
import yfinance as yf
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from mplfinance.original_flavor import candlestick_ohlc
import talib
import numpy as np


class Stock_details(QDialog):
    def __init__(self, ticker, stock_list, parent=None):
        super().__init__(parent)

        self.ticker = ticker
        self.stock_list = stock_list if stock_list else []
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle(f"Stock Details - {ticker}")
        self.data = None
        # self.ui.label.setText(self.ticker)
        if hasattr(self, 'ui'):
            # *** REPLACE 'label' with the ACTUAL objectName of your QLabel ***
            label_object_name = 'label' # Default name if not changed in Designer
            if hasattr(self.ui, label_object_name):
                label_widget = getattr(self.ui, label_object_name)

                # --- Define desired style ---
                font_size = 16  # Example size
                text_color = " #ec407a " # Example color (light grey)
                font_weight = "bold"
                # --- Apply style using specific stylesheet ---
                # This rule targets ONLY the widget with this object name
                label_widget.setStyleSheet(f"""
                    #{label_object_name} {{
                        font-size: {font_size}pt;
                        color: {text_color};
                        font-weight: {font_weight};
                    }}
                """)
                # ---
                label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Set the initial text AFTER applying the style
                label_widget.setText(self.ticker)
            else:
                print(f"Warning: QLabel named '{label_object_name}' not found in UI.")
        else:
             print("Warning: self.ui not found during __init__. Cannot set label text.")
        self.setup_chart()
        self.load_chart_data()
        
        # Set minimum size for better UX
        self.setMinimumSize(800, 600)

    def setup_chart(self):
        """Initialize the chart components: canvas, toolbar, axes, annotation"""
        self.fig = Figure(figsize=(10, 8), facecolor='#121416', constrained_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding,
                                 QSizePolicy.Policy.Expanding)

        # Add navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        #self.toolbar.setStyleSheet("background-color: #2e2e2e;") # Basic styling

        # Check if ui.chartLayout exists before adding widgets
        self.ui.chartLayout.addWidget(self.toolbar)
        self.ui.chartLayout.addWidget(self.canvas)



        # --- Create subplots using GridSpec for better height control ---
        gs = self.fig.add_gridspec(10, 1) # 10 rows, 1 column

        self.ax_price = self.fig.add_subplot(gs[0:6, 0])      # Price/MA (Top 6 rows)
        self.ax_volume = self.fig.add_subplot(gs[6:8, 0], sharex=self.ax_price) # Volume (Middle 2 rows)
        self.ax_rsi = self.fig.add_subplot(gs[8:10, 0], sharex=self.ax_price) # RSI (Bottom 2 rows)
        # --- End GridSpec Setup ---

        # Hide x-tick labels on upper plots, they will show on the bottom (ax_rsi)
        plt.setp(self.ax_price.get_xticklabels(), visible=False)
        plt.setp(self.ax_volume.get_xticklabels(), visible=False)

        # Setup hover annotation (attached to the main price axis)
        self.annot = self.ax_price.annotate("", xy=(0,0), xytext=(-50,30), # Adjusted offset
                         textcoords="offset points",
                         bbox=dict(boxstyle="round", fc="#202020", ec="white", lw=0.5, alpha=0.9),
                         arrowprops=dict(arrowstyle="-|>", connectionstyle="arc3,rad=-0.3",
                                         color="white", lw=0.5),
                         color='white', # Text color
                         fontsize=8) # Smaller font
        self.annot.set_visible(False)
        self.current_hover_index = -1 # Track index to avoid redundant updates

        # Connect events
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        # Use leave_axes_event for better detection when leaving plot area
        self.fig.canvas.mpl_connect('axes_leave_event', self.on_leave)


    def _format_price_chart(self, ax):
        """Formats the main candlestick/price chart axis"""
        ax.set_facecolor('#091217')
        ax.grid(True, color='#2e2e2e', linestyle='-', linewidth=0.5, alpha=0.7)
        ax.yaxis.tick_left()
        ax.yaxis.set_label_position("left")
        ax.tick_params(axis='y', colors='white', labelsize=8)
        ax.tick_params(axis='x', colors='white', labelsize=8) # Keep x-axis ticks styled even if labels are hidden

        leg = ax.legend(loc='upper left', facecolor='#121416', edgecolor='none', fontsize=8)
        if leg:
            for text in leg.get_texts():
                text.set_color('white')

        ax.spines['bottom'].set_color('#808080')
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_color('#808080')
        ax.spines['right'].set_visible(False)
        ax.set_ylabel("Price", color="white", fontsize=9)


    def _format_indicator_chart(self, ax, title=""):
        """Formats indicator axes (volume, RSI)"""
        ax.set_facecolor('#091217')
        ax.grid(True, color='#2e2e2e', linestyle='-', linewidth=0.5, alpha=0.7)
        ax.text(0.01, 0.95, title, transform=ax.transAxes,
                color='white', fontsize=9, va='top', ha='left')

        ax.yaxis.tick_left()
        ax.yaxis.set_label_position("left")
        ax.tick_params(axis='y', colors='white', labelsize=7)
        ax.tick_params(axis='x', colors='white', labelsize=8) # Keep x-axis ticks styled

        ax.spines['bottom'].set_color('#808080')
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_color('#808080')
        ax.spines['right'].set_visible(False)


    def load_chart_data(self):
        """Load and plot the stock data"""
        try:
            stock = yf.Ticker(self.ticker)
            self.data = stock.history(period='6mo', interval='1d')

            if self.data.empty:
                self.ax_price.text(0.5, 0.5, f"No data found for {self.ticker}",
                                   color="orange", ha="center", va="center", transform=self.ax_price.transAxes)
                self.canvas.draw()
                return

            # --- Data Preparation ---
            # Ensure index is DatetimeIndex (important for labels)
            self.data.index = pd.to_datetime(self.data.index)
            # Store the original DatetimeIndex for later use (labels, hover)
            self.datetime_index = self.data.index

            # **NO reset_index NEEDED for plotting if using numerical positions**

            # Calculate Indicators
            close_col = 'Close' if 'Close' in self.data.columns else 'close'
            if close_col not in self.data.columns:
                 raise ValueError(f"'{close_col}' column not found in data.")

            self.data['MA20'] = self.data[close_col].rolling(20).mean()
            self.data['MA50'] = self.data[close_col].rolling(50).mean()
            self.data['RSI'] = talib.RSI(self.data[close_col].values, timeperiod=14) # Use .values for numpy array input

            # --- Create numerical indices for plotting ---
            plot_indices = np.arange(len(self.data)) # Use numpy array [0, 1, 2...]

            # --- Clear previous plots ---
            self.ax_price.clear()
            self.ax_volume.clear()
            self.ax_rsi.clear()

            # --- Plot Price Chart (ax_price) ---
            # Prepare data for candlestick_ohlc (needs numerical index, O, H, L, C)
            ohlc_vals = self.data[['Open', 'High', 'Low', close_col]].values
            # Combine numerical indices and OHLC values
            ohlc_data = np.column_stack((plot_indices, ohlc_vals))

            candlestick_ohlc(self.ax_price, ohlc_data, width=0.6,
                             colorup='#18b800', colordown='#ff3503', alpha=0.8)

            # Plot MAs using numerical indices
            self.ax_price.plot(plot_indices, self.data['MA20'], color='#FFA500', linewidth=1, label='MA20')
            self.ax_price.plot(plot_indices, self.data['MA50'], color='#08a0e9', linewidth=1, label='MA50')
            self._format_price_chart(self.ax_price)

            self._format_price_chart(self.ax_price)

            # --- Plot Volume Chart (ax_volume) ---
            open_col = 'Open' if 'Open' in self.data.columns else 'open'
            colors = ['#18b800' if c >= o else '#ff3503' for c, o in zip(self.data[close_col], self.data[open_col])]
            # Use numerical indices for plotting
            self.ax_volume.bar(plot_indices, self.data['Volume'], color=colors, width=0.6, alpha=0.7)
            self._format_indicator_chart(self.ax_volume, "Volume")
            self.ax_volume.yaxis.set_major_formatter(mticker.FormatStrFormatter('% .1e'))
            self.ax_volume.set_ylabel("Volume", color="white", fontsize=9)

            # --- Plot RSI Chart (ax_rsi) ---
            # Find numerical indices where RSI is valid (not NaN)
            valid_rsi_mask = self.data['RSI'].notna()
            rsi_plot_indices = plot_indices[valid_rsi_mask]
            rsi_values = self.data['RSI'][valid_rsi_mask].values

            if len(rsi_plot_indices) > 0: # Check if there's any valid RSI data
                self.ax_rsi.plot(rsi_plot_indices, rsi_values, color='#FFA500', linewidth=1)
                self.ax_rsi.axhline(70, color='#ff3503', linestyle='--', linewidth=0.7, alpha=0.8)
                self.ax_rsi.axhline(30, color='#18b800', linestyle='--', linewidth=0.7, alpha=0.8)
                # Place text relative to the last numerical index
                self.ax_rsi.text(plot_indices[-1] * 1.01, 70, '70', color='#ff3503', va='center', ha='left', fontsize=7)
                self.ax_rsi.text(plot_indices[-1] * 1.01, 30, '30', color='#18b800', va='center', ha='left', fontsize=7)
            else:
                self.ax_rsi.text(0.5, 0.5, "Not enough data for RSI", color="orange", ha="center", va="center", transform=self.ax_rsi.transAxes)


            self._format_indicator_chart(self.ax_rsi, "RSI (14)")
            self.ax_rsi.set_ylim(0, 100)
            self.ax_rsi.set_yticks([30, 50, 70])
            self.ax_rsi.set_ylabel("RSI", color="white", fontsize=9)

            # --- Format X-axis Date Labels (on bottom plot ax_rsi) ---
            # Use the stored DatetimeIndex for labels, but positions are numerical
            self.ax_rsi.xaxis.set_major_locator(mticker.MaxNLocator(nbins=8, prune='both'))

            # Formatter maps numerical index back to Date from stored index
            date_index = self.datetime_index # Use the stored index
            def date_format_func(value, tick_number):
                idx = int(np.round(value)) # Round the float value to get integer index
                if 0 <= idx < len(date_index):
                    return date_index[idx].strftime('%Y-%m-%d')
                else:
                    return '' # Return empty string for out-of-bounds indices
            self.ax_rsi.xaxis.set_major_formatter(plt.FuncFormatter(date_format_func))
            self.fig.autofmt_xdate(rotation=15, ha='center')

            # Adjust limits based on numerical index length
            if len(self.data[close_col]) > 0: # Check if data exists before min/max
                pad = (self.data[close_col].max() - self.data[close_col].min()) * 0.05
                # Handle case where min/max are the same (add fixed padding)
                if pad == 0: pad = self.data[close_col].iloc[0] * 0.05 if len(self.data[close_col]) > 0 else 1
                self.ax_price.set_ylim(self.data[close_col].min() - pad, self.data[close_col].max() + pad)
            self.ax_price.set_xlim(-1, len(self.data)) # Use length for numerical index limit

            # --- Final Draw ---
            self.canvas.draw()

        except Exception as e:
            print(f"Error loading chart data for {self.ticker}: {e}")
            # Display error on the chart
            self.ax_price.clear()
            self.ax_volume.clear()
            self.ax_rsi.clear()
            self.ax_price.text(0.5, 0.5, f"Error loading data:\n{e}", color="red",
                               ha="center", va="center", transform=self.ax_price.transAxes)
            # Redraw canvas even on error to show the message
            try:
                self.canvas.draw()
            except Exception:
                pass # Avoid further errors if canvas drawing fails

    def on_hover(self, event):
        """Handle mouse hover events to display data annotations."""
        # Check if data is loaded and event is within the price axes
        # Also check if datetime_index exists
        if self.data is None or not hasattr(self, 'datetime_index') or event.inaxes != self.ax_price:
            if self.annot.get_visible():
                 self.annot.set_visible(False)
                 self.canvas.draw_idle()
            return

        try:
            # xdata is the numerical index in this setup
            x0 = int(round(event.xdata))

            # Check bounds and if the index has changed
            if not (0 <= x0 < len(self.data)) or x0 == self.current_hover_index:
                 if not (0 <= x0 < len(self.data)) and self.annot.get_visible():
                      self.annot.set_visible(False)
                      self.current_hover_index = -1
                      self.canvas.draw_idle()
                 return

            self.current_hover_index = x0
            # Use iloc to get data by numerical position
            point_data = self.data.iloc[x0]
            # Get the corresponding date from the stored datetime_index
            date_obj = self.datetime_index[x0]
            date_str = date_obj.strftime('%Y-%m-%d')

            # Prepare annotation text
            close_col = 'Close' if 'Close' in point_data else 'close'
            annot_text = (f"{date_str}\n"
                          f"O: {point_data['Open']:.2f}  H: {point_data['High']:.2f}\n"
                          f"L: {point_data['Low']:.2f}  C: {point_data[close_col]:.2f}\n"
                          f"V: {point_data['Volume']:,.0f}")
            # Access RSI from the original dataframe using the numerical index x0
            if 'RSI' in self.data.columns and pd.notna(self.data['RSI'].iloc[x0]):
                 annot_text += f"\nRSI: {self.data['RSI'].iloc[x0]:.2f}"

            # Update annotation position and text
            self.annot.xy = (x0, point_data['High'] * 1.005) # x0=numerical index
            self.annot.set_text(annot_text)
            self.annot.set_visible(True)
            self.canvas.draw_idle()

        except Exception as e:
            # print(f"Hover error: {e}") # Optional debug print
            self.annot.set_visible(False)
            self.current_hover_index = -1
            if event.canvas is not None:
                event.canvas.draw_idle()

    def on_leave(self, event):
        """Handle mouse leaving the axes area."""
        # Reset hover index and hide annotation
        self.current_hover_index = -1
        if self.annot.get_visible():
            self.annot.set_visible(False)
            if event.canvas is not None:
                event.canvas.draw_idle()
    
    def keyPressEvent(self, event):
        """Handle Left/Right arrow key presses for stock navigation."""
        current_key = event.key()
        navigate = False
        new_ticker = None

        if not self.stock_list or len(self.stock_list) < 2:
            # No navigation possible if list is empty or has only one item
            super().keyPressEvent(event) # Pass event to base class
            return

        try:
            current_index = self.stock_list.index(self.ticker)
        except ValueError:
            # Current ticker not found in list, maybe do nothing or reset?
            print(f"Warning: Ticker {self.ticker} not found in navigation list.")
            super().keyPressEvent(event)
            return

        list_len = len(self.stock_list)

        if current_key == Qt.Key.Key_Left:
            new_index = (current_index - 1 + list_len) % list_len # Wrap around backward
            new_ticker = self.stock_list[new_index]
            navigate = True

        elif current_key == Qt.Key.Key_Right:
            new_index = (current_index + 1) % list_len # Wrap around forward
            new_ticker = self.stock_list[new_index]
            navigate = True

        if navigate and new_ticker:
            print(f"Navigating to: {new_ticker}") # Debug print
            self.ticker = new_ticker # Update the current ticker
            self.setWindowTitle(f"Stock Details - {self.ticker}") # Update window title
            self.load_chart_data() # Reload data for the new ticker
            self.ui.label.setText(self.ticker)
            event.accept() # Indicate that we handled the event
        else:
            # If not Left/Right arrow, let the base class handle it (e.g., for Escape key)
            super().keyPressEvent(event)