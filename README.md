# finance
a small and simple stock app

      
pip install -r requirements.txt

1. Purpose:
This program is a desktop application built using Python and the PyQt6 framework. Its primary purpose is to provide users with a visual interface to view summary and detailed historical data for a predefined list of stock tickers.
2. How it Works:
The application consists of two main components:
•	Main Window (StockApp):
o	Upon launching, this window fetches basic, current (or latest available) daily data (Open, High, Low, Close, Volume) for a hardcoded list of stock tickers (e.g., AAPL, MSFT, GOOGL, etc.) using the yfinance library.
o	It displays this summary data in a table (QTableWidget), allowing users to see the latest figures for multiple stocks at a glance. Close prices are color-coded (green for up, red for down compared to the open).
o	The table allows sorting by columns.
o	Users can interact with the table by double-clicking on a specific stock's row.
•	Detail Window (Stock_details):
o	Launched when a user double-clicks a stock in the main window's table.
o	It receives the specific ticker symbol selected and the complete list of tickers from the main window.
o	It displays the currently selected ticker symbol prominently (in a dedicated QLabel).
o	It fetches more extensive historical data (6 months of daily data) for the selected ticker using yfinance.
o	It calculates technical indicators: 20-day and 50-day Moving Averages (MA20, MA50) using pandas, and the Relative Strength Index (RSI 14) using the talib library.
o	It uses Matplotlib, embedded within the PyQt6 window using FigureCanvasQTAgg, to display three vertically stacked charts:
	Top: Candlestick chart showing daily Open, High, Low, Close prices, overlaid with the MA20 and MA50 lines. The legend displays "MA20", "MA50", and the Ticker symbol separately.
	Middle: Volume chart, with bars colored green/red based on whether the closing price was higher/lower than the opening price for that day.
	Bottom: RSI(14) chart, showing the RSI line with horizontal lines indicating the 70 (overbought) and 30 (oversold) levels.
o	All three charts share the same x-axis (Date), allowing for synchronized panning and zooming using the standard Matplotlib Navigation Toolbar, which is included above the charts.
o	It provides interactive hover functionality: moving the mouse over the price chart displays a tooltip showing the specific Date, OHLC values, Volume, and RSI for that point.
o	It supports keyboard navigation: pressing the Left or Right arrow keys allows the user to cycle through the previous or next stock in the list passed from the main window, automatically updating the label and reloading all chart data for the new ticker.
3. Key Technologies:
•	GUI: PyQt6
•	Data Fetching: yfinance
•	Charting: Matplotlib (embedded in PyQt6)
•	Data Manipulation: pandas, numpy
•	Technical Indicators: talib, pandas
