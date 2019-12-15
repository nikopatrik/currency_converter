# Currency converter
Kiwi.com - Python developer task

## Dependencies
  All python dependencies are written in requirements.txt file. This requierements are installed when you ran docker compose.
  To run docker-compose you must have installed docker and docker-compose utilities on your machine.
  
## Installation
For application to be fully functional you need to be running docker-compose.
To install application go as follows:
```bash
$ git clone https://github.com/nikopatrik/currency_converter.git
$ cd currency_converter
$ docker-compose up --build
```

Now should API should be running, you can try this by typing this in your browser:
```
http://localhost:5000/?amount=0.9&input_currency=%C2%A5&output_currency=AUD
```

CLI depends on Redis which is running in docker container. For application to be fully functional please run:
> If you won't run docker-compose, CLI will be functional but only for few currencies which are provided by European Bank
```bash
$ docker-compose up
```
### Running without docker 
*(Not recommended)* To use application without docker you have to create virtual enviroment and install requirements.
To do so, type in console in root directory of this project following commands:
```bash
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```
Now, when we have everything installed to run our application, we can then run app by calling CLI:
```bash
./currency_converter.py --amount 100.0 --input_currency EUR --output_currency CZK
{   
    "input": {
        "amount": 100.0,
        "currency": "EUR"
    },
    "output": {
        "CZK": 2707.36, 
    }
}
```
To run Flask application: 
```bash
$ export FLASK_APP=app.py
$ export FLASK_RUN_HOST=0.0.0.0
$ flask run
```
## Parameters
- `amount` - amount which we want to convert - float
- `input_currency` - input currency - 3 letters name or currency symbol
- `output_currency` - requested/output currency - 3 letters name or currency symbol


