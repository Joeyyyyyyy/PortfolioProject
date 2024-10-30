import pandas as pd
import yfinance as yf

class StockPortfolio:
    def __init__(self, file_path: str, sheet_name: str = 'Sheet1'):
        """
        Initialize the StockPortfolio class with the path to the Excel file.
        
        :param file_path: Path to the Excel file containing transaction data.
        :param sheet_name: Name of the sheet to load from the Excel file.
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.df = None
        self.net_holdings = None
        self.buying_costs = None
        self.net_holdings_buying_price = None
        self.overall_profit_loss = None
        self.held_stocks = None

    def load_data(self):
        """Load the transaction data from the Excel file."""
        print("Loading Portfolio data....")
        self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, engine='openpyxl')
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df['Net Shares'] = self.df.apply(
            lambda row: row['Count'] if row['Transaction'] == 'Buy' else -row['Count'], axis=1
        )
        self.net_holdings = self.df.groupby(['Share', 'Symbol'])['Net Shares'].sum().reset_index()

    def calculate_total_buying_price(self):
        """
        Calculate the total buying price for shares currently held.
        
        :return: Total buying price and a dictionary with stock symbols as keys and their total buying price as values.
        """
        data = self.df
        data['Net Count'] = data.apply(lambda row: row['Count'] if row['Transaction'] == 'Buy' else -row['Count'], axis=1)
        net_holdings = data.groupby('Symbol')['Net Count'].sum()
        current_holdings = net_holdings[net_holdings > 0]

        buys = data[data['Transaction'] == 'Buy']
        buys_for_current_holdings = buys[buys['Symbol'].isin(current_holdings.index)]

        buying_costs = {}
        total_cost = 0
        for symbol in current_holdings.index:
            symbol_buys = buys_for_current_holdings[buys_for_current_holdings['Symbol'] == symbol].copy()
            symbol_buys.sort_values(by='Date', inplace=True)

            total_shares_needed = current_holdings[symbol]
            symbol_total_cost = 0
            for _, row in symbol_buys.iterrows():
                if total_shares_needed <= 0:
                    break
                shares_to_consider = min(row['Count'], total_shares_needed)
                symbol_total_cost += shares_to_consider * row['Price']
                total_shares_needed -= shares_to_consider

            buying_costs[symbol] = symbol_total_cost
            total_cost += symbol_total_cost

        self.buying_costs = buying_costs
        self.net_holdings_buying_price = total_cost

    def calculate_overall_profit_loss(self):
        """Calculate the realized profit/loss including currently held shares."""
        total_buy_cost = self.df[self.df['Transaction'] == 'Buy']['Total Amount'].sum()
        total_sell_revenue = self.df[self.df['Transaction'] == 'Sell']['Total Amount'].sum()
        self.overall_profit_loss = total_sell_revenue - total_buy_cost + self.net_holdings_buying_price

    def retrieve_current_prices(self):
        """Retrieve the current prices for held stocks using yfinance."""
        print("Retrieving current stock prices....")

        def get_current_price(ticker):
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period='1d')['Close'].iloc[-1]
                return current_price
            except Exception:
                return None

        self.held_stocks = self.net_holdings[self.net_holdings['Net Shares'] > 0].copy()
        self.held_stocks['Current Price'] = self.held_stocks['Symbol'].apply(get_current_price)

    def calculate_potential_sale_values(self):
        """Calculate potential sale values and profit/loss for held stocks."""
        self.held_stocks['Potential Sale Value'] = (
            self.held_stocks['Net Shares'] * self.held_stocks['Current Price']
        )
        self.held_stocks['Potential Sale Profit/Loss'] = self.held_stocks.apply(
            lambda row: row['Potential Sale Value'] - self.buying_costs.get(row['Symbol'], 0),
            axis=1
        )
        self.held_stocks['Current Price'] = self.held_stocks['Current Price'].round(2)
        self.held_stocks['Potential Sale Value'] = self.held_stocks['Potential Sale Value'].round(2)
        self.held_stocks['Potential Sale Profit/Loss'] = self.held_stocks['Potential Sale Profit/Loss'].round(2)
        self.held_stocks.dropna(axis=0,inplace=True)

    def display_results(self):
        """Display the overall profit/loss and held stocks with potential sale values."""
        print(f"\nRealised Profit: {self.overall_profit_loss:.2f}\n")
        print("Held stocks with potential sale values and profit/loss:\n")
        print(
            self.held_stocks[
                ['Share', 'Symbol', 'Net Shares', 'Current Price', 'Potential Sale Value', 'Potential Sale Profit/Loss']
            ].to_string(index=False)
        )
        
    def getHeldStocks(self):
        return self.held_stocks
    
    def getRealisedProfit(self):
        return self.overall_profit_loss

    def driver(self):
        """
        Run the complete workflow of loading data, calculating buying price,
        computing profit/loss, retrieving current stock prices, and displaying results.
        """
        self.load_data()
        self.calculate_total_buying_price()
        self.calculate_overall_profit_loss()
        self.retrieve_current_prices()
        self.calculate_potential_sale_values()
        self.display_results()
        
    def run(self):
        """
        Run the complete workflow of loading data, calculating buying price,
        computing profit/loss, retrieving current stock prices.
        """
        self.load_data()
        self.calculate_total_buying_price()
        self.calculate_overall_profit_loss()
        self.retrieve_current_prices()
        self.calculate_potential_sale_values()

# Example usage:
if __name__ == "__main__":
    file_path = 'TransactionDeets.xlsx'
    portfolio = StockPortfolio(file_path)
    portfolio.driver()