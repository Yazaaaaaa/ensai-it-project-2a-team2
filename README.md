# NEO-Watch 

NEO-Watch is a web application to follow **Near-Earth Objects (NEOs)**: asteroids whose orbits bring them close to our planet. It collects the data published by NASA, lets you explore it, and warns you when an object passes closer than you want.

## What is it for?

- **Explore** the catalogue of asteroids and their close approaches to Earth, with the information that matters (size, hazardous status, distance, velocity, date of passage).
- **Follow** the asteroids you care about and see how their distance from Earth evolves over time.
- **Be warned** automatically when an asteroid matches a risk you define, for example *"an asteroid larger than 100 m passing within 5 million km of Earth"*.
- **Contribute**: add an object you observed yourself to the database.

## Features

| | Feature | What you can do |
|---|---|---|
| **F1** | Users and access | Create an account and log in. Administrators manage user accounts, view the connection history and update the data from NASA's API. |
| **F2** | Dashboard | See an overview of the database: number of NEOs, how many are potentially hazardous, the largest objects, and your favorite NEOs. |
| **F3** | Browse NEOs | Search by name, identifier, size, magnitude, hazardous status, orbiting body or date of passage. Sort the results and export them (CSV or JSON). Each NEO has a detail page with its close approaches. |
| **F4** | Create a NEO | Add your own NEO. Custom NEOs are never overwritten when the database is refreshed with NASA data. |
| **F5** | Favorites | Add or remove NEOs from your favorites list. For each favorite, the history of its distance from Earth is plotted and can be downloaded as an image. |
| **F6** | Alerts | Define alerts on a given NEO or on any NEO, with a distance threshold and an optional minimum size. Triggered alerts are shown as a notification when you log in, and listed in the *Alerts* tab. |

## Requirements

- **Python 3.10** or later
- **PostgreSQL** (a running server and a database you can write to)
- A **NASA API key** (a free key can be requested at <https://api.nasa.gov>, `DEMO_KEY` works with strict rate limits)
- **Git**

## Installation

### 1. Get the code

```bash
git clone <repository-url>
cd ensai-it-project-2a-team2
```

### 2. Install the dependencies

uv sync --project backend --all-extras

### 3. Configure the application

Create a `.env` file at the root of the repository (or export the same variables in your shell):

```dotenv
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=<your database>
POSTGRES_USER=<your user>
POSTGRES_PASSWORD=<your password>
SCHEMA=neow

# NASA API
NASA_API_KEY=<your key>
```

### 4. Create the database tables

From the `backend/src` folder:

```bash
cd backend/src
python -m utils.reset_database
```

> ⚠️ This script **drops and recreates** the tables of the schema. Run it only on a new installation.

### 5. Load the NASA data

Still in `backend/src`:

```bash
python -m utils.import_all_data
```

The first import can take several minutes. Administrators can refresh the data later from the application.

## Launching the application

The application has two parts that must both be running: the **backend** (API) and the **frontend** (web interface). Open two terminals, with the virtual environment activated in each.

**Terminal 1: backend** (from `backend/src`)

```bash
uv run --project backend python backend/src/main.py
```

The API is then available at <http://localhost:5000>, and its interactive documentation at <http://localhost:5000/docs>.

**Terminal 2: frontend** (from the root of the repository)

```bash
cd frontend
```
and
```bash
uv run --project . streamlit run src/app.py
```

Open <http://localhost:8000> in your browser.

## Quick tour

1. **Sign up** from the home page with an email and a password (8 characters minimum), then **log in**.
2. In **Browse a NEO**, search with the filters, click a row to see its details and close approaches, then click **Add to favorites**.
3. In **Favorites**, select a NEO to see the evolution of its distance from Earth, and download the chart.
4. In **Alerts**, create an alert (distance threshold, optional minimum size). If an upcoming close approach matches, a notification appears the next time you log in.
5. In **Add a NEO**, record an object you observed yourself.

