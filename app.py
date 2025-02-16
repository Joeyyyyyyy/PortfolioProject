from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, g
from StockPortfolio import StockPortfolio,MarketStatus
import os
from typing import Optional
from admin import StockTransactionManager
from datetime import datetime,timezone
from google import genai
from random_term import stock_terms
import random

class StockPortfolioAPI:
    def __init__(self) -> None:
        """
        Initialize the StockPortfolioAPI instance.

        Args:
            file_path (str): The path to the file containing stock portfolio data.
        """
        self.app: Flask = Flask(__name__)
        self.app.secret_key = "secret_key"  # Required for session management
        self.api_key: str = "joel09-02-2024Adh"  # Hardcoded API key
        self.setup_routes()  # Initialize all routes
        load_dotenv()
        self.genai_key = os.getenv("GENAI_API")

    def setup_routes(self) -> None:
        """
        Set up the routes for the Flask app.
        """
        @self.app.route("/")
        def index() -> str:
            """
            Render the home page.

            Returns:
                str: HTML content for the home page.
            """     
            if "password" not in session:
                session.pop('user',None)
                           
            return render_template("index.html")

        @self.app.route("/stockDisplay")
        def stock_display() -> str:
            """
            Render the stock display page.

            Returns:
                str: HTML content for the stock display page.
            """
            if "user" in session:
                if "password" not in session:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
                g.admindb=StockTransactionManager()
                login=g.admindb.login(username=session["user"],password=session["password"])
                if login == False:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
            else:
                return redirect(url_for("login"))
                
            return render_template("stockDisplay.html")

        @self.app.route("/login", methods=["GET", "POST"])
        def login() -> str:
            """
            Handle login form submission and render login page.
            """
            login_failed = request.args.get("login_failed", default=False, type=lambda v: v.lower() == "true")  # Initialize the flag
            
            if request.method == "POST":
                username = request.form.get("username").strip()
                password = request.form.get("password")
                
                g.admindb=StockTransactionManager()
                login=g.admindb.login(username=username,password=password)

                if login == True:  
                    print(username+" has logged in.")
                    
                    session["user"] = username
                    session["password"] = password
                    
                    return redirect(url_for("stock_display"))
                else:
                    session.pop("user", None)
                    g.admindb.logout()
                    flash("Invalid username or password")
                    login_failed = True  
                    return redirect(url_for("login", login_failed=True))

            return render_template("login.html", login_failed=login_failed)
        
        @self.app.route("/signup", methods=["GET", "POST"])
        def signup():
            """
            Render the signup page and handle account creation.
            """
            if request.method == "POST":
                # Get form data
                username = request.form.get("username").strip()
                email = request.form.get("email").strip()
                password = request.form.get("password")
                confirm_password = request.form.get("confirm_password")

                # Validate input
                if not username or not email or not password or not confirm_password:
                    flash("All fields are required.", "error")
                    return render_template("signup.html")

                if password != confirm_password:
                    flash("Passwords do not match.", "error")
                    return render_template("signup.html")

                # Interact with StockTransactionManager to create an account
                try:
                    g.admindb=StockTransactionManager()
                    success = g.admindb.create_account(username=username, password=password, email=email)
                    if success:
                        flash("Account created successfully! Please log in.", "success")
                        return redirect(url_for("login"))
                    else:
                        flash("Username already exists. Please try a different username.", "error")
                except Exception as e:
                    flash(f"An error occurred: {str(e)}", "error")

            return render_template("signup.html")
        
        @self.app.route("/transaction", methods=["GET", "POST"])
        def transaction_form():
            """
            Handle displaying and submitting the stock transaction form.

            Returns:
                str: Rendered HTML page for GET requests, or redirects after POST.
            """
            if "user" in session:
                if "password" not in session:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
                g.admindb=StockTransactionManager()
                login=g.admindb.login(username=session["user"],password=session["password"])
                if login == False:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
            else:
                return redirect(url_for("login"))

            if request.method == "POST":
                pass
            return render_template("transaction.html")

        @self.app.route("/logout")
        def logout() -> str:
            """
            Clear the session and log the user out.
            """
            session.pop("user", None)
            flash("You have been logged out.")
            return redirect(url_for("home"))

        @self.app.route("/api/transactionLogs", methods=["GET"])
        def get_transaction_logs() -> tuple:
            """
            Get the list of transactions by the user.

            Returns:
                tuple: JSON response with transaction logs or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
            g.admindb=StockTransactionManager()
            g.admindb.login(username=session["user"],password=session["password"])
            transactions = g.admindb.transactions_to_dataframe()
            if transactions is not None:
                return jsonify(transactions.to_dict(orient="records"))
            return jsonify({"error": "No transaction data available"})
        
        @self.app.route("/api/market_status",methods=["GET"])
        def get_market_status() -> tuple:
            """
            Returns the market status
            
            Returns:
                bool: True if market is open and False if market is closed.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}),403
            g.status=MarketStatus()
            g.marketopen=g.status.is_market_open()
            return jsonify({"market_status":g.marketopen})
        
        @self.app.route("/api/portfolio_data", methods=["GET"])
        def get_portfolio_data() -> tuple:
            """
            Get all portfolio data in a single response.

            Returns:
                tuple: JSON response with all portfolio data or an error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403

            try:
                # Initialize and prepare portfolio
                g.admindb = StockTransactionManager()
                g.admindb.login(username=session["user"], password=session["password"])
                g.df = g.admindb.transactions_to_dataframe()
                
                if g.df is None:
                    portfolio_data={
                        "realized_profit": 0,
                        "unrealized_profit": 0,
                        "todays_returns": 0,
                        "held_stocks": [],
                        "sold_stocks": []
                    }
                    return jsonify(portfolio_data)
                
                g.portfolio = StockPortfolio(user=session["user"], dataframe=g.df)
                g.portfolio.run()

                # Collect all data
                portfolio_data = {
                    "realized_profit": g.portfolio.getRealisedProfit(),
                    "unrealized_profit": g.portfolio.getUnrealisedProfit(),
                    "todays_returns": g.portfolio.getOneDayReturns(),
                    "held_stocks": g.portfolio.getHeldStocks().to_dict(orient="records") if g.portfolio.getHeldStocks() is not None else [],
                    "sold_stocks": g.portfolio.getSoldStocksData().to_dict(orient="records") if g.portfolio.getSoldStocksData() is not None else []
                }

                return jsonify(portfolio_data)

            except Exception as e:
                # Handle errors gracefully
                return jsonify({"error": str(e)}), 500
        
        @self.app.route("/api/submit_transactions", methods=["POST"])
        def submit_transactions():
            """
            Endpoint to handle submitted transaction data.
            """
            if not api.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403

            # Get JSON data from the POST request
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid data"}), 400

            try:
                
                def formatter(data):
                    converted_data = []
                    for entry in data:
                        # Convert date string to DatetimeWithNanoseconds format
                        date_object = datetime.strptime(entry['Date'], '%d-%m-%Y').replace(tzinfo=timezone.utc)
                        converted_entry = {
                            'Sl_No': entry['Sl.No.'],  # Rename to camelCase
                            'Date': date_object,  # Convert to datetime object
                            'Share': entry['Share'],
                            'Symbol': entry['Symbol'],
                            'Transaction': entry['Transaction'].lower(),  # Convert to lowercase
                            'Count': entry['Count'],
                            'Price': float(entry['Price']),  # Ensure float type for price
                            'Total_Amount': float(entry['Total Amount'])  # Rename to camelCase
                        }
                        converted_data.append(converted_entry)
                    return converted_data
                g.admindb=StockTransactionManager()
                g.admindb.login(username=session["user"],password=session["password"])
                update= g.admindb.replace_transaction_history(formatter(data))
                
                if update:
                    return jsonify({"message": "Transactions updated successfully"}), 200
                else:
                    return jsonify({"error": "Failed to update transactions"}), 500
            except Exception as e:
                
                return jsonify({"error": f"An error occurred: {str(e)}"}), 500

        @self.app.route("/api/advise", methods=["GET"])
        def get_advise():
            
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403

            try:
                # Initialize and prepare portfolio
                g.admindb = StockTransactionManager()
                g.admindb.login(username=session["user"], password=session["password"])
                g.df = g.admindb.transactions_to_dataframe()
                g.portfolio = StockPortfolio(user=session["user"], dataframe=g.df)
                g.portfolio.run()                
                random_term = random.choice(stock_terms)
                g.status=MarketStatus()
                my_data = {
                        "realized_profit": g.portfolio.getRealisedProfit(),
                        "unrealized_profit": g.portfolio.getUnrealisedProfit(),
                        "todays_returns": g.portfolio.getOneDayReturns(),
                        "held_stocks": g.portfolio.getHeldStocks().to_dict(orient="records") if g.portfolio.getHeldStocks() is not None else [],
                        "indices": g.status.market_movement_summary()
                    }
                transactionstring = g.df.to_string()
                prompt="""System Prompt: You are Toro, a bull living on the Dalal Street, a stock market genius AI that has immense knowledge in this field.
                    You speak in a high-energy, bullish, money-hungry and confident tone—like Jordan Belfort, but family-friendly.\n\n
                    Introduce yourself first. Then give a short disclaimer that you're not a SEBI registered advisor and you're just Toro who can make mistakes and your advise is just for educational and informative purposes.
                    Don't forget that the market usually opens at 9:30 AM and closes at 3:30 PM on weekdays. If the time is not during market hours then you have to tailor your response accordingly.
                    \n\nNow, I want you to be very elaborate for your answers to these questions and use a little relevant emojis. Add extra gaps between paragraphs too:-
                    \n* Daily Performance Review: Identify today’s biggest loser and biggest winner. Explain possible reasons for their movements. Don't forget to take into account the index movements for analysing this. 
                    \n* What is my favourite stock: Assess what is my favourite stock.
                    \n* Your opinion on NIFTY50 and SENSEX movements.
                    \n* Future Prospects: Suggest potential stocks or sectors I should keep a watch on.
                    \n* Expectations: What do you think i should expect right now from the market (Answer this question only if the time right now is between 9:30 AM and 3:30 PM, otherwise ignore)
                    """
                prompt += f"\n* Random Stock market term for today: Explain '{random_term}' concisely." +"""
                    My Data:\n\nMy transactions:\n"""
                if my_data is not None:
                    print("Generating AI advise")
                    prompt+= transactionstring+"""\n\n\n My currently held stocks: 
                    (Data in the order: Name, Net Shares, Avg Buying Price, Current Price, Potential Sale Value, Day Gain, Today's % Change, Unrealised P/L):\n"""
                    prompt += str(my_data["held_stocks"])+"\n\nRealised Profit: "+str(my_data["realized_profit"])+"\n\nUnrealised Profit: "+str(my_data["unrealized_profit"])+"\n\nToday's P&L: "+str(my_data["todays_returns"])+"\n\n"+str(my_data["indices"])
                    client = genai.Client(api_key = self.genai_key)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", contents=prompt
                    )
                    return jsonify({"AIresponse": response.text})
                return jsonify({"error": "No held stocks data available"}), 404
            
            except Exception as e:
                # Handle errors gracefully
                return jsonify({"error": str(e)}), 500


    def is_authorized(self, request) -> bool:
        """
        Check if the request contains the correct API key.

        Args:
            request : The Flask request object.

        Returns:
            bool: True if authorized, False otherwise.
        """
        api_key: Optional[str] = request.headers.get("x-api-key")
        return api_key == self.api_key

    def run(self, debug: bool = True, host: str = "127.0.0.1", port: int = 5000) -> None:
        """
        Run the Flask app.

        Args:
            debug (bool): Whether to run the app in debug mode.
            host (str): The hostname to listen on.
            port (int): The port of the web server.
        """
        self.app.run(debug=debug, host=host, port=port)


# To run the API
if __name__ == "__main__":
    api = StockPortfolioAPI()
    port: int = int(os.environ.get("PORT", 8000))
    api.run(debug=True, host="0.0.0.0", port=port)

# Expose the Flask app instance for Waitress
api = StockPortfolioAPI()
app = api.app