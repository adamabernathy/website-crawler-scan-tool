# website-crawler-scan-tool
Try to understand how my website looks to a bot/crawler

## Usage

```python does_my_website_require_js_to_run.py --help

usage: does_my_website_require_js_to_run [-h] [--website-url WEBSITE_TO_CHECK] [--output OUTPUT_FILENAME] [--verbose] [--quiet]

Is website bot friendly? I.e., does it need JavaScript to render

options:
  -h, --help            show this help message and exit
  --website-url, -u WEBSITE_TO_CHECK
                        Website to evaluate
  --output, -o OUTPUT_FILENAME
                        Save output of results
  --verbose, -v         Verbose output
  --quiet, -q           Runs quiet-er

🌮s are a way of life.
```

## Output

```
python does_my_website_require_js_to_run.py --website-url https://adamabernathy.com
```

Gives you something like:

<img width="634" alt="Screenshot 2025-06-10 at 1 37 23 PM" src="https://github.com/user-attachments/assets/9f16ccfc-8c59-4d50-8036-6f15e80de5f5" />


## Install

```sh
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
