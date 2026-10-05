# Tricount Clone

A simple **Tricount-inspired web application** for managing shared expenses between groups of people.

The application allows users to create expense groups, add members, record shared expenses, calculate each member's balance, and record settlements between members. The backend is built with **FastAPI** and **SQLite**, while the frontend uses **HTML, CSS, and JavaScript**.

## Features

* Create and manage expense groups
* Add, update, and delete group members
* Add and delete shared expenses
* Choose who paid for an expense
* Choose which members participate in an expense
* Automatically calculate member balances
* Record settlements between members
* View and delete existing settlements
* Store data persistently using SQLite

## How It Works

The application is organized around groups. Each group contains its members, expenses, and settlements.

When an expense is added, the application records the member who paid and the members among whom the expense should be divided. The backend then calculates the individual shares and updates the balances accordingly.
The balance system takes both expenses and recorded settlements into account to determine the current balance of each member.

## Technologies Used

* **Python**
* **FastAPI** — backend REST API
* **SQLite** — database
* **HTML** — frontend structure
* **CSS** — styling and layout
* **JavaScript** — frontend logic and API communication

The frontend communicates with the FastAPI backend through HTTP requests to endpoints for groups, members, expenses, balances, and settlements.

## Project Structure

```text
.
├── main.py
├── index.html
├── group.html
├── style.css
└── tricount.db
```

### Backend

`main.py` contains the FastAPI application, API endpoints, data models, SQLite database operations, and database initialization.

### Frontend

`index.html` provides the group management interface, while `group.html` provides the interface for members, expenses, balances, and settlements.
`style.css` provides the application's dark-themed interface, cards, forms, buttons, and balance styling.

## Purpose

This project was developed as a practical exercise in building a full-stack web application and working with:

* REST API development
* Database management with SQLite
* Frontend-to-backend communication
* CRUD operations
* Data modeling with Pydantic
* Expense splitting and balance calculations
