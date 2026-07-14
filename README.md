### setup in mac locally
python3 -m venv venv <br />
source venv/bin/activate <br />
pip3 install -r requirements.txt <br />

### setup in server
python3 -m ensurepip --upgrade <br />
pip3 install -r requirements.txt <br />

### run tests
source venv/bin/activate <br />
pytest tests/test_tools.py <br />
pytest tests/test_tools.py -v <br />

### generate Kaggle submission (runs agent on test.csv)
source venv/bin/activate <br />
python scripts/generate_submission.py <br />

### everytime update packages in local
pip3 freeze > requirements.txt