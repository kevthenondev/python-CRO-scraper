# -*- coding: utf-8 -*-
"""
Simple crawler to collect company's address data.

@author: kdwalsh based on idwaker's linkedin scraper

Requirements:
    python-selenium
    python-click
    python-keyring
    lxml

Tested on Python 3 not sure how Python 2 behaves
"""

import sys
import csv
import time
import click
import getpass
import keyring
from selenium import webdriver
from selenium.common.exceptions import (WebDriverException, NoSuchElementException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import random
import lxml.html


CRO_URL = 'https://search.cro.ie/company/CompanySearch.aspx'

class UnknownUserException(Exception):
    pass


class UnknownBrowserException(Exception):
    pass


class WebBus:
    """
    context manager to handle webdriver part
    """

    def __init__(self, browser):
        self.browser = browser
        self.driver = None

    def __enter__(self):
        # XXX: This is not so elegant
        # should be written in better way
        if self.browser.lower() == 'firefox':
            self.driver = webdriver.Firefox()
        elif self.browser.lower() == 'chrome':
            self.driver = webdriver.Chrome()
        elif self.browser.lower() == 'phantomjs':
            self.driver = webdriver.PhantomJS()
        else:
            raise UnknownBrowserException("Unknown Browser")

        return self

    def __exit__(self, _type, value, traceback):
        if _type is OSError or _type is WebDriverException:
            click.echo("Please make sure you have this browser")
            return False
        if _type is UnknownBrowserException:
            click.echo("Please use either Firefox, PhantomJS or Chrome")
            return False
        print('__exit__, driver close')
        self.driver.close()

def collect_conames(filepath):
    """
    collect names from the file given
    """
    conames = []
    with open(filepath, 'r') as _file:
        # names = [line.strip() for line in _file.readlines()]
        conames = [line[:-1] for line in _file.readlines()]
    return conames
        

@click.group()
def cli():
    pass


@click.command()
@click.option('--browser', default='phantomjs', help='Browser to run with')
@click.argument('infile')
@click.argument('outfile')                        
def crawlcro(browser, infile, outfile):

    # first check and read the input file
    conames = collect_conames(infile)   #get company names from file - could make a single smarter file reader proc
    print(conames)
    
    fieldnames = ['Company name', 'Legal name','Address']
    # then check we can write the output file
    # we don't want to complete process and show error about not
    # able to write outputs
    with open(outfile, 'w', newline='') as csvfile:
        # just write headers now
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    
    # now open the browser

    with WebBus(browser) as bus:
        bus.driver.get(CRO_URL)
        print("Opening page")


        with open(outfile, 'a+', newline='') as csvfile:
            print('Starting writer')
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            for coname in conames:
                addresses = []
                print('link:',coname)
                
                conamefield = bus.driver.find_element_by_id('ctl00_ContentPlaceHolder1_textCompanyName')
                submit_form = bus.driver.find_element_by_class_name('search-site-button')

                conamefield.clear()
                conamefield.send_keys(coname)
                submit_form.click()
                click.echo("Searching company")

                #time.sleep(random.uniform(2, 2))

                resultsBlock = None
                results = None


    
                #get the results block
                try:                                        
##                    resultsBlock = bus.driver.find_element_by_id('ctl00_ContentPlaceHolder1_GridView1')
##                    print('Results Block: ', resultsBlock)


                    root = lxml.html.fromstring(bus.driver.page_source)
                    print("creating root")
                    for row in root.xpath('.//table[@id="ctl00_ContentPlaceHolder1_GridView1"]//tr'):
                        legalname = row.xpath('.//a/text()')
                        print(legalname)
                        cells = row.xpath('.//td/text()')
                        print(cells)
                        if cells != []:
                            print('Creating data entry')

                            data = {'Company name': coname, 'Legal name': legalname[0], 'Address': cells[1]}


                            #print('Data: ',data)
                            addresses.append(data)
                            #print(addresses)
                            writer.writerows(addresses)
                            click.echo("Obtained ..." + coname)

                except NoSuchElementException:
                    click.echo("No results")
                    continue

cli.add_command(crawlcro)

if __name__ == '__main__':
    cli()
