# Fix Virtual Environment - Pandas/NumPy Compatibility

If you're still getting the pandas/numpy compatibility error in your virtual environment, follow these steps:

## Quick Fix

1. **Activate your virtual environment:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. **Uninstall and reinstall pandas and numpy:**
   ```powershell
   pip uninstall -y pandas numpy
   pip install "numpy>=1.24.0,<2.0.0" "pandas>=2.1.0,<3.0.0" --no-cache-dir
   ```

3. **Verify the installation:**
   ```powershell
   python -c "import pandas as pd; import numpy as np; print(f'pandas: {pd.__version__}'); print(f'numpy: {np.__version__}')"
   ```

4. **Test the scraper:**
   ```powershell
   cd backend
   python -c "from scraper import WebScraper; print('Success!')"
   ```

## Alternative: Reinstall All Dependencies

If the above doesn't work, reinstall all dependencies:

```powershell
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt --force-reinstall --no-cache-dir
```

## If Still Having Issues

Try clearing Python cache and reinstalling:

```powershell
.venv\Scripts\Activate.ps1
# Remove __pycache__ directories
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse

# Reinstall packages
pip uninstall -y pandas numpy
pip install "numpy==1.26.4" "pandas==2.3.3" --no-cache-dir
```

## Verify It Works

```powershell
cd backend
python app.py
```

You should see:
```
==================================================
Enhanced Web Scraper API Server v2.0
==================================================
API running at: http://localhost:5000
```

