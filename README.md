# ☕ Cafe & Wifi REST API

A RESTful API built with Flask that serves a database of laptop-friendly London cafes - whether they have wifi, power sockets and toilets, how many seats, and what a coffee costs. It comes with 20 cafes already in the database.

## Features

- `GET /random` - a random cafe
- `GET /all` - every cafe
- `GET /search?loc=Peckham` - cafes in a location
- `POST /add` - add a cafe
- `PATCH /update-price/<id>?new_price=£2.50` - update a price
- `DELETE /report-closed/<id>?api-key=...` - remove a closed cafe (needs the API key)
- JSON responses with proper status codes (400, 403, 404, 409)

## Built with

Python, Flask, SQLAlchemy, SQLite

## How to run

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python main.py
```

Then open **http://127.0.0.1:5000** in your browser.

The home page lists every endpoint. Use a tool like Postman or `curl` to try the POST, PATCH and DELETE routes.

### API key

Deleting a cafe needs an API key. The default is `TopSecretAPIKey`; set your own with the `CAFE_API_KEY` environment variable.

```bash
curl -X DELETE "http://127.0.0.1:5000/report-closed/1?api-key=TopSecretAPIKey"
```
