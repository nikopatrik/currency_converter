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
