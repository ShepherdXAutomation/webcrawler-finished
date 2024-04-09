import anvil.tables as tables
from anvil.tables import app_tables
import anvil.tables.query as q
import anvil.server
import anvil.http
import anvil.tables
from datetime import datetime


@anvil.server.callable
def launch_one_crawler(sitemap_url):
  """Launch a single crawler background task."""
  task = anvil.server.launch_background_task('crawl', sitemap_url)
  return task


@anvil.server.background_task
def crawl(sitemap_url):
  """Crawl an XML sitemap, downloading all the pages it points to."""
  print('Crawling: ' + sitemap_url)

  # Request the sitemap
  response = anvil.http.request(sitemap_url)
  sitemap = response.get_bytes().decode("utf-8")

  # Parse the sitemap
  urls = []
  for line in sitemap.split('\n'):
    if '<loc>' in line:
      urls.append(line.split('<loc>')[1].split('</loc>')[0])
  
  # Only load the first 20 URLs for now, as Background Tasks will timeout after 30s for free users.
  # This restriction does not apply to users on paid plans.
  urls = urls[:20]
  
  get_pages(urls)
  

def get_pages(urls):
  """Request and store all the pages in a list of URLs."""
  anvil.server.task_state['total_urls'] = len(urls)
  for n, url in enumerate(urls):
    url = url.rstrip('/')

    # Get the page
    try:
      print("Requesting URL " + url)
      response = anvil.http.request(url)
      html = response.get_bytes().decode("utf-8")
    except:
      # If the fetch failed, just try the other URLs
      continue
      
    store_page(url, html)
    
    anvil.server.task_state['n_complete'] = n + 1


def store_page(url, html):
  # Find the Data Tables row, or add one
  with anvil.tables.Transaction() as txn:
    data = app_tables.pages.get(url=url) or app_tables.pages.add_row(url=url)
  
    # Update the data in the Data Tables
    data['html'] = html
    data['last_indexed'] = datetime.now()


@anvil.server.callable
def search(query):
  """Perform the search within the page contents."""
  pages = app_tables.pages.search(html=q.full_text_match(query))
  return [{"url": p['url']} for p in pages]


@anvil.server.callable
def kill_crawler(task):
  task.kill()


@anvil.server.callable
def get_existing_tasks():
  return [
    t for t in anvil.server.list_background_tasks() if t.get_task_name() == 'crawl'
  ]
