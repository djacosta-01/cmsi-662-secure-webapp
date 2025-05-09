import sqlite3


def get_balance(account_number, owner):
    try:
        con = sqlite3.connect("bank.db")
        cur = con.cursor()
        cur.execute(
            """
            SELECT balance FROM accounts where id=? and owner=?""",
            (account_number, owner),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]
    finally:
        con.close()


def get_user_accounts(owner):
    """
    Retrieves all accounts belonging to a specific user.
    Returns:
        - List of tuples containing (account_id, balance)
    """
    try:
        con = sqlite3.connect("bank.db")
        cur = con.cursor()
        cur.execute(
            """
            SELECT id, balance FROM accounts WHERE owner=? ORDER BY id""",
            (owner,),
        )
        accounts = cur.fetchall()
        return accounts
    finally:
        con.close()


def do_transfer(source, target, amount, owner=None):
    """
    Performs a transfer between accounts.
    Returns:
        - True if the transfer was successful
        - False if target account does not exist or source account doesn't belong to owner
    Raises:
        - Exception if any other error occurs
    """
    try:
        con = sqlite3.connect("bank.db")
        cur = con.cursor()

        # Check if source account belongs to owner (if owner is provided)
        if owner is not None:
            cur.execute(
                """
                SELECT id FROM accounts WHERE id=? AND owner=?""",
                (source, owner),
            )
            row = cur.fetchone()
            if row is None:
                return False  # Source account doesn't exist or doesn't belong to owner

        cur.execute(
            """
            SELECT id FROM accounts where id=?""",
            (target,),
        )
        row = cur.fetchone()
        if row is None:
            return False

        con.execute("BEGIN TRANSACTION")

        cur.execute(
            """
            UPDATE accounts SET balance=balance-? where id=?""",
            (amount, source),
        )

        cur.execute(
            """
            UPDATE accounts SET balance=balance+? where id=?""",
            (amount, target),
        )

        con.commit()
        return True
    except Exception as e:
        con.rollback()
        raise e
    finally:
        con.close()
