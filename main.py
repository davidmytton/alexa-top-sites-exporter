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
import json
import sys
from collections import Iterable

# 3rd party
import boto3
import requests

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument('--results',
                    help='How many results to export.',
                    required=True)
parser.add_argument('--ats_api_key',
                    help='Alexa ATS API Key from https://ats.alexa.com',
                    required=True)
parser.add_argument('--awis_api_key',
                    help='Alexa AWIS Key from https://awis.alexa.com',)
parser.add_argument('--country',
                    help='Filter top sites by 2-letter country code e.g. US.')
parser.add_argument('--start',
                    help='Result to start from.')
parser.add_argument('--test',
                    help='If specified, the Alexa API will not be called and the \
                          example-*.json files will be used instead.')
args = parser.parse_args()

fieldnames = ['URL', 'Global rank', 'Reach per million', 'Page views per million']

if args.awis_api_key:
    fieldnames.append('Online since')
    fieldnames.append('Adult')
    fieldnames.append('Category 1')
    fieldnames.append('Category 2')
    fieldnames.append('Top country')
    fieldnames.append('Top country rank')
    fieldnames.append('UK rank')
    fieldnames.append('US rank')
    fieldnames.append('Description')


def query_alexa_ats(results, start=1):
    # Set up the query URL
    canonical_querystring = 'Action=TopSites'
    if args.country:
        canonical_querystring += '&' + 'CountryCode=' + args.country
    canonical_querystring += '&' + 'ResponseGroup=Country'
    canonical_querystring += '&Start=' + str(start)

    if int(results) > 100:
        count = 100
    else:
        count = results

    canonical_querystring += '&Count=' + str(count) + '&Output=json'

    canonical_uri = '/api'
    request_url = 'https://ats.api.alexa.com' + canonical_uri + '?' + canonical_querystring

    headers = {'x-api-key': args.ats_api_key}

    # The Alexa API is paid per result so we want a cheap way to test things
    if not args.test:
        print('Request: ' + request_url, end='', flush=True)
        r = requests.get(request_url, headers=headers)
        print(' (status: ' + str(r.status_code) + ')')
        response = r.json()
    else:
        print('Dummy Request: ' + request_url)
        with open('example-ats.json', 'r') as json_file:
            response = json.load(json_file)

    return response


def query_alexa_awis(url):
    # Set up the query URL
    canonical_querystring = 'Action=UrlInfo&Output=json'
    canonical_querystring += '&ResponseGroup=AdultContent,SiteData,Categories,RankByCountry'
    canonical_querystring += '&Url=' + url

    canonical_uri = '/api'
    request_url = 'https://awis.api.alexa.com' + canonical_uri + '?' + canonical_querystring

    headers = {'x-api-key': args.awis_api_key}

    # The Alexa API is paid per result so we want a cheap way to test things
    if not args.test:
        r = requests.get(request_url, headers=headers)
        print(' (status: ' + str(r.status_code) + ')')
        response = r.json()
    else:
        print('Dummy Request: ' + request_url)
        with open('example-awis.json', 'r') as json_file:
            response = json.load(json_file)

    return response['Awis']['Results']['Result']['Alexa']


def write_csv(sites, writer):
    print('Looping through sites...')

    total = 0
    # Loop through the results
    for site in sites['Ats']['Results']['Result']['Alexa']['TopSites']['Country']['Sites']['Site']:
        csv_line = {}
        csv_line['URL'] = site['DataUrl']
        csv_line['Global rank'] = site['Global']['Rank']
        csv_line['Reach per million'] = site['Country']['Reach']['PerMillion']
        csv_line['Page views per million'] = site['Country']['PageViews']['PerMillion']

        if args.awis_api_key:
            print('Querying AWIS: ' + site['DataUrl'], end='', flush=True)

            awis = query_alexa_awis(site['DataUrl'])

            if 'ContentData' in awis:
                if 'OnlineSince' in awis['ContentData']['SiteData']:
                    csv_line['Online since'] = awis['ContentData']['SiteData']['OnlineSince']

                if 'AdultContent' in awis['ContentData']:
                    csv_line['Adult'] = awis['ContentData']['AdultContent']

            if 'Categories' in awis['Related'] and 'CategoryData' in awis['Related']['Categories']:
                if isinstance(awis['Related']['Categories']['CategoryData'], list):
                    if 'Title' in awis['Related']['Categories']['CategoryData'][0]:
                        csv_line['Category 1'] = awis['Related']['Categories']['CategoryData'][0]['Title']
                    if 'Title' in awis['Related']['Categories']['CategoryData'][1]:
                        csv_line['Category 2'] = awis['Related']['Categories']['CategoryData'][1]['Title']
                elif isinstance(awis['Related']['Categories']['CategoryData'], dict):
                    csv_line['Category 1'] = awis['Related']['Categories']['CategoryData']['Title']

            # We want to know how this site ranks in the UK and US
            # and also which country it has the highest rank in
            if 'RankByCountry' in awis['TrafficData'] and awis['TrafficData']['RankByCountry'] is not None:
                if isinstance(awis['TrafficData']['RankByCountry']['Country'], Iterable):
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
                else:
                    csv_line['Top country'] = awis['TrafficData']['RankByCountry']['Country']['@Code']
                    csv_line['Top country rank'] = awis['TrafficData']['RankByCountry']['Country']['Rank']

            # Sometimes a site will be #1 in lots of markets and in that case, the loop
            # will put the last country as the top country, but we want to override that
            if 'US rank' in csv_line and \
                csv_line['US rank'] == csv_line['Top country rank']:
                csv_line['Top country'] = 'US'

            if 'Description' in awis['ContentData']['SiteData']:
                csv_line['Description'] = awis['ContentData']['SiteData']['Description']

        writer.writerow(csv_line)

        # Total up returned results so we can page through them
        total = total + 1

    return total


# Calculate the cost of this query
cost = int(args.results) * 0.0025

if args.awis_api_key:
    cost = cost + (int(args.results) / 10) * 0.036

cost = round(cost, 2)

if not args.test:
    print('Querying %d results from Alexa will cost $%s, would you like to continue (y/n)?' % (int(args.results), str(cost)))

    # Give the user a chance to quit
    yes = {'yes', 'y'}
    no = {'no', 'n', ''}

    choice = input().lower()
    if choice in yes:
        pass
    elif choice in no:
        exit('Quit')
    else:
        sys.stdout.write('Would you like to continue?')
else:
    print('TEST MODE. Querying %d results from Alexa would cost $%s, would you like to continue (y/n)?' % (int(args.results), str(cost)))

with open('top-sites.csv', 'a') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Normally start at 1 but if we need to resume, no point re-querying results
    if not args.start:
        start = 1
        total = 0
        writer.writeheader()
    else:
        start = args.start
        total = int(start)
        
    response = query_alexa_ats(args.results, start)
    total = total + write_csv(response, writer)

    # If the total results returned is less than the number we want
    # then we need to make repeated requests to the Alexa API, incrementing
    # the start result each time
    while total < int(args.results):
        start = total + 1
        response = query_alexa_ats(args.results, start)
        total = total + write_csv(response, writer)

print('Finished. Output: top-sites.csv')
