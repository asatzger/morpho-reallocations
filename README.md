This code creates a simple Dash dashboard written in Python that analyzes public reallocations by MetaMorpho vault owners/operators.

Please follow the below steps to host the dashboard locally (requires `python` and `pip`):

1. Clone repository
```
git clone https://github.com/asatzger/morpho-reallocations.git
cd morpho-reallocations
```

2. Copy raw data CSV file into project directory
```
cp <CSV file location> .
```

4. Activate venv virtual environment<br>

  On Linux and Mac:
```
python3 -m venv venv
```
  On Mac:
```
python -m venv venv
```

6. Install requirements from requirements.txt file
```
pip install -r requirements.txt
```

8. Run Dash application (by default uses port 8050)
```
python3 app.py
```
