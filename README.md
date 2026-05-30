# Smart Agriculture AI — v1 System Foundation

A production-grade web application foundation for AI-powered crop analysis.
This version establishes the full system infrastructure without an AI model.

## Project Structure

```
smart-agri/
├── app.py                   # Flask application
├── requirements.txt
├── static/
│   ├── css/main.css         # Full design system
│   ├── js/main.js           # Drag-and-drop, preview, form logic
│   └── uploads/             # Uploaded images (auto-created)
└── templates/
    ├── base.html            # Shared layout
    ├── index.html           # Upload page
    ├── result.html          # Result page
    └── 404.html             # Error page
```

## Setup

```bash
# 1. Create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
python app.py
```

The application will be available at http://127.0.0.1:5000

## Configuration

Set the `SECRET_KEY` environment variable before running in any environment:

```bash
export SECRET_KEY="your-secure-random-key"
python app.py
```

## What is active in v1

- Upload page with drag-and-drop, file preview, and client-side validation
- Flask backend with secure filename handling and UUID-based storage
- Result page showing the submitted image and placeholder analysis fields
- 10 MB file size limit enforced on both client and server
- Supported formats: PNG, JPG, JPEG, WEBP, BMP, TIFF
- 404 error page

## What is NOT yet active

- AI/ML model inference
- Disease detection and health scoring
- Recommendations engine
- Database storage
- User authentication

## Next version (v2)

Integration of an AI vision model for disease detection,
health scoring, and agronomic recommendations.
