from anvil import *
import anvil.tables as tables
from anvil.tables import app_tables
import anvil.server

class Form1(Form1Template):

  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run when the form opens.
    tasks = anvil.server.call('get_existing_tasks')
    if len(tasks) > 0:
      # Keep track of the latest task
      self.task = tasks[-1]
      # Turn on the progress display
      self.timer_1.interval = 0.5
      self.card_search.visible = True
      self.crawl_progress_panel.visible = True

  def button_run_click(self, **event_args):
    """This method is called when the button is clicked"""
    self.task = anvil.server.call('launch_one_crawler', self.text_box_sitemap.text)
    self.timer_1.interval = 0.5
    self.card_search.visible = True
    self.crawl_progress_panel.visible = True
    
  def timer_1_tick(self, **event_args):
    """This method is called Every [interval] seconds. Does not trigger if [interval] is 0."""
    with anvil.server.no_loading_indicator:
      # Show progress
      state = self.task.get_state()
      n_complete, total_urls = state.get('n_complete', 0), state.get('total_urls', 0)
      self.label_num_indexed.text = n_complete
      self.label_total_pages.text = total_urls
  
      # Switch Timer off if process is complete
      if not self.task.is_running():
        self.timer_1.interval = 0
      
  def button_search_click(self, **event_args):
    """This method is called when the button is clicked"""
    query = self.text_box_search.text
    self.repeating_panel_1.items = anvil.server.call('search', query)

  def button_stop_click(self, **event_args):
    """This method is called when the button is clicked"""
    anvil.server.call('kill_crawler', self.task)



