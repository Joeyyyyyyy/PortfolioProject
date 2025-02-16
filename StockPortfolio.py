from datetime import datetime,timezone
from typing import Optional
import pandas as pd
import yfinance as yf

class StockPortfolio:
    def __init__(self, user: str, file_path: str = None , sheet_name: str = 'Sheet1', dataframe: pd.DataFrame = None):
        """
        Initialize the StockPortfolio class with the path to the Excel file.
        
        :param file_path: Path to the Excel file containing transaction data.
        :param sheet_name: Name of the sheet to load from the Excel file.
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.df = dataframe
        self.net_holdings = None
        self.buying_costs = None
        self.net_holdings_buying_price = None
        self.overall_profit_loss = None
        self.held_stocks = None
        self.sold_stocks = None
        self.buys = None
        self.realised_df=None
        self.potential_profit=None
        self.held_stocks_updated=0
        self.user=user

    def load_excel(self) -> pd.DataFrame:
        """Load the transaction data from the Excel file."""
        
        if(self.file_path==None):
            return None
        
        print("Loading Portfolio data....")
        self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, engine='openpyxl')
        
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df['Net Shares'] = self.df.apply(
            lambda row: row['Count'] if row['Transaction'] == 'Buy' else -row['Count'], axis=1
        )
        net_holdings = self.df.groupby(['Share', 'Symbol'])['Net Shares'].sum().reset_index()
        
        return net_holdings
    
    def load_dataframe(self) -> pd.DataFrame:
        """Load the transaction data from the Database."""
        
        if self.df is None:
            return None
        
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df['Net Shares'] = self.df.apply(
            lambda row: row['Count'] if row['Transaction'] == 'Buy' else -row['Count'], axis=1
        )
        net_holdings = self.df.groupby(['Share', 'Symbol'])['Net Shares'].sum().reset_index()
        
        return net_holdings

    def calculate_total_buying_price(self):
        """
        Calculate the total buying price for shares currently held, ensuring that sold shares
        are properly accounted for and partial transactions are handled.
        
        :return: None. Updates the instance attributes for buying costs and total buying price.
        """
        data = self.df.copy()

        # Add a "Net Count" column to track the impact of each transaction
        data['Net Count'] = data.apply(lambda row: row['Count'] if row['Transaction'] == 'Buy' else -row['Count'], axis=1)
        
        # Save sold stocks for later use
        self.sold_stocks = data[data['Net Count'] < 0].reset_index(drop=True)
        
        # Calculate net holdings per stock
        net_holdings = data.groupby('Symbol')['Net Count'].sum()
        current_holdings = net_holdings[net_holdings > 0]  # Filter for stocks currently held
        
        # Filter buy transactions only
        self.buys = data[data['Transaction'] == 'Buy'].copy()
        self.buys = self.buys.reset_index(drop=True)  # Reset index for safe iteration
        
        # Create a copy of the buys to track remaining shares after sales
        remaining_buys = self.buys.copy()

        # Deduct sold shares from relevant buy transactions
        for _, sell_row in self.sold_stocks.iterrows():
            sell_count = sell_row['Count']
            sell_symbol = sell_row['Symbol']
            
            # Filter buy transactions for the sold stock, ensuring FIFO order
            relevant_buys = remaining_buys[(remaining_buys['Symbol'] == sell_symbol) & (remaining_buys['Count'] > 0)]
            relevant_buys = relevant_buys.sort_values(by='Date')

            for idx, buy_row in relevant_buys.iterrows():
                if sell_count <= 0:
                    break
                # Deduct shares from the relevant buy transaction
                available_to_deduct = min(buy_row['Count'], sell_count)
                remaining_buys.at[idx, 'Count'] -= available_to_deduct
                sell_count -= available_to_deduct

        # Calculate the cost of currently held shares using remaining buys
        buying_costs = {}
        total_cost = 0

        for symbol in current_holdings.index:
            # Filter remaining buys for this stock
            symbol_buys = remaining_buys[(remaining_buys['Symbol'] == symbol) & (remaining_buys['Count'] > 0)].copy()
            symbol_buys.sort_values(by='Date', inplace=True)

            total_shares_needed = current_holdings[symbol]
            symbol_total_cost = 0

            for _, row in symbol_buys.iterrows():
                if total_shares_needed <= 0:
                    break

                shares_to_consider = min(row['Count'], total_shares_needed)
                symbol_total_cost += shares_to_consider * row['Price']
                total_shares_needed -= shares_to_consider

            # Log a warning if insufficient buys are available
            if total_shares_needed > 0:
                print(f"Warning: Not enough buy transactions to account for {total_shares_needed} shares of {symbol}.")

            buying_costs[symbol] = symbol_total_cost
            total_cost += symbol_total_cost

        # Store results in instance attributes
        self.buying_costs = buying_costs
        self.net_holdings_buying_price = total_cost

    def calculate_overall_profit_loss(self):
        """Calculate the realized profit/loss including currently held shares."""
        total_buy_cost = self.df[self.df['Transaction'] == 'Buy']['Total Amount'].sum()
        total_sell_revenue = self.df[self.df['Transaction'] == 'Sell']['Total Amount'].sum()
        self.overall_profit_loss = total_sell_revenue - total_buy_cost + self.net_holdings_buying_price

    def retrieve_current_prices(self, mode: str = 'held_stocks'):
        """Retrieve the current prices for held stocks using yfinance."""

        def get_current_price(ticker):
            try:
                stock = yf.Ticker(ticker)
                current_price = stock.history(period='1d')['Close'].iloc[-1]
                return current_price
            except Exception:
                return None

        def get_yesterday_close(ticker):
            try:
                stock = yf.Ticker(ticker)
                # Use '5d' period to get enough data for filtering
                history = stock.history(period='5d')
                if len(history) > 1:
                    yesterday_close = history['Close'].iloc[-2]  # Second last row is previous close
                else:
                    yesterday_close = None
                return yesterday_close
            except Exception:
                return None

        self.net_holdings = self.net_holdings.reset_index(drop=True)  # Resetting the index

        if mode == 'held_stocks':
            print("Retrieving current stock prices....")
            self.held_stocks_updated+=1
            self.held_stocks = self.net_holdings[self.net_holdings['Net Shares'] > 0].copy()
            self.held_stocks['Current Price'] = self.held_stocks['Symbol'].apply(get_current_price)

        elif mode == 'price_change':
            print("Retrieving previous day stock prices....")
            if self.held_stocks_updated == 0:
                self.held_stocks = self.net_holdings[self.net_holdings['Net Shares'] > 0].copy()
            self.held_stocks_updated+=1
            self.held_stocks['Current Price'] = self.held_stocks['Symbol'].apply(get_current_price)
            self.held_stocks['Previous Closing'] = self.held_stocks['Symbol'].apply(get_yesterday_close)
            self.held_stocks['Price Change'] = self.held_stocks['Net Shares']*(self.held_stocks['Current Price'] - self.held_stocks['Previous Closing'])
            self.held_stocks['Percentage Change'] = 100*self.held_stocks['Price Change']/(self.held_stocks['Net Shares']*self.held_stocks['Previous Closing'])
            self.held_stocks['Percentage Change']=self.held_stocks['Percentage Change'].round(2)

    def calculate_potential_sale_values(self):
        """Calculate potential sale values, profit/loss for held stocks and avg buying price."""
        self.held_stocks['Potential Sale Value'] = (
            self.held_stocks['Net Shares'] * self.held_stocks['Current Price']
        )
        self.held_stocks['Potential Sale Profit/Loss'] = self.held_stocks.apply(
            lambda row: row['Potential Sale Value'] - self.buying_costs.get(row['Symbol'], 0),
            axis=1
        )
        self.held_stocks['Avg Buying Price'] = self.held_stocks.apply(
            lambda row: self.buying_costs.get(row['Symbol'], 0)/row['Net Shares'],
            axis=1
        ).round(2)
        self.held_stocks['Current Price'] = self.held_stocks['Current Price'].round(2)
        self.held_stocks['Potential Sale Value'] = self.held_stocks['Potential Sale Value'].round(2)
        self.held_stocks['Potential Sale Profit/Loss'] = self.held_stocks['Potential Sale Profit/Loss'].round(2)
        self.held_stocks.dropna(axis=0,inplace=True)
        
        self.potential_profit=self.held_stocks['Potential Sale Profit/Loss'].sum()

    def compute_realised_returns_dataframe(self):
        """
        This function computes data about shares that have already been sold and returns a DataFrame,
        consisting of the average price at which it was bought, profit/loss made in each transaction,
        and the price at which it was sold.
        """
        print("Computing realised returns data....")
        sell = self.sold_stocks
        realised_data = []  # List to store results for each sell transaction
        
        for row in sell.itertuples(index=True):
            slno = row[1]
            sell_date = row.Date
            sell_count = row.Count
            sell_price = row.Price
            # Access Total Sell Amount properly
            sell_total_amount = row._asdict().get("Total Sell Amount", row._asdict().get("Total Amount", None))
            if sell_total_amount is None:
                sell_total_amount = sell_price * sell_count  # Calculate if not present in the row data
            remaining_sell_count = sell_count
            total_buy_amount = 0
            total_bought_count = 0
            profit = 0
            
            # Filter buys that occurred before the sell transaction and sort by date for FIFO
            prior_buys = self.buys[self.buys['Date'] <= sell_date].sort_values(by='Date')
            prior_buys = prior_buys[prior_buys['Symbol']==row[4]]
            
            for idx, buy_row in prior_buys.iterrows():
                buy_count = buy_row['Count']
                buy_price = buy_row['Price']
                
                if buy_count == 0:
                    continue  # Skip fully depleted buys
                
                # Determine how many shares we can "sell" from this buy transaction
                if remaining_sell_count <= buy_count:
                    # Fulfill the sell with the remaining buy_count in this row
                    used_buy_count = remaining_sell_count
                    profit += used_buy_count * (sell_price - buy_price)
                    total_buy_amount += used_buy_count * buy_price
                    total_bought_count += used_buy_count
                    prior_buys.at[idx, 'Count'] -= used_buy_count  # Reduce the buy count in the buys DataFrame
                    remaining_sell_count = 0
                    break  # Fully matched the sell order
                else:
                    # Use up all shares in this buy transaction
                    used_buy_count = buy_count
                    profit += used_buy_count * (sell_price - buy_price)
                    total_buy_amount += used_buy_count * buy_price
                    total_bought_count += used_buy_count
                    prior_buys.at[idx, 'Count'] = 0  # Mark this buy as fully depleted
                    remaining_sell_count -= used_buy_count
            
            # Calculate average buy price based on the matched buy transactions
            avg_buy_price = total_buy_amount / total_bought_count if total_bought_count > 0 else 0
            realised_data.append({
                'Sell Sl.No.': slno,
                'Sell Date': row.Date,
                'Symbol': row.Symbol,
                'Sell Count': sell_count,
                'Sell Price': sell_price,
                'Total Sell Amount': sell_total_amount,
                'Avg Buy Price': avg_buy_price,
                'Total Buy Amount': total_buy_amount,
                'Realized Profit/Loss': profit
            })
            
            # Debugging output
            #print(f"Sell transaction {slno}:")
            #print(f"Sell Count: {sell_count}, Sell Price: {sell_price}, Total Sell Amount: {sell_total_amount}")
            #print(f"Avg Buy Price: {avg_buy_price}, Total Buy Amount: {total_buy_amount}, Realized Profit/Loss: {profit}")
            #print("")

        # Convert realised_data list to a DataFrame
        realised_df = pd.DataFrame(realised_data)
        
        if realised_df.empty== True:
            columns = [
            'Transaction ID',
            'Sell Date',
            'Stock Code',
            'Shares Sold',
            'Sell Price (per share)',
            'Total Sell Value',
            'Avg Buy Price',
            'Total Buy Value',
            'Profit/Loss'
            ]

            realised_df = pd.DataFrame(columns=columns)
        
        # Rename columns for user-friendly presentation
        realised_df = realised_df.rename(columns={
            'Sell Sl.No.': 'Transaction ID',
            'Symbol': 'Stock Code',
            'Sell Count': 'Shares Sold',
            'Sell Price': 'Sell Price (per share)',
            'Total Sell Amount': 'Total Sell Value',
            'Total Buy Amount': 'Total Buy Value',
            'Realized Profit/Loss': 'Profit/Loss'
        })

        # Format monetary columns to 2 decimal places with commas for readability and real numbers like indices to int
        realised_df['Sell Price (per share)'] = realised_df['Sell Price (per share)']
        realised_df['Total Sell Value'] = realised_df['Total Sell Value']
        realised_df['Avg Buy Price'] = realised_df['Avg Buy Price']
        realised_df['Total Buy Value'] = realised_df['Total Buy Value']
        realised_df['Profit/Loss'] = realised_df['Profit/Loss']
        realised_df['Transaction ID'] = realised_df['Transaction ID'].round().astype(int)
        realised_df['Shares Sold'] = realised_df['Shares Sold'].round().astype(int)


        # Reorder columns for better readability
        realised_df = realised_df[['Transaction ID', 'Sell Date', 'Stock Code', 'Shares Sold', 
                                'Sell Price (per share)', 'Total Sell Value', 
                                'Avg Buy Price', 'Total Buy Value', 'Profit/Loss']]
        
        self.realised_df=realised_df.sort_values(by='Sell Date')


    def display_results(self): 
        """Display the overall profit/loss and held stocks with potential sale values."""
        print(f"\nRealised Profit: {self.overall_profit_loss:.2f}\n")
        print("Held stocks with potential sale values and profit/loss:\n")
        print(
            self.held_stocks[
                ['Share', 'Symbol', 'Net Shares', 'Avg Buying Price', 'Current Price', 'Potential Sale Value', 'Potential Sale Profit/Loss', 
                 'Previous Closing', 'Price Change','Percentage Change']
            ].to_string(index=False)
        )
        
    def getHeldStocks(self) -> Optional[pd.DataFrame]:
        """ Returns data of current holdings and has these columns: 'Share', 'Symbol', 'Net Shares', 'Current Price',
       'Potential Sale Value', 'Potential Sale Profit/Loss',
       'Avg Buying Price', 'Previous Closing', 'Price Change',
       'Percentage Change'"""
        df=self.held_stocks.copy()
        df['Percentage Change'] = df['Percentage Change'].round(2).apply(lambda x: f"+{x}" if x > 0 else str(x))
        df['Potential Sale Profit/Loss'] = df['Potential Sale Profit/Loss'].round(2).apply(lambda x: f"+{x}" if x > 0 else str(x))
        df['Price Change'] = df['Price Change'].round(2).apply(lambda x: f"+{x}" if x > 0 else str(x))
        return df
    
    def getRealisedProfit(self):
        if self.realised_df is None:
            return 0
        return self.overall_profit_loss

    def getSoldStocksData(self) -> Optional[pd.DataFrame]:
        """ Returns data of previously sold stocks and has these columns:'Transaction ID', 'Sell Date', 'Stock Code', 
                                'Shares Sold', 'Sell Price (per share)', 'Total Sell Value', 
                                'Avg Buy Price', 'Total Buy Value', 'Profit/Loss'"""
        df=self.realised_df.copy()
        df['Profit/Loss'] = df['Profit/Loss'].round(2).apply(lambda x: f"+{x}" if x > 0 else str(x))
        return df
    
    def getUnrealisedProfit(self):
        if self.held_stocks is None:
            return 0
        return self.potential_profit
    
    def getOneDayReturns(self):
        if self.held_stocks is None:
            return 0
        one_day_returns=self.held_stocks["Price Change"].sum()
        return one_day_returns

    def driver(self):
        """
        Run the complete workflow of loading data, calculating buying price,
        computing profit/loss, retrieving current stock prices, and displaying results.
        """
        if self.file_path!=None:
            self.net_holdings = self.load_excel()
        elif self.df is not None and not self.df.empty:
            self.net_holdings = self.load_dataframe()
        else:
            return False
        
        if self.df is not None:    
            self.calculate_total_buying_price()
            self.calculate_overall_profit_loss()
            self.retrieve_current_prices()
            self.calculate_potential_sale_values()
            self.compute_realised_returns_dataframe()
            self.retrieve_current_prices(mode="price_change")
            self.display_results()
        
        return True
        
    def run(self):
        """
        Run the complete workflow of loading data, calculating buying price,
        computing profit/loss, retrieving current stock prices.
        """
        if self.file_path!=None:
            self.net_holdings = self.load_excel()
        elif self.df is not None and not self.df.empty:
            self.net_holdings = self.load_dataframe()
        else:
            return False
            
        if self.df is not None:    
            self.calculate_total_buying_price()
            self.calculate_overall_profit_loss()
            self.retrieve_current_prices()
            self.calculate_potential_sale_values()
            self.compute_realised_returns_dataframe()
            self.retrieve_current_prices(mode="price_change")
        
        return True
    
class MarketStatus:
    def __init__(self):
        pass
    
    def is_market_open(self):
        try:
            stock = yf.Ticker("^NSEI")
            hist = stock.history(period="1d", interval="1m")
            
            if not hist.empty:
                # Get the most recent data point
                last_trade_time = hist.index[-1].to_pydatetime()
                current_time = datetime.now(timezone.utc)
                # If the last trade was recent (within a few minutes), the market is likely open
                if (current_time - last_trade_time).seconds < 5*60:
                    return True
        except:
            return False
        return False
    
    def market_movement_summary(self)->str:
        # Fetching NIFTY50 and SENSEX data
        nifty = yf.Ticker('^NSEI')
        sensex = yf.Ticker('^BSESN')

        nifty_today = nifty.history(period='5d')
        sensex_today = sensex.history(period='5d')

        if nifty_today.empty or sensex_today.empty:
            return "Market data not available for today."

        # Calculating the point changes
        nifty_change = nifty_today['Close'].iloc[-1] - nifty_today['Close'].iloc[-2]
        sensex_change = sensex_today['Close'].iloc[-1] - sensex_today['Close'].iloc[-2]


        # Determining up/down movement
        nifty_status = 'up' if nifty_change > 0 else 'down'
        sensex_status = 'up' if sensex_change > 0 else 'down'

        # Formatting date and getting day name
        today = datetime.now()
        today_date = today.strftime('%d/%m/%Y, %I:%M:%S %p')
        day_name = today.strftime('%A')  # Gets full day name (e.g., Monday)

        # Checking if market is open
        open = self.is_market_open()
        open_or_close = "open." if open else "closed."

        # Generating the result string with day name
        result = (f"As of latest data, SENSEX is {sensex_status} by {abs(sensex_change):.2f} points while NIFTY50 is {nifty_status} "
                f"by {abs(nifty_change):.2f} points today. Today's date and time: {today_date} ({day_name}). "
                f"Market is {open_or_close}")

        return result

# Example usage:
if __name__ == "__main__":
    file_path = 'DummyTransactions.xlsx'
    status=MarketStatus()
    print(status.market_movement_summary())