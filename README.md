# Alexa Top Sites Exporter

This code exports sites from the Alexa Top Sites API into CSV format.

## Requirements

macOS 10.15 with Python 3.7.6

## Setup

1. Extract the release zip file into a new directory. In a terminal, cd into that directory.
2. Execute: `python3 -m venv venv`. macOS may ask you to download the free developer tools from Apple. Allow this to run when prompted then run this command again.
3. Execute: `source venv/bin/activate`
4. Execute: `pip3 install -r requirements.txt`

## Usage

```
usage: main.py [-h] --results RESULTS --ats_api_key ATS_API_KEY
               [--awis_api_key AWIS_API_KEY] [--country COUNTRY]
               [--start START] [--test TEST]

optional arguments:
  -h, --help            show this help message and exit
  --results RESULTS     How many results to export.
  --ats_api_key ATS_API_KEY
                        Alexa ATS API Key from https://ats.alexa.com
  --awis_api_key AWIS_API_KEY
                        Alexa AWIS Key from https://awis.alexa.com
  --country COUNTRY     Filter top sites by 2-letter country code e.g. US.
  --start START         Result to start from.
  --test TEST           If specified, the Alexa API will not be called and the
                        example-*.json files will be used instead.
```

### Alexa Top Sites API (required)

1. Setup an AWS IAM user by [following the instructions here](https://aws.amazon.com/alexa-top-sites/getting-started/).
2. [Subscribe to Alexa Top Sites from the AWS Marketplace](https://aws.amazon.com/marketplace/pp/B07QK2XWNV). This will provide you with an API key from the [ATS dashboard](https://ats.alexa.com).

### Alexa URL Info API (optional)

If you want to query the URL Info API at the same time, you will need to generate a separate API. [Subscribe to Alexa URL Info from the AWS Marketplace](https://aws.amazon.com/marketplace/pp/B07Q71HJ3H). This will provide you with an API key from the [AWIS dashboard](https://awis.alexa.com).

### Resuming

If the script fails, you can use `--start` to resume from the last `TopSites` query. The position last queried will be in the request query string output to the console. E.g. 

`Request: https://ats.api.alexa.com/api?Action=TopSites&ResponseGroup=Country&Start=1&Count=5&Output=json`

means the API was queried for 5 results starting at result 1. If you wanted to query another set of results starting from the next result, you would add the argument `--start 6`.
