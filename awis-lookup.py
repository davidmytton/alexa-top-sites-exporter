# Alexa Top Sites Exporter
#
# This exports sites from the Alexa Top Sites API into CSV format.
#
# Copyright (c) 2020 David Mytton <david@davidmytton.co.uk>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# System
import argparse
import csv
from collections.abc import Iterable

# 3rd party
import boto3
import requests

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument('--awis_api_key',
                    help='Alexa AWIS Key from https://awis.alexa.com',
                    required=True)
args = parser.parse_args()

fieldnames = ['URL', 'Top country', 'Top country rank', 'UK rank', 'US rank']


def query_alexa_awis(url):
    # Set up the query URL
    canonical_querystring = 'Action=UrlInfo&Output=json'
    canonical_querystring += '&ResponseGroup=AdultContent,SiteData,Categories,RankByCountry'
    canonical_querystring += '&Url=' + url

    canonical_uri = '/api'
    request_url = 'https://awis.api.alexa.com' + canonical_uri + '?' + canonical_querystring

    headers = {'x-api-key': args.awis_api_key}

    # The Alexa API is paid per result so we want a cheap way to test things
    r = requests.get(request_url, headers=headers)
    print(' (status: ' + str(r.status_code) + ')')
    response = r.json()

    return response['Awis']['Results']['Result']['Alexa']

with open('awis-input.csv') as csvfile:
    csvreader = csv.reader(csvfile)

    with open('awis-results.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in csvreader:
            url = row[0]
            print(url, end='', flush=True)

            csv_line = {}
            csv_line['URL'] = url

            awis = query_alexa_awis(url)

            if 'RankByCountry' in awis['TrafficData'] and awis['TrafficData']['RankByCountry'] is not None:
                try:
                    for country in awis['TrafficData']['RankByCountry']['Country']:
                        # UK and US
                        if country['@Code'] == 'GB':
                            csv_line['UK rank'] = country['Rank']
                        elif country['@Code'] == 'US':
                            csv_line['US rank'] = country['Rank']

                        # Which country it has the top rank in
                        if 'Top country' not in csv_line \
                            and country['Rank'] is not None:
                            csv_line['Top country'] = country['@Code']
                            csv_line['Top country rank'] = country['Rank']
                        elif country['Rank'] \
                            and 'Rank' in country \
                            and country['Rank'] is not None \
                            and int(country['Rank']) < int(csv_line['Top country rank']):
                            csv_line['Top country'] = country['@Code']
                            csv_line['Top country rank'] = country['Rank']
                except TypeError:
                    csv_line['Top country'] = awis['TrafficData']['RankByCountry']['Country']['@Code']
                    csv_line['Top country rank'] = awis['TrafficData']['RankByCountry']['Country']['Rank']

            # Sometimes a site will be #1 in lots of markets and in that case, the loop
            # will put the last country as the top country, but we want to override that
            if 'US rank' in csv_line and \
                csv_line['US rank'] == csv_line['Top country rank']:
                csv_line['Top country'] = 'US'

            writer.writerow(csv_line)

        