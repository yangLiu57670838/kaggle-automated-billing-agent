### setup in mac locally
python3 -m venv venv <br />
source venv/bin/activate <br />
pip3 install -r requirements.txt <br />

### setup in server
python3 -m ensurepip --upgrade <br />
pip3 install -r requirements.txt <br />

### everytime update packages in local
pip3 freeze > requirements.txt