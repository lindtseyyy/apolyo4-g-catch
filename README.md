# G-Catch

Forensic pixel analysis for GCash transaction receipt verification. Detects forged or tampered digital receipts using computer vision forensics — built for CodeKada Hackathon 2026 by Apolyo 4.

## How It Works

G-Catch runs a multi-detector forensic pipeline on uploaded receipt screenshots:

1. **Error Level Analysis (ELA)** — Re-encodes the image at a known JPEG quality and measures pixel-level differences. AI-generated or tampered images exhibit unnaturally high noise in flat background areas.
2. **Typography & Kerning Forensics** — Extracts receipt fields via OCR and checks character aspect ratios, kerning gaps, baseline alignment, and font consistency for each field.
3. **Micro-Alignment Detection** — Verifies that digits in the amount field share a consistent baseline. Manually pasted digits typically drift by 2+ pixels.
4. **Reference Number Cross-Check** — Queries Firestore to detect duplicate reference numbers across users.

Each detector returns per-field verdicts and integrity scores, which are combined into a final forgery assessment.

## Tech Stack

| Layer    | Technology                                            |
|----------|-------------------------------------------------------|
| Backend  | Python 3.11, FastAPI, OpenCV, Tesseract OCR           |
| Frontend | Next.js 16 (React 19), Tailwind CSS v4, Framer Motion |
| Auth     | Firebase Auth (Email/Password + Google OAuth)         |
| Database | Firestore (scan history + reference cross-checking)   |

## Project Structure

```
apolyo4-g-catch/
  backend/
    server/           FastAPI app, routes, services, config
    gcatch/           Core analysis library (detectors, pipeline, CLI, utils)
  frontend/
    g-catch/          Next.js app (pages, components, auth, Firestore)
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Tesseract-OCR (`sudo apt-get install tesseract-ocr libgl1 libglib2.0-0`)
- A Firebase project with Auth (Email/Password + Google) and Firestore enabled

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000
```

The API serves at `http://localhost:8000` with:
- `GET /api/v1/health`
- `GET /api/v1/analyzers`
- `POST /api/v1/analyze/receipt` — multipart file upload (JPEG, PNG, TIFF, BMP, WebP; max 10 MB)

### Frontend

```bash
cd frontend/g-catch
npm install
```

Create `.env.local` with your Firebase config:
```
NEXT_PUBLIC_FIREBASE_API_KEY=<your_key>
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<your_domain>
NEXT_PUBLIC_FIREBASE_PROJECT_ID=<your_project_id>
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=<your_bucket>
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=<your_sender_id>
NEXT_PUBLIC_FIREBASE_APP_ID=<your_app_id>
```

```bash
npm run dev
```

Opens at `http://localhost:3000`. The frontend calls the backend at `NEXT_PUBLIC_API_URL` (falls back to `http://localhost:8000` in development).

### CLI (Optional)

The backend includes a CLI for offline analysis:

```bash
cd backend
source venv/bin/activate
python -m gcatch.cli ela <image_path>
python -m gcatch.cli scan-receipt <image_path>
python -m gcatch.cli verify <image_path>
```

## Deployment

### Backend (Railway)

The root `railway.toml` configures a Dockerfile-based build from `backend/`. The health check hits `GET /` on port 8000.

### Frontend

Build and deploy the Next.js app to Vercel or Firebase Hosting:

```bash
cd frontend/g-catch
npm run build && npm start
```
