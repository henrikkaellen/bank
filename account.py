from transaction import Transaction, Base
from decimal import *
import datetime
import calendar
import logging

from sqlalchemy import Column, Integer, String, ForeignKey, DATE, Float
from sqlalchemy.orm import relationship, backref

getcontext().rounding = ROUND_HALF_UP

class OverdrawError(Exception):
    pass

class TransactionLimitError(Exception):
    pass
    

class TransactionSequenceError(Exception):
    def __init__(self, date):
        self.latest_date = date

class Account(Base):

    last_id = 0

    __tablename__ = "account"

    _id = Column(Integer, primary_key=True)
    _bank_id = Column(Integer, ForeignKey("bank._id"))

    _transactions = relationship("Transaction", backref=backref("account"))

    _balance = Column(Float(asdecimal=True))

    #_balance = Column(String)
    latest_date = Column(DATE)

    _interest_rate = Column(Float(asdecimal=True))

    #name = Column(String(50))
    type = Column(String(20))

    __mapper_args__ = {
        'polymorphic_identity':'account',
        'polymorphic_on': type
    }

    #accountType = relationship("accountType", back_populates="account")

    def __init__(self):
        """initialize an account with a list of transactions and 
        a balance of the total amount. Automatically set the account's
        unique id."""

        # create list for transactions and add inital transaction
        #self._transactions = []
        self._balance = Decimal(0)
        self.latest_date = datetime.date.today()

        # give account id and update static variable
        Account.last_id += 1
        self._id = Account.last_id

        logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug(f"Created account: {self._id}")
    
    def id_matches(self, id):
        """
        Determine if this account has the given id
        """
        return self._id == int(id)
    
    def get_id(self):
        """Returns the accounts id"""
        return self._id
    
    def add_transaction(self, amount, date, session):
        """Checks a pending transaction to see if it is allowed and adds it to the account if it is.
        """
        if amount >= 0 or self._balance > abs(amount):
            limits_ok = self._check_limits(amount, date)
            if limits_ok:
                if date >= self.latest_date:
                    self._balance += amount
                    t = Transaction(amount, date)
                    self._transactions.append(t)
                    str(t._amount)
                    session.add(t)
                    self.latest_date = date

                    logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
                    logging.debug(f"Created transaction: {self._id}, {amount}")
                else:
                    raise(TransactionSequenceError(self.latest_date))
            else:
                raise(TransactionLimitError)
        else:
            raise(OverdrawError)

    
    def _check_limits(self, amount, date):
        return True
    
    def sort_transactions(self):
        """
        Sort the transactions by date
        """
        return sorted(self._transactions)
    
    def assess_interest_and_fees(self, session):
        """Calculates interest for an account balance and adds it as a new transaction exempt from limits. 
            Also checks if fees apply.
        """        
        month_range = calendar.monthrange(self.latest_date.year, self.latest_date.month)
        date = datetime.datetime(self.latest_date.year, self.latest_date.month, month_range[1]).date()

        for t in self._transactions:
            if t.check_flag_and_date(date):
                raise(TransactionSequenceError(self.latest_date))

        amount = self._balance * self._interest_rate

        self.latest_date = date
        self._balance += amount
        t = Transaction(amount, date, 1)
        self._transactions.append(t)
        session.add(t)

        logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug(f"Created transaction: {self._id}, {amount}")

        self._fees(date, session)

    def _fees(self, date, session):
        pass

    def __str__(self):
        """Formats the account number and balance of the account.
        For example, '#000000001,<tab>balance: $50.00'
        """    
        return f"#{self._id:09},\tbalance: ${Decimal(self._balance):,.2f}"


class CheckingAccount(Account):
    """Create a new checking account which inherits
    properties from the Account class"""


    __mapper_args__ = {
        'polymorphic_identity':'Checking',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interest_rate = Decimal("0.0012")

    def __str__(self):
        """Formats the type, account number, and balance of the account.
        For example, 'Checking#000000001,<tab>balance: $50.00'
        """ 
        return "Checking" + super().__str__()
    
    def _fees(self, date, session):
        """Adds a low balance fee if balance is below a particular threshold. Fee amount and balance threshold are defined on the CheckingAccount.
        """
        if self._balance < 100:
            self._balance += -10
            t = Transaction(-10, date, 1)
            self._transactions.append(t)
            session.add(t)
            logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.debug(f"Created transaction: {self._id}, -10")


class SavingsAccount(Account):

    __mapper_args__ = {
        'polymorphic_identity':'Savings',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interest_rate = Decimal("0.029")

    def __str__(self):
        """Formats the type, account number, and balance of the account.
        For example, 'Savings#000000001,<tab>balance: $50.00'
        """ 
        return "Savings" + super().__str__()
    
    def _check_limits(self, amount, date):
        """ Check if the daily or monthly limit has been reached. """
        day_counter = 0
        month_counter = 0
        for transaction in self._transactions:
            if transaction.check_day_limit(date):
                day_counter += 1
            if transaction.check_month_limit(date):
                month_counter += 1

        if day_counter < 2 and month_counter < 5:
            return True
        else:
            return False