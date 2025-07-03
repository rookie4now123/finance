from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from PyQt6.QtCore import Qt
import yfinance as yf
from PyQt6.QtGui import QColor
from homework_ui import Ui_Form
from stock_detail_window import Stock_details

class StockApp(QMainWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.Stock = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'PYPL', 'NFLX']
        self.stockTable.setSortingEnabled(True)
        self.load_stocks()
        self.stockTable.itemDoubleClicked.connect(self.on_stock_row_double_clicked)

    def on_stock_row_double_clicked(self, item):
        """Handle click events on stock table rows."""
        # Get the row that was clicked
        row = item.row()
        # Get the ticker from the first column of that row
        ticker_item = self.stockTable.item(row, 0)
        if ticker_item:
            ticker = ticker_item.text()
            # Launch the details dialog
            dlg = Stock_details(ticker, self.Stock, self)
            dlg.exec()

    def resizeEvent(self, event):
        self.stockTable.resize(self.width(), self.height())  # Fills entire window
        super().resizeEvent(event)


def load_stocks(self):
    if not self.Stock:
        print("Stock list is empty.")
        return

    try: # Use try-except for the whole download block
        data = yf.download(
            self.Stock,
            period="1d",
            interval="1d",
            group_by="ticker"
        )
        # --- NEW CODE: Check if the download returned an empty dataframe ---
        if data.empty:
            print("Download failed or returned no data. Check your connection or ticker symbols.")
            print("This may be due to a rate limit. Please wait a while before trying again.")
            return # Exit the function
        # --- END NEW CODE ---

    except Exception as e:
         print(f"Error downloading stock data: {e}")
         # Optionally display an error message to the user in the UI
         return # Exit the function if download fails, preventing the crash

    self.stockTable.setRowCount(0)
    self.stockTable.setColumnCount(6)  # Ticker + OHLC + Volume
    self.stockTable.setHorizontalHeaderLabels(
        ["Ticker", "Open", "High", "Low", "Close", "Volume"]
    )
    row = 0
    for ticker in self.Stock:
        # Check if the data for this specific ticker is valid and not empty
        if ticker in data and not data[ticker].dropna().empty:
            try:
                # Get latest data point
                latest = data[ticker].iloc[-1]

                # Add ticker
                self.stockTable.insertRow(row)
                self.stockTable.setItem(row, 0, QTableWidgetItem(ticker))

                # Add OHLCV data (formatted)
                self.stockTable.setItem(row, 1, QTableWidgetItem(f"${latest['Open']:.2f}"))
                self.stockTable.setItem(row, 2, QTableWidgetItem(f"${latest['High']:.2f}"))
                self.stockTable.setItem(row, 3, QTableWidgetItem(f"${latest['Low']:.2f}"))

                # Close price with color coding
                close_item = QTableWidgetItem(f"${latest['Close']:.2f}")
                if latest['Close'] >= latest['Open']:
                    close_item.setForeground(QColor(0, 255, 0))  # Green
                else:
                    close_item.setForeground(QColor(255, 0, 0))  # Red
                self.stockTable.setItem(row, 4, close_item)
                self.stockTable.setItem(row, 5, QTableWidgetItem(f"{latest['Volume']:,}"))

                row += 1

            except Exception as e:
                print(f"Could not process data for {ticker}: {e}")
                continue
        else:
            print(f"No valid data downloaded for {ticker}. Skipping.")
        

if __name__ == "__main__":
    app = QApplication([])
    win = StockApp()
    win.show()
    app.exec()