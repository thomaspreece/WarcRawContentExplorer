# WarcRawContentExplorer

This python script starts up a server on localhost:8000 which allows you to upload arc/warc files and browse the files in this folder. The interface doesn't try to reconstruct the websites inside the (W)ARCs. It's use is for exploring the exact records of the (W)ARC file, the metadata attached to them and their raw content.

## Requirements
You'll need a python install (Python 2.7 only). Then you'll need the warcio library:
```
pip install warcio
```

## Starting server
Just run the following:
```
python WarcRawContentExplorer
```
The python script should open a web page with a file listing on. If not navigate to `localhost:8000`
