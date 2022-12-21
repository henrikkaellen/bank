import sys
import pickle
import logging
from bank import Bank
from decimal import *
import datetime
from transaction import Transaction, Base
from account import OverdrawError
from account import TransactionLimitError
from account import TransactionSequenceError

import sqlalchemy
from sqlalchemy.orm.session import sessionmaker


getcontext().rounding = ROUND_HALF_UP

class BankCLI:
    """Display a menu for bank and respond to choices when run."""


    def __init__(self):
        self._session = Session()

        self._bank = self._session.query(Bank).first()
        logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug("Loaded from bank.db")
        if not self._bank:
            self._bank = Bank()
            self._session.add(self._bank)
            self._session.commit()
            logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.debug("Saved to bank.db")

        self._selected_account = None

        self._choices = {
            "1": self._open_account,
            "2": self._summary,
            "3": self._select_account,
            "4": self._list_transactions,
            "5": self._add_transactions,
            "6": self._interest_and_fees,
            "7": self._quit,
        }
        
    def _display_BankCLI(self):
        print(f"""--------------------------------
Currently selected account: {self._selected_account}
Enter command
1: open account
2: summary
3: select account
4: list transactions
5: add transaction
6: interest and fees
7: quit""")

    def run(self):
        """Display the bank menu and respond to choices."""
        while True:
            self._display_BankCLI()
            choice = input(">")
            action = self._choices.get(choice)
            if action:
                action()
            else:
                print("{0} is not a valid choice".format(choice))

    def _open_account(self):
        account_type = input("Type of account? (checking/savings)\n>")

        while True:
            amount = input("Initial deposit amount?\n>")
            try:
                amount = Decimal(amount)
            except InvalidOperation:
                print("Please try again with a valid dollar amount.")
                continue

            break

        a = self._bank.new_account(account_type, self._session)

        try:
            a.add_transaction(Decimal(amount), datetime.date.today(), self._session)
        except OverdrawError:
            print("This transaction could not be completed due to an insufficient account balance.") 
        
        self._session.commit()
        logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug("Saved to bank.db")

    def _summary(self, accounts=None):
        if accounts is None:
            accounts = self._bank.all_accounts()
        for account in accounts:
            print(account)

    def _select_account(self):
        account_id = input("Enter account number\n>")

        self._selected_account = self._bank.find_account(account_id)

        

    def _list_transactions(self):
        try:
            sorted_transaction_list = self._selected_account.sort_transactions()
            for transaction in sorted_transaction_list:
                transaction.print_transaction()
        except AttributeError: 
            print("This command requires that you first select an account.")

    def _add_transactions(self):
        while True:
            amount = input("Amount?\n>")
            try:
                amount = Decimal(amount)
            except InvalidOperation:
                print("Please try again with a valid dollar amount.")
                continue

            break

        while True:
            date = input("Date? (YYYY-MM-DD)\n>")
            try:
                date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                print("Please try again with a valid date in the format YYYY-MM-DD.")
                continue

            break


        try:
            self._selected_account.add_transaction(amount, date, self._session)
            self._session.commit()
            logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.debug("Saved to bank.db")
        except AttributeError: 
            print("This command requires that you first select an account.")
        except OverdrawError:
            print("This transaction could not be completed due to an insufficient account balance.")
        except TransactionLimitError:
            print("This transaction could not be completed because the account has reached a transaction limit.")
        except TransactionSequenceError as e:
            print("New transactions must be from " + str(e.latest_date) +  " onward.")
        

    def _interest_and_fees(self):
        try:
            self._selected_account.assess_interest_and_fees(self._session)
            logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.debug("Triggered fees and interest")
            self._session.commit()
            logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.debug("Saved to bank.db")
        except AttributeError: 
            print("This command requires that you first select an account.")
        except TransactionSequenceError as e:
            print("Cannot apply interest and fees again in the month of " + str(e.latest_date.strftime("%B")) + ".")

    # def _save(self):
    #     with open("bank.pickle", "wb") as f:
    #         pickle.dump(self._bank, f)
    #         logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #         logging.debug("Saved to bank.pickle")

    # def _load(self):
    #     with open("bank.pickle", "rb") as f:   
    #         self._bank = pickle.load(f)
    #         logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    #         logging.debug("Loaded from bank.pickle")

    def _quit(self):
        sys.exit(0)


if __name__ == "__main__":
    engine = sqlalchemy.create_engine(f"sqlite:///bank.db")
    Base.metadata.create_all(engine)

    Session = sessionmaker()
    Session.configure(bind=engine)

    try:
        BankCLI().run()
    except Exception as e:
        print("Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
        logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.error(type(e).__name__ + ": " + repr(str(e)))
