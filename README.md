A simple bot that will monitor any web page for changes and post a status update on a Mastodon instance when changes are detected.

To run it, install the requirements:

```sh
pip install requirements.txt
```

Then create a config file from the example and edit with your data:

```sh
cp config.example.yml config.yml
```

And run:

```sh
chmod a+x ./main.py
./main.py
```