# Quick Start Guide - How to Run the Web Scraper

## Prerequisites

Before running, make sure you have:
- **Python 3.8+** installed ([Download](https://www.python.org/downloads/))
- **Node.js 16+** installed ([Download](https://nodejs.org/))
- **npm** (comes with Node.js)

## Installation Steps

### Step 1: Install Backend Dependencies

Open a terminal/command prompt in the project root and run:

```bash
cd backend
pip install -r requirements.txt
cd ..
```

**Note for Windows:** If `pip` doesn't work, try `pip3` or `python -m pip`

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 3: Install Root Dependencies (for Electron)

```bash
npm install
```

## Running the Program

You have **3 options** to run the web scraper:

---

## Option 1: Run Everything Together (Recommended for First Time)

This runs the full Electron desktop app with backend and frontend:

```bash
npm run dev
```

This will:
- Start the Flask backend on `http://localhost:5000`
- Start the React frontend on `http://localhost:5173`
- Launch the Electron desktop app

**Wait for:** You should see "Backend is ready!" in the terminal, then the Electron window will open.

---

## Option 2: Run Backend Only (Python API)

If you just want to use the API or test the backend:

```bash
cd backend
python app.py
```

The API will be available at: `http://localhost:5000`

You can test it by visiting: `http://localhost:5000/api/health`

---

## Option 3: Run Backend + Frontend Separately

### Terminal 1 - Backend:
```bash
cd backend
python app.py
```

### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Then open your browser to: `http://localhost:5173`

---

## Quick Test

Once everything is running:

1. **Open the app** (Electron window or browser at `http://localhost:5173`)
2. **Click "Test API Connection"** - Should show ✅ if backend is running
3. **Enter a URL** - Try `https://example.com`
4. **Add a selector**:
   - Field name: `title`
   - Selector: `h1`
   - Type: `CSS`
5. **Click "Start Scraping"**

---

## Troubleshooting

### "python: command not found"
- **Windows:** Try `py` instead of `python`
- **Mac/Linux:** Make sure Python is installed and in PATH
- Check: `python --version` or `python3 --version`

### "npm: command not found"
- Make sure Node.js is installed
- Check: `node --version` and `npm --version`

### Backend won't start
- Check if port 5000 is already in use
- Make sure all dependencies are installed: `pip install -r backend/requirements.txt`
- Try: `python -m pip install -r backend/requirements.txt`

### Frontend won't connect to backend
- Make sure backend is running first
- Check the API URL in the frontend (should be `http://localhost:5000`)
- Click "Test API Connection" button

### "Module not found" errors
- Reinstall dependencies:
  ```bash
  cd backend
  pip install -r requirements.txt
  cd ../frontend
  npm install
  ```

### Port already in use
- **Backend (5000):** Change port in `backend/app.py` (last line: `port=5000`)
- **Frontend (5173):** Vite will automatically use next available port

---

## Using the Built Executable (Windows)

If you see `backend/dist/web-scraper-backend.exe`, you can run it directly:

```bash
cd backend/dist
web-scraper-backend.exe
```

Or if you have the full Electron build in `dist-electron/win-unpacked/`:

```bash
cd dist-electron/win-unpacked
Web Scraper Pro.exe
```

---

## Next Steps

1. **Read the README.md** for detailed feature documentation
2. **Try scraping a website:**
   - Enter URL
   - Add selectors
   - Test selectors before scraping
   - Start scraping!

3. **Explore Advanced Features:**
   - JavaScript rendering (for dynamic sites)
   - Pagination (for multi-page scraping)
   - Proxy rotation
   - Rate limiting

---

## Need Help?

- Check the main **README.md** for detailed documentation
- Look at the error messages in the terminal
- Make sure all dependencies are installed correctly







