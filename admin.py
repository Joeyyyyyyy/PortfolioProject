import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from dotenv import load_dotenv
import os
import pandas as pd
from StockPortfolio import StockPortfolio

class StockTransactionManager:
    """A manager class for handling user accounts and stock transactions in Firebase Firestore."""

    def __init__(self, service_account_path):
        """
        Initialize StockTransactionManager with Firebase credentials.

        Args:
            service_account_path (str): Path to the Firebase service account JSON file.
        """
        self._initialize_firebase(service_account_path)
        self.db = firestore.client()
        self.current_user = None

    def _initialize_firebase(self, service_account_path):
        """Initialize the Firebase app with the provided service account credentials."""
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)

    def create_account(self, username, password):
        """
        Create a new user account.

        Args:
            username (str): Username for the new account.
            password (str): Password for the new account.
        """
        user_data = self._get_user_data(username)
        if user_data:
            print("Username already exists. Please choose a different username.")
        else:
            self._insert_document('users', username, {'password': password})
            print("Account created successfully!")

    def login(self, username, password):
        """
        Authenticate a user based on username and password.

        Args:
            username (str): Username of the user.
            password (str): Password of the user.
        """
        user_data = self._get_user_data(username)
        if user_data and user_data.get('password') == password:
            self.current_user = username
            print("Login successful!")
        else:
            print("Invalid username or password.")

    def logout(self):
        """Log out the current user."""
        if self.current_user:
            print(f"User '{self.current_user}' has logged out.")
            self.current_user = None
        else:
            print("No user is currently logged in.")

    def add_transaction(self, serial_no, date, name, stock_symbol, transaction_type, count, price, total_amount):
        """
        Add a new stock transaction for the current user.

        Args:
            serial_no (int): Serial number for the transaction.
            date (str): Date of the transaction.
            name (str): Name of the stock.
            stock_symbol (str): Stock symbol.
            transaction_type (str): Either "buy" or "sell".
            count (int): Number of shares.
            price (float): Price per share.
            total_amount (float): Total transaction amount.
        """
        if not self.current_user:
            print("Please login to add a transaction.")
            return

        transaction_data = {
            'Sl_No': serial_no,
            'Date': date,
            'Share': name,
            'Symbol': stock_symbol,
            'Transaction': transaction_type,
            'Count': count,
            'Price': price,
            'Total_Amount': total_amount
        }
        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions_ref.add(transaction_data)
        print("Transaction added successfully!")

    def delete_transaction(self, serial_no):
        """
        Delete a stock transaction by its serial number for the current user.

        Args:
            serial_no (int): The serial number of the transaction to delete.
        """
        if not self.current_user:
            print("Please login to delete a transaction.")
            return

        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions = transactions_ref.where('Sl_No', '==', serial_no).stream()

        deleted = False
        for transaction in transactions:
            transaction.reference.delete()
            print(f"Transaction with serial number {serial_no} deleted.")
            deleted = True

        if not deleted:
            print(f"No transaction found with serial number {serial_no}.")

    def list_transactions(self):
        """List all stock transactions for the current user."""
        if not self.current_user:
            print("Please login to view transactions.")
            return

        df= self.transactions_to_dataframe()
        portfolio=StockPortfolio(dataframe=df)
        portfolio.driver()
        

    def _insert_document(self, collection_name, document_id, data):
        """Insert a document into a specified collection."""
        self.db.collection(collection_name).document(document_id).set(data)

    def _get_user_data(self, username):
        """Retrieve user data from the Firestore."""
        doc_ref = self.db.collection('users').document(username)
        return doc_ref.get().to_dict() if doc_ref.get().exists else None
    
    def transactions_to_dataframe(self):
        """
        Converts the user's transactions into a pandas DataFrame.

        Returns:
            pd.DataFrame: DataFrame containing all transactions if login is successful.
                          None if login fails or no transactions are found.
        """
       
        # Fetch transactions for the user
        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions = transactions_ref.stream()

        # Convert transactions to a list of dictionaries
        transaction_list = []
        for transaction in transactions:
            transaction_data = transaction.to_dict()
            transaction_list.append(transaction_data)

        # Check if there are any transactions
        if not transaction_list:
            print("No transactions found for this user.")
            return None

        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame(transaction_list)
        
        # Reordering columns to match df
        df = df[['Sl_No', 'Date', 'Share', 'Symbol', 'Transaction', 'Count', 'Price', 'Total_Amount']]

        # Renaming columns to match df
        df.rename(columns={'Sl_No': 'Sl.No.', 'Total_Amount': 'Total Amount'}, inplace=True)

        # Removing the time component from the 'Date' column
        df['Date'] = df['Date'].dt.date

        # Ensuring 'Date' is in datetime format without time zone information (if necessary)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Sorting df by 'Sl.No.' in ascending order
        df = df.sort_values(by='Sl.No.').reset_index(drop=True)
        
        # Capitalizing the uncapitalized transaction entries
        df['Transaction'] = df['Transaction'].str.capitalize()

        return df
    
    def add_transactions_from_excel(self, filepath="TransactionDeets.xlsx", username='Joel Joseph Justin', password='1234'):
        """
        Add transactions from an Excel sheet to a user's Firestore transaction collection.

        Args:
            manager (StockTransactionManager): Instance of the StockTransactionManager class.
            filepath (str): Path to the Excel file containing transaction data.
            username (str): Username of the account to add transactions to.
            password (str): Password of the account.
        """
        # Attempt login
        self.login(username, password)
        if not self.current_user:
            print("Failed to login. Transactions not added.")
            return
        
        
        # Load Excel data
        data = pd.ExcelFile(filepath)
        sheet_data = data.parse(data.sheet_names[0])
        
        # Loop through each row and add the transaction
        for _, row in sheet_data.iterrows():
            self.add_transaction(
                serial_no=row['Sl.No.'],
                date=row['Date'],
                name=row['Share'],
                stock_symbol=row['Symbol'],
                transaction_type=row['Transaction'].lower(),
                count=row['Count'],
                price=row['Price'],
                total_amount=row['Total Amount']
            )
        
        self.logout()
        
        print(f"All transactions from {filepath} have been successfully added to {username}'s account.")



def main():
    """Main function to interact with the StockTransactionManager."""
    
    load_dotenv()
    # Store all variables in a single dictionary
    firebase_config = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
        "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
    }

    service_account_path = firebase_config
    manager = StockTransactionManager(service_account_path)

    #manager.add_transactions_from_excel()
    
    while True:
        print("\nWelcome to the Stock Transaction Manager")
        print("1. Create Account")
        print("2. Login")
        print("3. Add Transaction")
        print("4. Delete Transaction")
        print("5. List Transactions")
        print("6. Logout")
        print("7. Exit")

        choice = input("Choose an option: ")
        
        if choice == '1':
            username = input("Enter a new username: ")
            password = input("Enter a new password: ")
            manager.create_account(username, password)

        elif choice == '2':
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            manager.login(username, password)

        elif choice == '3':
            if manager.current_user:
                serial_no = int(input("Enter serial number: "))
                date = input("Enter date (YYYY-MM-DD): ")
                name = input("Enter stock name: ")
                stock_symbol = input("Enter stock symbol: ")
                transaction_type = input("Enter transaction type (buy/sell): ").lower()
                count = int(input("Enter number of shares: "))
                price = float(input("Enter price per share: "))
                total_amount = count * price
                manager.add_transaction(serial_no, date, name, stock_symbol, transaction_type, count, price, total_amount)
            else:
                print("Please login to add a transaction.")

        elif choice == '4':
            if manager.current_user:
                serial_no = int(input("Enter serial number of transaction to delete: "))
                manager.delete_transaction(serial_no)
            else:
                print("Please login to delete a transaction.")

        elif choice == '5':
            manager.list_transactions()

        elif choice == '6':
            manager.logout()

        elif choice == '7':
            print("Exiting program...")
            break

        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
