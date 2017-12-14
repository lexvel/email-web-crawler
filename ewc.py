import re
import argparse
from collections import deque
from urllib.parse import urlsplit

import requests
import validators
from bs4 import BeautifulSoup, SoupStrainer


def check_url(value):
    """
    Simple url validator for command line arguments
    """
    if validators.url(value):
        return value
    else:
        msg = "%s is not a valid url" % value
        raise argparse.ArgumentTypeError(msg)


def parse_emails(text):
    '''
    Returns list of emaillike strings
    '''
    regex = r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]{2,4}"
    return re.findall(regex, text, re.I)


def find_emails(starting_url, depth=0):
    '''
    Returns set of unique emails, found in starting url
    and all included urls
    '''
    # Queue of urls to be crawled
    unprocessed_urls = deque([starting_url])
    # Queue for collecting urls from visited links
    collected_urls = deque()
    # Set of already crawled urls
    processed_urls = set()
    # Set of fetched emails
    emails = set()

    while True:
        while len(unprocessed_urls):
            # Move next url from the queue to the set of processed urls
            url = unprocessed_urls.popleft()
            processed_urls.add(url)

            # Extract base url to resolve relative links
            parts = urlsplit(url)
            base_url = "{0.scheme}://{0.netloc}".format(parts)

            # Get url's content
            print("Crawling URL %s" % url)
            try:
                response = requests.get(url)
            except (requests.exceptions.MissingSchema,
                    requests.exceptions.InvalidSchema,
                    requests.exceptions.ConnectionError):
                continue

            # Extract all email addresses and add them into the resulting set
            new_emails = set(parse_emails(response.text))
            emails.update(new_emails)

            # Parse document and extract all links
            soup = BeautifulSoup(response.text, 'html.parser',
                                 parse_only=SoupStrainer('a', href=True))

            for anchor in soup:
                link = anchor["href"]
                # Resolve relative links (starting with /)
                if link.startswith('/'):
                    link = base_url + link

                # Add new url to the collected
                if (link not in unprocessed_urls and
                        link not in processed_urls and
                        link not in collected_urls):
                    collected_urls.append(link)

        depth -= 1
        if depth >= 0:
            # Move collected urls to unprocessed
            # for crawling on the next level of depth
            unprocessed_urls = collected_urls.copy()
            collected_urls.clear()
        else:
            return emails


def main():
    parser = argparse.ArgumentParser(description='Email Web Crawler')
    parser.add_argument('url',
                        type=check_url,
                        help='Starting url for parsing emails from pages')
    parser.add_argument('-d', '--depth',
                        type=int,
                        choices=range(5),
                        default=0,
                        help='How deep should it parse pages')
    args = parser.parse_args()

    emails = find_emails(args.url, args.depth)
    if not emails:
        print('\nEmails not found')
    else:
        print('\nFound emails:\n')
        for email in emails:
            print(email)


if __name__ == '__main__':
    main()
