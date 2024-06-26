#!/usr/bin/python3
# encoding=utf8

import os, re, sys, subprocess
import configparser
import urllib.request as urllib
from bs4 import BeautifulSoup

# year in which first using, and version edit number
# version = 23.00

# ================== Settings ====================

config_dir = '.config'
config_name = 'arxiv.conf'
translate = {}
# Dictionary to map the placeholders in the filename style 
# to article metadata keys
translate['$title'] = "title"
translate['$authors'] = "authors"
translate['$doi'] = "doi"

textwidth = int(os.popen('stty size', 'r').read().split()[1])
style_std = "$title-$authors-$doi.pdf"

arguments = {}
arguments['-h, --help'] = 'Print help'
arguments['-v, --version'] = 'Print Version'
arguments['--config'] = 'Setup basic configuration in ~/{}/{}'.format(config_dir,config_name)

# ================================================

def config_write(dict, config_dir=config_dir, config_name=config_name):
  """
  Write ~/config_dir/config_name
  """
  config = configparser.ConfigParser()
  home = os.path.expanduser('~')
  config_folder = home + '/' + config_dir
  config_path = config_folder + '/' + config_name

  if not os.path.exists( config_folder ):
    print('Creating ~/{}'.format(config_dir))
    os.mkdir( config_folder )

  config['DEFAULT'] = dict

  with open( config_path, 'w') as configfile:
    config.write(configfile)

def config_read(config_dir=config_dir, config_name=config_name):
  """
  Read ~/config_dir/config_name
  """
  config = configparser.ConfigParser()
  home = os.path.expanduser('~')
  config_path = home + '/' + config_dir + '/' + config_name

  if os.path.exists( config_path ):
    config.read( config_path )
    return config['DEFAULT']

  else:
    return None

def setup(style=style_std):
  """
  Setup sites of interest from arxiv.org
  """

  req = urllib.Request("https://arxiv.org/",
                        headers={'User-Agent': 'Mozilla/5.0'})
  html = urllib.urlopen(req)
  soup = BeautifulSoup(html, "lxml")

  pages = soup.find_all("a", href=re.compile("/list/"))

  category_prev = ''
  links = []

  iii = 0
  for page in pages:

    category = page.parent.parent.previous_sibling.previous_sibling.get_text()

    # Print category once
    if not category == category_prev:
      print('\n' + color.BOLD + '~ ~ ~ {}'.format(category.upper()) + color.END)
      category_prev = category

    # Search for previous words written in bold
    if page.previous_sibling.previous_sibling.name == 'b':
      tag = page.previous_sibling.previous_sibling.previous_sibling.previous_sibling.get_text()

      # For small categories, don't write them twice
      if not tag == category_prev:
        print('\n' + page.previous_sibling.previous_sibling.previous_sibling.previous_sibling.get_text())

    print('{:4}: '.format(iii) + page.get_text())
    links.append('https://arxiv.org' + page.get('href'))
    iii += 1

  # Get user input list
  while True:

    choice = input( '\n' + color.BOLD + 'Choose (2 12 ..): ' + color.END )

    try:
      choice = [ int(i) for i in choice.split() if int(i) <= iii ]
      if choice == []:
        print('Number(s) too high!')
      else: break

    except ValueError:
      print('Not a valid list: "{}"'.format(choice))
      pass

  print("All right! I got:")
  for c in choice:
    print(links[c])

  config = {}
  config['URL'] = ', '.join([ links[c] for c in choice ])
  config['STYLE'] = style
  config_write(config)

  print('Done!')
  return 0

class color:
  PURPLE = '\033[95m'
  CYAN = '\033[96m'
  DARKCYAN = '\033[36m'
  BLUE = '\033[94m'
  GREEN = '\033[92m'
  YELLOW = '\033[93m'
  RED = '\033[91m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  END = '\033[0m'

# ================== Config =====================

config = config_read()
if not config:
  print('No config found, generating now ...')
  setup()
  config = config_read()

else:
  if not 'URL' in config:
    print('No URL setup found in ~/.config/arxif.conf. Setting up now ...')
    setup( style=config['STYLE'] )
    config = config_read()

  if not 'STYLE' in config:
    print('No STYLE setup found in ~/.config/arxif.conf. Setting fallback: {}'.format(style_std))
    config['STYLE'] = style_std
    config_write(config)

urls = config['URL']
urls = [ i.strip() for i in urls.split(',') ]
style = config['STYLE']

# ================================================

if __name__ == "__main__":

  # =============== Argument parser=================

  if any([1 if arg in sys.argv else 0 for arg in ['-v', '--version']]):
    print(version)
    sys.exit(0)

  if any([1 if arg in sys.argv else 0 for arg in ['-h', '--help']]):

    name = os.path.basename(sys.argv[0])

    # Display help
    print("This is {program}. Get your daily arXiv-dose.\n".format(program=name))
    print("Usage: ./{program}".format(program=name))
    print("Currently I'm fetching", url, '\n')

    for key in arguments:
      print("\t{:15}: {}".format(key, arguments[key]))

    sys.exit(0)

  if any([1 if arg in sys.argv else 0 for arg in ['--config']]):

    setup()
    sys.exit(0)

  # ================================================

  # ============ Generate and fetch url ============


  articles = {}
  iii = 0

  for url in urls:

    try:
      req = urllib.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
      html = urllib.urlopen(req)

    except urllib.HTTPError:
      print(url)
      print('"{}" not found. Correct spelling?'.format(search))
      sys.exit(0)

    # ================================================

    # ================= Find papers ==================

    soup = BeautifulSoup(html, "lxml")

    # Get DOI and URL
    papers = soup.find_all("dt")

    for c, nnn in zip( papers, range( iii, iii+len(papers) ) ):

      articles[nnn] = {}

      doi = c.find_all("a", title="Abstract")[0]
      doi = doi.get_text()
      articles[nnn]["doi"] = doi

      try:
        link = c.find_all("a", title="Download PDF")[0].get('href')
      except IndexError:
        link = c.find("a", title="Download PDF")
        if link: link = link.get('href')

      if link:
        articles[nnn]["url"] = 'https://arxiv.org' + link

    # Get Title, Authors and Abstract
    meta = soup.find_all("div", class_="meta")

    for c, nnn in zip(meta, range( iii, iii+len(meta) )):

      title = c.find("div", class_="list-title")
      title = title.get_text().replace('Title: ','').strip()

      # Replace multiple consecutive occurrences of " " with " "
      title = re.sub(r'(\ )\1+', r' ', title)

      articles[nnn]["title"] = title

      authors = c.find("div", class_="list-authors")

      # Find authors with hyperlinks
      authors = [ a.get_text().strip() for a in  authors.find_all('a') ]

      # Remove name abbreviations: John J.J. Doe |--> John Doe
      authors = [ re.sub('[a-zA-Z]+\.','',a).strip() for a in authors ]

      # Take last name: John Doe |--> Doe
      authors = [ a.split()[-1] if len( a.split() ) > 1 else a for a in authors ]
      authors = ','.join(authors)

      articles[nnn]["authors"] = authors

      try:
        abstract = c.find("p", class_="mathjax").get_text().replace('\n',' ')
      except AttributeError:
        abstract = None

      articles[nnn]["abstract"] = abstract

    iii += len(meta)

  # List findings
  for paper in articles.keys():

    print( '\n' + color.BOLD + color.UNDERLINE +'{:5}'.format(paper) + color.END,
           articles[paper]["title"])
    print( 6 * ' ' + articles[paper]["authors"], '\n' )
    if articles[paper]["abstract"]:
      print( ' ' + articles[paper]["abstract"] )

  # Get user input list
  while True:

    download = input( '\n' + color.BOLD + 'Download (2 12 ..): ' + color.END )

    try:
      download = [ int(i) for i in download.split() if int(i) <= len(articles.keys()) - 1]
      if download == []:
        print('Number(s) too high!')
      else: break

    except ValueError:
      print('Not a valid list: "{}"'.format(download))
      pass

  for file in download:

    url = articles[file]["url"]
    filename = '{}-{}-{}.pdf'.format(articles[file]["title"], articles[file]["authors"], articles[file]["doi"])

    # Take style and successively replace keys with values
    filename = style

    for key in translate:
      if key in style and not key == "$authors":
        filename = filename.replace(key, articles[file][translate[key]])

    # Generate length filename without authors
    baselength = len(filename) - len( "$authors" )

    # Get maximum file length supported by OS
    name_max = subprocess.check_output("getconf NAME_MAX /", shell=True).strip()
    name_max = int(name_max)

    if baselength > name_max:

      print( "Warning: Your filesystem supports filenames up to {} characters but title + doi are already longer.".format(name_max) )
      print( "Hence I choose the original url {}".format(url) )
      filename = ''

    else:

      # Fill in authors as long as baselength < name_max
      authors = ''
      breaking = 0

      for author in articles[file]["authors"].split(','):

        if not breaking:

          if baselength + len(author) + 1 < name_max:
            if authors == '': authors = author
            else: authors = ",".join( [authors, author] )
            baselength += len(author) + 1

          else:
            print('\n' + color.BOLD + str(file) + color.END + ' Warning: '
                  + 'Too many authors for |filename| <= {} (max. of your filesystem)'.format(name_max))
            print('\n' + ( int(textwidth/2) ) * '~ ')
            print('Truncating ...\n\n{}\n\nto ...\n\n{}'.format(articles[file]["authors"],authors))
            print( ( int(textwidth/2) ) * '~ ' )
            breaking = 1

      # Generate filename
      filename = filename.replace('$authors', authors)
      print('Saving: ', filename, '\n')

    # Download
    if filename == '':
      subprocess.call(["wget", '--quiet', '--show-progress', '--header', "User-Agent: Mozilla/5.0", url])

    else:
      subprocess.call(["wget", '--quiet', '--show-progress', '--header', "User-Agent: Mozilla/5.0", "--output-document", '{}'.format(filename), url])

  # ================================================
