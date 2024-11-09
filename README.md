# Running
Can be run from docker or directly.

## Docker
Build the image from project root:

```commandline
docker build -t fetchimage .
```

Run the container:
```commandline
docker run -d --name fetchcontainer -p 80:80 fetchimage
```

Access the api at `127.0.0.1:80`. To have a web interactable 
version go to `/docs` to see api and be able to send request through a GUI.

## Command Line
Run these preferably in a python venv.

Install the requirements:
```commandline
pip install -r requirements.txt
```

Run the app:
```commandline
fastapi run ./app/main.py --port 80
```

Access the api at `0.0.0.0:80`.

# Comments
Receipt points are stored in a dictionary along with the UUID generated at process time. This is the only mapping
of the UUID to the receipts. UUID collisions are not handled.

API endpoints are in app/receipts. Items contains the item class and tests.

Does not support offset-aware times for purchaseTime on receipts (time zone based timestamp). Should not be 
hard to extend support (construct the 2pm and 4pm times in timezone supplied with purchase date).
