# Black Widow - Blackbox Data-driven Web Scanning

## Running Black Widow

单独环境
python -m venv env
.\env\Scripts\activate

pip install --no-cache-dir -r requirements.txt

1. Add chromedriver to your path

Example for current directory on linux:

PATH=$PATH:.

2. Run the scanner

python3 crawl.py --url http://example.com


