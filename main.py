from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import sqlite3
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def readroot():
    return{"message": "Hello,Tricount clone!"}


class Member(BaseModel):
    id: int
    name: str


class Group(BaseModel):
    id: int
    name: str
    members: list[Member] = []


class Expense(BaseModel):
    id: int
    description: str
    amount: float
    paid_by: int
    split_among: list[int]


class Settlement(BaseModel):
    id: int
    from_member: int
    to_member: int
    amount: float


@app.post("/groups")
def parse(group: Group):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("INSERT INTO groups (id, name) VALUES (?, ?)", (group.id, group.name))
    conn.commit()
    conn.close()
    return group


@app.get("/groups")
def get_groups():
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT * FROM groups")
    info = c.fetchall()
    conn.close()
    return info


@app.post("/groups/{group_id}/members")
def add_member(group_id: int, member: Member):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT id FROM groups WHERE id=?", (group_id,))
    group = c.fetchone()
    if group is None:
        conn.close()
        raise HTTPException(status_code=404, detail="GROUP NOT FOUND")
    c.execute("INSERT INTO members (id,name,group_id) VALUES (?,?,?)", (member.id, member.name, group_id))
    conn.commit()
    conn.close()
    return member


@app.get("/groups/{group_id}/members")
def get_member(group_id: int):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT * FROM members WHERE group_id=?", (group_id,))
    info = c.fetchall()
    conn.close()
    return info
@app.delete("/groups/{group_id}/members/{member_id}")
def delete_member(group_id: int, member_id: int):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT id FROM members WHERE id=? AND group_id=?",(member_id,group_id))
    if c.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="MEMBER NOT FOUND")
    c.execute("DELETE FROM members WHERE id=? AND group_id=?",(member_id,group_id))
    conn.commit()
    conn.close()
    return{"message":"Member deleted"}
@app.put("/groups/{group_id}/members/{member_id}")
def update_member(group_id: int, member_id: int, member: Member):
    conn=sqlite3.connect("tricount.db")
    c=conn.cursor()
    c.execute("SELECT id FROM members WHERE id=? AND group_id=?",(member_id,group_id))
    if c.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404,detail="MEMBER NOT FOUND")
    c.execute("UPDATE members SET name=? WHERE id=? AND group_id=?",(member.name,member_id,group_id))  
    conn.commit()
    conn.close()
    return{"Message":"Member name updated "} 
@app.post("/groups/{group_id}/expenses")
def add_expense(group_id: int, expense: Expense):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT id FROM groups WHERE id=?", (group_id,))
    group = c.fetchone()
    if(group is None):
        conn.close()
        raise HTTPException(status_code=404, detail="GROUP NOT FOUND")
    c.execute("SELECT id FROM members WHERE id=?", (expense.paid_by,))
    pd = c.fetchone()
    if(pd is None):
        conn.close()
        raise HTTPException(status_code=404, detail="NOT VALID MEMBER")
    c.execute("INSERT INTO expenses (id,description,amount,paid_by,group_id) VALUES (?,?,?,?,?)",
              (expense.id, expense.description, expense.amount, expense.paid_by, group_id))
    for member_id in expense.split_among:
        c.execute("INSERT INTO expense_splits (expense_id, member_id) VALUES (?, ?)", (expense.id, member_id))
    conn.commit()
    conn.close()
    return expense


@app.get("/groups/{group_id}/expenses")
def get_expense(group_id: int):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT * FROM expenses WHERE group_id=?", (group_id,))
    info = c.fetchall()
    conn.close()
    return info
@app.delete("/groups/{group_id}/expenses/{expense_id}")
def delete_expense(group_id:int,expense_id:int):
    conn=sqlite3.connect("tricount.db")
    c=conn.cursor()
    c.execute("SELECT * FROM expenses WHERE group_id=? AND id=?",(group_id,expense_id))
    pd=c.fetchone()
    if(pd is None):
        conn.close()
        raise HTTPException(status_code=404, detail="NOT VALID EXPENSE")
    c.execute("DELETE FROM expense_splits WHERE  expense_id=?",(expense_id,))
    c.execute("DELETE FROM expenses WHERE group_id=? AND id=?",(group_id,expense_id))
    conn.commit()
    conn.close()
    return{"message": "expense deleted"}
@app.get("/groups/{group_id}/balances")
def get_balance(group_id: int):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT id,amount,paid_by FROM expenses WHERE group_id=?", (group_id,))
    expenses = c.fetchall()
    balances = {}

    for expense_id, amount, paid_by in expenses:
        c.execute("SELECT member_id FROM expense_splits WHERE expense_id=?", (expense_id,))
        split_members = c.fetchall()

        share = amount / len(split_members)

        balances[paid_by] = balances.get(paid_by, 0) + amount

        for (member_id,) in split_members:
            balances[member_id] = balances.get(member_id, 0) - share
    c.execute("SELECT id,from_member,to_member,amount FROM settlements WHERE group_id=? ", (group_id,))
    split_settlement = c.fetchall()
    for (settlement_id, from_member, to_member, amount) in split_settlement:
        balances[from_member] = balances.get(from_member, 0) + amount
        balances[to_member] = balances.get(to_member, 0) - amount
    conn.close()
    return balances


@app.post("/groups/{group_id}/settlements")
def settle(group_id: int, settlement: Settlement):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT id FROM groups WHERE id=?", (group_id,))
    group = c.fetchone()
    if(group is None):
        conn.close()
        raise HTTPException(status_code=404, detail="GROUP NOT FOUND")
    c.execute("SELECT id FROM members WHERE id=?", (settlement.from_member,))
    fm = c.fetchone()
    if(fm is None):
        conn.close()
        raise HTTPException(status_code=404, detail="MEMBER NOT FOUND")
    c.execute("SELECT id FROM members WHERE id=?", (settlement.to_member,))
    Tm = c.fetchone()
    if(Tm is None):
        conn.close()
        raise HTTPException(status_code=404, detail="MEMBER NOT FOUND")
    c.execute("INSERT INTO SETTLEMENTS (id,group_id,from_member,to_member,amount) VALUES (?,?,?,?,?)",
              (settlement.id, group_id, settlement.from_member, settlement.to_member, settlement.amount))
    conn.commit()
    conn.close()
    return settlement


@app.get("/groups/{group_id}/settlements")
def get_settle(group_id: int):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT * FROM settlements where group_id=?", (group_id,))
    info = c.fetchall()
    conn.close()
    return info
@app.delete("/groups/{group_id}/settlements/{settlement_id}")
def delete_settlement(group_id: int, settlement_id: int):
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("SELECT id FROM settlements WHERE id=? AND group_id=?", (settlement_id, group_id))
    if c.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="SETTLEMENT NOT FOUND")
    c.execute("DELETE FROM settlements WHERE id=? AND group_id=?", (settlement_id, group_id))
    conn.commit()
    conn.close()
    return {"message": "settlement deleted"}


def init_db():
    conn = sqlite3.connect("tricount.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY,name TEXT,group_id INTEGER ,FOREIGN KEY (group_id) REFERENCES groups(id)) ")
    c.execute("CREATE  TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY,description TEXT,amount REAL,paid_by INTEGER,group_id INTEGER,FOREIGN KEY(group_id) REFERENCES groups(id), FOREIGN KEY(paid_by) REFERENCES members(id))")
    c.execute("CREATE TABLE IF NOT EXISTS expense_splits(expense_id INTEGER,member_id INTEGER ,FOREIGN KEY(expense_id) REFERENCES expenses(id),FOREIGN KEY(member_id) REFERENCES members(id))")
    c.execute("CREATE TABLE IF NOT EXISTS settlements(id INTEGER PRIMARY KEY,group_id INTEGER ,from_member INTEGER,to_member INTEGER,amount REAL,FOREIGN KEY(group_id) REFERENCES groups(id),FOREIGN KEY(from_member) REFERENCES members(id),FOREIGN KEY(to_member) REFERENCES members(id))")
    conn.commit()
    conn.close()


init_db()
