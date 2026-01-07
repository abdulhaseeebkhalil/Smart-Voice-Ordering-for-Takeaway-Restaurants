# AI-Powered Takeaway Order Automation (MVP)

This project is a working MVP for automated phone ordering using Twilio voice, OpenAI for understanding, SQLite for persistence, and ESC/POS printing. It includes a minimal staff dashboard and a sample menu.

## Features
- Twilio webhook call flow with speech gather
- Menu-constrained order extraction with structured JSON
- Follow-up questions for missing info
- Order confirmation loop
- SQLite order tracking
- ESC/POS printing with dry-run mode
- Lightweight dashboard with reprint

## Folder Structure
```
app/
  api/
  services/
  utils/
  static/
  main.py
  config.py
  db.py
  models.py
  schemas.py
menu.json
Dockerfile
docker-compose.yml
requirements.txt
```

## Setup (Local)
1. Create a virtualenv and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy env:
   ```bash
   cp .env.example .env
   ```
3. Update `.env` with your keys and base URL.
4. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Open the dashboard at `http://localhost:8000/dashboard`.

## Setup (Docker)
```bash
docker-compose up --build
```

## Twilio Webhook Configuration
- Point your Twilio phone number voice webhook to:
  - **POST** `https://<your-ngrok-url>/twilio/voice`
- For local testing with ngrok:
  ```bash
  ngrok http 8000
  ```
  Use the HTTPS forwarding URL as `BASE_URL` in `.env`.

## Environment Variables
See `.env.example` for all settings. Key items:
- `OPENAI_API_KEY`: OpenAI key
- `BASE_URL`: Public base URL for Twilio webhooks
- `DASHBOARD_PASSWORD`: shared password for staff dashboard
- `FALLBACK_FORWARD_NUMBER`: number to forward to if AI fails
- `PRINTER_MODE`: `dryrun`, `usb`, or `network`

## Printing
- Dry-run mode writes tickets to `./data/prints/`.
- USB printing needs vendor/product IDs.
- Network printing needs IP + port.

## Menu Updates
Edit `menu.json` to update categories, items, variants, addons, and prices. The assistant only offers items from this menu.

## API Endpoints
- `POST /twilio/voice` - Twilio entrypoint
- `POST /twilio/process` - speech handling
- `POST /twilio/confirm` - confirmation
- `GET /api/orders` - list orders (auth)
- `GET /api/orders/{order_id}` - order detail (auth)
- `POST /api/orders/{order_id}/reprint` - reprint ticket (auth)

## Testing
```bash
pytest
```

## Notes
- LLM output is stored in `confidence_notes` with the transcript.
- If AI fails twice, calls are forwarded to `FALLBACK_FORWARD_NUMBER`.
- For production, add signature validation for Twilio requests and a proper auth layer.
- The MVP uses Twilio <Gather> speech transcription; optional Whisper transcription is available in `app/services/speech_to_text.py`.
