# Local Music Generator

A web application that uses Facebook's MusicGen-small model to generate music locally without relying on external APIs.

## Features

- Generate music using text prompts
- Control music parameters (length, style, etc.)
- Play, pause, and download generated music
- Apple-style user interface
- Local model deployment with no external dependencies

## Project Structure

```
local-music-generator/
├── backend/             # Python FastAPI backend
│   ├── api/             # API endpoints
│   ├── audio/           # Audio processing utilities
│   ├── config/          # Configuration settings
│   ├── models/          # Model management
│   ├── tests/           # Backend tests
│   ├── utils/           # Utility functions
│   ├── main.py          # Main application entry point
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend
│   ├── public/          # Static assets
│   ├── src/             # Source code
│   │   ├── assets/      # Frontend assets
│   │   ├── components/  # React components
│   │   ├── context/     # React context providers
│   │   ├── hooks/       # Custom React hooks
│   │   ├── pages/       # Page components
│   │   ├── services/    # API services
│   │   ├── styles/      # Global styles
│   │   └── utils/       # Utility functions
│   └── package.json     # Frontend dependencies
└── docs/                # Documentation
```

## Requirements

### Backend
- Python 3.9+
- PyTorch
- FastAPI
- Transformers library

### Frontend
- Node.js 16+
- React 18
- Modern web browser

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd local-music-generator/backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the backend server:
   ```
   python main.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd local-music-generator/frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000`

## Development

### Backend Development

- API endpoints are defined in the `backend/api` directory
- Model management is handled in the `backend/models` directory
- Audio processing utilities are in the `backend/audio` directory
- Configuration settings are in the `backend/config` directory

#### API Framework Features

- Comprehensive error handling with standardized error responses
- Resource monitoring middleware to track CPU, memory, and disk usage
- Request validation middleware for early validation of JSON payloads
- Detailed request logging with timing information
- CORS configuration with specific headers and methods
- OpenAPI documentation customization
- Health check and system monitoring endpoints
- Graceful startup and shutdown procedures

### Frontend Development

- React components are in the `frontend/src/components` directory
- Pages are in the `frontend/src/pages` directory
- API services are in the `frontend/src/services` directory
- Global styles are in the `frontend/src/styles` directory

## License

[MIT License](LICENSE)