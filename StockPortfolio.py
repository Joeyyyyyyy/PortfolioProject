import pandas as pd
import yfinance as yf

class StockPortfolio:
    def __init__(self, file_path: str = None , sheet_name: str = 'Sheet1', dataframe: pd.DataFrame = None):
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

    def load_excel(self):
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
    
    def load_dataframe(self):
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

    def retrieve_current_prices(self, mode:str = 'held_stocks'):
        """Retrieve the current prices for held stocks using yfinance."""
        print("Retrieving current stock prices....")
        if(mode == 'held_stocks'):
            def get_current_price(ticker):
                try:
                    stock = yf.Ticker(ticker)
                    current_price = stock.history(period='1d')['Close'].iloc[-1]
                    return current_price
                except Exception:
                    return None
            self.net_holdings = self.net_holdings.reset_index(drop=True) #resetting the index
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
            prior_buys = self.buys[self.buys['Sl.No.'] < slno].sort_values(by='Date')
            prior_buys = prior_buys[prior_buys['Symbol']==row[4]]
            
            for idx, buy_row in prior_buys.iterrows():
                buy_count = buy_row['Count']
                buy_price = buy_row['Price']
                buy_total_amount = buy_row['Total Amount']
                
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
        
        self.realised_df=realised_df


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

    def getSoldStocksData(self):
        return self.realised_df

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
        
        return True

# Example usage:
if __name__ == "__main__":
    file_path = 'DummyTransactions.xlsx'
    portfolio = StockPortfolio(file_path)
    portfolio.driver()