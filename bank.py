from account import CheckingAccount
from account import SavingsAccount
from decimal import *
from transaction import Base

from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship, backref

getcontext().rounding = ROUND_HALF_UP

class Bank(Base):
    """Represent a collection of accounts that can be opened,
    add new transactions, and be searched."""

    __tablename__ = "bank"

    _id = Column(Integer, primary_key=True)

    _accounts = relationship("Account", backref=backref("bank"))
    
    def new_account(self, account_type, session):
        """Create a new bank account and add it to the list."""
        if account_type == "checking":
            account = CheckingAccount()
        else:
            account = SavingsAccount()
        
        self._accounts.append(account)
        session.add(account)
        return account
    
    def all_accounts(self):
        """Returns all accounts in the bank"""

        return self._accounts
    
    def find_account(self, account_id):
        """Locate the account with the given id."""
        for account in self._accounts:
            if account.id_matches(account_id):
                return account
        return None
        