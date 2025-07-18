# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a local music generator application that uses Facebook's MusicGen-small model to generate music locally without external API dependencies. The project consists of a Python FastAPI backend and a React frontend with TypeScript.

## Project Structure

```
local-music-generator/
├── backend/             # Python FastAPI backend
│   ├── api/             # API endpoints and routing
│   ├── audio/           # Audio processing utilities
│   ├── config/          # Configuration settings
│   ├── models/          # Model management and resource monitoring
│   ├── tests/           # Backend tests
│   ├── utils/           # Backend utility functions
│   ├── main.py          # FastAPI application entry point
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend with TypeScript
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── services/    # API service layer
│   │   ├── hooks/       # Custom React hooks
│   │   ├── context/     # React context providers
│   │   └── utils/       # Frontend utilities
│   ├── package.json     # Frontend dependencies
│   ├── tsconfig.json    # TypeScript configuration
│   └── vite.config.ts   # Vite build configuration
└── docs/                # Documentation
```

## Development Commands

### Backend Development

```bash
# Navigate to backend directory
cd local-music-generator/backend

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py

# Run tests
pytest

# Run specific test
pytest tests/test_model_manager.py

# Run tests with coverage
pytest --cov=.
```

### Frontend Development

```bash
# Navigate to frontend directory
cd local-music-generator/frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Format code
npm run format
```

## Key Architecture Components

### Backend Architecture

- **FastAPI Application**: Main entry point in `main.py` with comprehensive middleware setup
- **Model Management**: `models/model_manager.py` handles MusicGen model lifecycle with resource monitoring
- **Resource Monitoring**: `models/resource_monitor.py` tracks CPU, memory, and disk usage
- **API Structure**: RESTful endpoints organized in `api/` directory with standardized error handling
- **Configuration**: Centralized settings in `config/settings.py` with environment-specific overrides

### Frontend Architecture

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Strict typing with path aliases (`@/` for src directory)
- **Vite**: Build tool with hot module replacement and API proxy to backend
- **Styled Components**: CSS-in-JS styling solution
- **WaveSurfer.js**: Audio waveform visualization and playback

### Model Integration

The application uses Facebook's MusicGen-small model with:
- Automatic GPU/CPU detection and fallback
- Memory usage monitoring and resource limits
- Asynchronous model loading to prevent blocking
- Model state management with health checks

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/status` - Detailed API status
- `GET /api/system/*` - System monitoring endpoints
- `GET /api/models/*` - Model management endpoints

## Configuration

Backend configuration is managed in `config/settings.py`:
- Model settings (GPU usage, auto-load)
- Audio settings (format, duration, sample rate)
- System settings (memory limits, logging)
- CORS configuration for frontend communication

## Testing

Backend tests are located in `tests/` and cover:
- API endpoint testing
- Model manager functionality
- Resource monitoring
- Error handling

Use `pytest` for running tests with standard Python testing practices.

## Dependencies

### Backend Key Dependencies
- `fastapi>=0.100.0` - Modern async web framework
- `torch>=2.0.0` - PyTorch for model inference
- `transformers>=4.30.0` - Hugging Face transformers
- `librosa>=0.10.0` - Audio processing
- `psutil>=5.9.0` - System resource monitoring

### Frontend Key Dependencies
- `react@^18.2.0` - React framework
- `typescript@^5.1.3` - TypeScript compiler
- `vite@^4.3.9` - Build tool
- `styled-components@^6.0.0` - CSS-in-JS
- `wavesurfer.js@^7.0.0` - Audio visualization

## Development Notes

- The backend runs on port 8000 by default
- The frontend runs on port 3000 with API proxy to backend
- Model files are stored in `backend/data/models/`
- Generated audio files are saved in `backend/data/audio/`
- The application supports both GPU and CPU inference with automatic fallback
- Resource monitoring is built-in and tracks system performance