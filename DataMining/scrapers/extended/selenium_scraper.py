from multiprocessing import Pool

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
import time
from collections import namedtuple, defaultdict


class PageData(namedtuple(
	'PageData',
	[
		'url',
		'author',
		'author_role',
		'entity',
		'vertical',
		'title',
		'views',
		'date',
		'text',
	]
)):
    def to_dict(self):
        return self._asdict()

    @classmethod
    def from_dict(cls, dictionary):
        return cls(**dictionary)


class DriverWrapper:
	def __init__(self, options=None, starting_link='https://www.smartkarma.com/insights'):
		self.options_list = options
		self.options = webdriver.ChromeOptions()
		self._driver = None
		self._starting_link = starting_link

	def create_driver(self):
		self._apply_options()
		self._driver = webdriver.Chrome(chrome_options=self.options)
		self._driver.get(self._starting_link)
		print('created driver', self._driver)

	def get_current_window(self):
		return self._driver.current_window_handle

	def _apply_options(self):
		for option in self.options_list:
			self.options.add_argument(option)

	def quit(self):
		if self._driver is not None:
			self._driver.quit()


class Scraper:
	def __init__(self, options=[], starting_link='https://www.smartkarma.com/insights', **settings):
		self.driver_wrapper = DriverWrapper(options, starting_link)
		self.driver_wrapper.create_driver()
		self._executor = Executor(self.driver_wrapper, self.return_driver_instance())
		self._data_processor = DataProcessor()
		self.settings = settings
		self.main_window = None
		self.scraped_websites = None
		self.stored_multiple_elements = defaultdict(list)
		self.stored_single_elements = defaultdict(list)
		self.timeouted_links = []

	def get_current_driver_window(self):
		self.main_window = self.driver_wrapper.get_current_window()
		print('driver', self.driver_wrapper)

	def open_new_tab(self, link):
		self._executor.open_and_switch_window(link=link)

	def close_new_tab(self):
		self._executor.close_and_return_main_window(main_window=self.main_window)

	def scroll_down(self, tag='body'):
		self._executor.scroll_down_page(self.settings['scroll_iterations'], tag=tag)

	def get_single_element(self, timeout, xpath, key=None, base_element=None, store_text=False):
		single_element = self._executor.wait_for_element_presence_and_get(
			timeout=timeout, 
			xpath=xpath, 
			base_element=base_element,
		)
		value_to_be_stored = single_element.text if store_text else single_element
		self.stored_single_elements[key].append(value_to_be_stored)
		return value_to_be_stored

	def get_single_element_to_resolve(self, timeout, xpath, key=None, base_element=None):
		element_to_resolve = self._executor.wait_for_element_presence_and_get(
			timeout=timeout, 
			xpath=xpath, 
			base_element=base_element,
		)
		resolved_elements = self._data_processor.convert_views_and_date(element_to_resolve=element_to_resolve.text)
		for name, element in resolved_elements.items():
			self.stored_single_elements[name].append(element)
		return resolved_elements.values()

	def get_multiple_elements(self, timeout, xpath, key=None, base_element=None):
		multiple_elements = self._executor.wait_for_all_elements_presence_and_get(
			timeout=timeout, 
			xpath=xpath,
			base_element=base_element,
		)
		self.stored_multiple_elements[key] = multiple_elements

	def return_driver_instance(self):
		return self.driver_wrapper._driver


class Executor:
	def __init__(self, driver_wrapper, chrome_driver):
		self.driver_wrapper = driver_wrapper
		self.chrome_driver = chrome_driver

	def open_and_switch_window(self, link):
		self.chrome_driver.execute_script("window.open('" + link + "', 'new_window')")
		self.chrome_driver.switch_to_window(self.chrome_driver.window_handles[-1])

	def close_and_return_main_window(self, main_window):
		self.chrome_driver.switch_to.window(main_window)

	def scroll_down_page(self, scroll_iterations, tag='body'):
		for scroll_iteration in range(scroll_iterations):
			self.chrome_driver.find_element_by_tag_name(tag).send_keys(Keys.END)
			time.sleep(1)

	def wait_for_all_elements_presence_and_get(self, timeout=5, xpath='//div', base_element=None):
		# print('scraping all elements', self.driver_wrapper)
		return WebDriverWait(base_element, timeout).until(
			EC.presence_of_all_elements_located((By.XPATH, xpath))
		)

	def wait_for_element_presence_and_get(self, timeout=5, xpath='//div', base_element=None):
		# print('scraping single element', self.driver_wrapper)
		return WebDriverWait(base_element, timeout).until(
			EC.presence_of_element_located((By.XPATH, xpath))
		)


class DataProcessor:
	def convert_views_and_date(self, element_to_resolve):
		views_and_date_separated = element_to_resolve.split(',')
		views = self.safe_casting(views_and_date_separated[0].split()[0], int, 0)
		date = views_and_date_separated[1]
		return {'views': views, 'date': date}

	def safe_casting(self, value, to_type, default=None):
	    try:
	        return to_type(value)
	    except (ValueError, TypeError):
	        return default

	def safe_json(self, value):
		with open('output_oop.json', 'w') as outfile:
			json.dump(value, outfile)


options = []#['--headless']
settings = {
	'primary_timeout': 5,
	'secondary_timeout': 2,
	'scroll_iterations': 2,
}
scraped_insights = []

scraper = Scraper(options=options, **settings)
scraper.get_current_driver_window()
scraper.get_multiple_elements(
	timeout=settings['primary_timeout'],
	xpath='//a[contains(@class, "sk-insight-snippet__headline")]',
	key='link',
	base_element=scraper.return_driver_instance(),
)

print(len(scraper.stored_multiple_elements['link']))

for index, webelement in enumerate(scraper.stored_multiple_elements['link']):
	link = webelement.get_attribute('href')
	print(link)

	try: 
		scraper.open_new_tab(link)

		"""AUTHOR"""
		author_section = scraper.get_single_element(
			timeout=settings['primary_timeout'],
			xpath='//div[contains(@class, "sk-insight-longform__compact-header__author")]',
			key='author_section',
			base_element=scraper.return_driver_instance(),
		)
		author = scraper.get_single_element(
			timeout=settings['secondary_timeout'],
			xpath='.//a[contains(@class, "item-snippet__text")]',
			key='author',
			base_element=author_section,
			store_text=True,
		)
		author_role = scraper.get_single_element(
			timeout=settings['secondary_timeout'],
			xpath='.//div[contains(@class, "item-snippet__text")]',
			key='author_role',
			base_element=author_section,
			store_text=True,
		)

		"""ENTITY"""
		entity_section = scraper.get_single_element(
			timeout=settings['primary_timeout'],
			xpath='//div[contains(@class, "sk-insight-longform__compact-header__entity")]',
			key='entity_section',
			base_element=scraper.return_driver_instance(),
		)
		entity = scraper.get_single_element(
			timeout=settings['secondary_timeout'],
			xpath='.//a[starts-with(@href, "/entities")]',
			key='entity',
			base_element=entity_section,
			store_text=True,
		)
		vertical = scraper.get_single_element(
			timeout=settings['secondary_timeout'],
			xpath='.//a[starts-with(@href, "/verticals")]',
			key='vertical',
			base_element=entity_section,
			store_text=True,
		)

		"""HEADLINE""" 
		headline_section = scraper.get_single_element(
			timeout=settings['primary_timeout'],
			xpath='//div[contains(@class, "sk-insight-longform__title-container")]',
			key='headline_section',
			base_element=scraper.return_driver_instance(),
		)
		title = scraper.get_single_element(
			timeout=settings['secondary_timeout'],
			xpath='.//h1[contains(@class, "insight-content__headline")]',
			key='title',
			base_element=headline_section,
			store_text=True,
		)
		views, date = scraper.get_single_element_to_resolve(
			timeout=settings['secondary_timeout'],
			xpath='.//div[contains(@class, "insight-content__meta +print-hidden")]',
			key='views_and_date',
			base_element=headline_section,
		)

		"""CONTENT"""
		content = scraper.get_single_element(
			timeout=settings['secondary_timeout'],
			xpath='//div[contains(@class, "insight-content__content")]',
			key='content',
			base_element=scraper.return_driver_instance(),
			store_text=True,
		) 
		print('FINAL', scraper.stored_single_elements['author'], scraper.stored_single_elements['date'])
		scraper.close_new_tab()

		data = PageData(
			url=link,
			author=author,
			author_role=author_role,
			entity=entity,
			vertical=vertical,
			title=title,
			views=views,
			date=date,
			text=content,
		)
		scraped_insights.append(data._asdict())

	except TimeoutException as ex:
		scraper.timeouted_links.append(index)
		print("[TIMEOUT]" + str(ex), 'cannot store #' + str(index) + 'insight. Continue iterating...')
		scraper.close_new_tab()
		continue

scraper.driver_wrapper.quit()

scraper._data_processor.safe_json(scraped_insights)

