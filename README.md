# Travel Planner

A REST API for planning trips and collecting places to visit.

A **project** is a trip that holds **1–10 places**. Each place is a real artwork
imported from the public [Art Institute of Chicago API](https://api.artic.edu/docs/).
Travellers add notes to places and mark them as visited — and once *every* place in a
project is visited, the project is automatically marked **completed**.

**Tech stack:** Django + Django REST Framework · `uv` for dependencies · SQLite ·
`httpx` for the external API · `drf-spectacular` for Swagger/OpenAPI docs.

---

## Quick start (Docker — recommended)

You only need Docker installed. From the project folder:

```bash
docker compose up --build
```

That's it. The command builds the image, runs database migrations, and starts the
server. When you see `Starting development server at http://0.0.0.0:8000/`, open:

- **API docs (where you click around):** http://localhost:8000/api/docs/
- **Projects endpoint:** http://localhost:8000/api/projects/

To stop it: press `Ctrl+C`, then `docker compose down`.

---

## Quick start (local, without Docker)

You need **Python 3.13+** and [**uv**](https://docs.astral.sh/uv/) installed.

```bash
uv sync                                # install dependencies into a virtualenv
uv run python manage.py migrate        # create the SQLite database
uv run python manage.py runserver      # start the server
```

Then open http://localhost:8000/api/docs/.

> The server keeps running (this is normal — it's waiting for requests). Test it from
> your browser or a **second** terminal window. Stop it with `Ctrl+C`.

---

## How to use it (where to click)

The easiest way to try the API is the built-in **Swagger UI**:

1. Open **http://localhost:8000/api/docs/**.
2. Pick an endpoint, e.g. `POST /api/projects/`.
3. Click **“Try it out”**, edit the JSON body, then click **“Execute”**.
4. Scroll down to see the response and status code.

Prefer clicking through HTML forms? Django REST Framework also ships a browsable API —
just open **http://localhost:8000/api/projects/** in your browser and use the form at
the bottom of the page.

### A 60-second walkthrough

Real Art Institute artwork IDs you can use: `27992`, `28560`, `129884`, `129885`.

1. **Create a project with a place** → returns `201`, project status `planning`:
   ```bash
   curl -X POST http://localhost:8000/api/projects/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Chicago art tour", "places": [{"external_id": "27992"}]}'
   ```
   The place title (e.g. *“A Sunday on La Grande Jatte — 1884”*) is fetched
   automatically from the Art Institute API.

2. **Add a note and mark it visited** → the project flips to `completed`:
   ```bash
   curl -X PATCH http://localhost:8000/api/projects/1/places/1/ \
     -H "Content-Type: application/json" \
     -d '{"notes": "Loved it", "visited": true}'
   ```

3. **Try to delete that project** → returns `400` (it has a visited place):
   ```bash
   curl -X DELETE http://localhost:8000/api/projects/1/
   ```

---

## API reference

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/projects/` | List projects |
| POST | `/api/projects/` | Create a project (optionally with a `places` array) |
| GET | `/api/projects/{id}/` | Retrieve a project |
| PATCH | `/api/projects/{id}/` | Update `name` / `description` / `start_date` |
| DELETE | `/api/projects/{id}/` | Delete a project (blocked if any place is visited) |
| GET | `/api/projects/{id}/places/` | List places in a project |
| POST | `/api/projects/{id}/places/` | Add a place (validated against the Art Institute API) |
| GET | `/api/projects/{id}/places/{place_id}/` | Retrieve a place |
| PATCH | `/api/projects/{id}/places/{place_id}/` | Update `notes` / `visited` |
| GET | `/api/docs/` | Swagger UI |
| GET | `/api/schema/` | Raw OpenAPI schema |

### Business rules

- A project holds at most **10** places; the same external place can't be added twice.
- A place is **validated against the Art Institute API** before it is stored — unknown
  IDs are rejected with `400`.
- A project **cannot be deleted** while any of its places is marked as visited.
- A project is automatically **completed** once all of its places are visited.

---

## Running the tests

```bash
uv run pytest
```

Covers the core business rules (place limit, duplicate prevention, external-API
validation, auto-completion, delete protection). The external API is mocked, so the
tests run offline.

---

## Configuration

Set via environment variables (sensible defaults are used if unset):

| Variable | Default | Description |
|----------|---------|-------------|
| `ARTIC_API_BASE_URL` | `https://api.artic.edu/api/v1` | Base URL of the Art Institute API |
| `ARTIC_API_TIMEOUT` | `10` | HTTP timeout in seconds for API calls |

---

## Troubleshooting

- **`{"detail":"Not Found"}` at `/api/projects/`** — you're hitting an old/stale server
  on port 8000. Stop any leftover containers (`docker compose down --remove-orphans`)
  and start again.
- **`port is already allocated` / `Bind for 0.0.0.0:8000 failed`** — something else is
  already using port 8000 (often an old container). Run `docker ps` to find it and
  `docker rm -f <name>`, or `docker compose down --remove-orphans`.
- **Empty list `[]`** — that's the correct, healthy response when you have no projects
  yet. Create one with the `POST` example above.
- **`400` when adding a place** — the `external_id` doesn't exist in the Art Institute
  API. Use a known ID like `27992`.
