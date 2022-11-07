A simple bot that will monitor Twitter ToS page for changes and tweet when there's one.

To run it, install the requirements:

```sh
pip install requirements.txt
```

Set Twitter access data via environment variables:

```sh
export TOSBOT_CONSUMER_KEY=your consumer key here
export TOSBOT_CONSUMER_SECRET=your consumer secret here
export TOSBOT_ACCESS_TOKEN=your access token here
export TOSBOT_ACCESS_TOKEN_SECRET=your access token secret here
```

Set the Github personal access token (make sure it can create gists):

```sh
export TOSBOT_GITHUB_TOKEN=your personal access token here
```

And run:

```sh
chmod a+x ./main.py
./main.py
```