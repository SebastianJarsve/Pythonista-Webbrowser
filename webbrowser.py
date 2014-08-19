# coding: utf-8

import ui, json, pickle, urlparse, console, os

class BrowserView (ui.View):
	
	def get_title(self):
		return self['webview'].evaluate_javascript('document.title')
		
	def get_url(self):
		return self['webview'].evaluate_javascript('window.location.href')
		
	def parse_url(self, url):
		#return '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse.urlparse(url))
		return urlparse.urlparse(url).netloc
		
	def set_url(self, url=None):
		if url is None:
			url = self.get_url()
		if self.addressbar_is_editing:
			self['controlpanel']['addressbar'].text = url
			self['controlpanel']['addressbar'].alignment = ui.ALIGN_LEFT
		else: 
			self['controlpanel']['addressbar'].text = self.parse_url(url)
			self['controlpanel']['addressbar'].alignment = ui.ALIGN_CENTER
		
	def load_url(self, url):
		if '.' not in url:
			url = 'http://www.google.com/search?q={}'.format(url.replace(' ', '+'))
		elif urlparse.urlparse(url).netloc == '': #not url.startswith('http'):
			url = 'http://'+url
		self['webview'].load_url(url)
		
	def load_bookmarks(self):
		try:
			with open('bookmarks.json', 'r+') as f:
				bookmarks = json.load(f)
		except Exception as e:
			with open('bookmarks.json', 'w+') as f:
				bookmarks = {}
				json.dump(bookmarks, f, indent=4)
		return bookmarks
		
	def load_history(self):
		try:
			with open('history.txt', 'r+') as f:
				history = pickle.load(f)
		except Exception as e:
			with open('history.txt', 'w+') as f:
				history = []
				pickle.dump(history, f)
		return history
		
	def init_buttons(self):
		# Set 'BrowserView.button_tapped' as the action for all the controlpanel's subviews'
		for subview in self['controlpanel'].subviews:
			subview.action = self.button_tapped
		
	def init_addressbar(self):
		addressbar = self['controlpanel']['addressbar']
		addressbar.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
		addressbar.keyboard_type = ui.KEYBOARD_WEB_SEARCH
		addressbar.clear_button_mode = 'while_editing'
		addressbar.font = ('<system>', addressbar.height*0.4)
		addressbar.delegate = self
		addressbar.action = None
		
	def init_webbrowser(self):
		web = self['webview']
		web.load_url('https://omz-forums.appspot.com/pythonista')
		web.delegate = self
	
	def did_load(self):
		self.init_buttons()
		self.init_webbrowser()
		self.init_addressbar()
		self.bookmarks = self.load_bookmarks()
		self.history = self.load_history()
		self.addressbar_is_editing = False 
		self.webpage_has_loaded = False 
		self.favourite_images = {True :ui.Image.named('ionicons-ios7-star-32'),
		                         False:ui.Image.named('ionicons-ios7-star-outline-32')}
		
	def save_history(self):
		with open('history.txt', 'w') as f:
			url = self.get_url()
			if url in self.history:
				self.history.remove(url)
			self.history.append(url)
			f.seek(0)
			pickle.dump(self.history, f)
		
	def save_bookmark(self):
		with open('bookmarks.json', 'w') as f:
			title = self.get_title()
			url = self.get_url()
			if title == '':
				title = self.parse_url(url)
			self.bookmarks[title] = url
			f.seek(0)
			json.dump(self.bookmarks, f, indent=4)
			self['controlpanel']['favourite'].image = self.favourite_images[True]
			
	def remove_bookmark(self, title=None):
		with open('bookmarks.json', 'w') as f:
			if title is None:
				title = self.get_title()
			del self.bookmarks[title]
			f.seek(0)
			json.dump(self.bookmarks, f, indent=4)
			self['controlpanel']['favourite'].image = self.favourite_images[False]
			
	def popup_menu(self):
		popup = ui.View(name='menu', frame=(0, 0, 320, 500))
		toolbar = ui.View(frame=(-5, 0, 330, 100), name='toolbar')
		toolbar.border_width = 0.5
		toolbar.border_color = '#B2B2B2'
		label = ui.Label()
		label.text = 'Bookmarks'
		label.alignment = ui.ALIGN_CENTER
		label.frame = (0, 0, 320, 50)
		label.name = 'title'
		segment_ctrl = ui.SegmentedControl(name='segctrl')
		segment_ctrl.segments = ['Bookmarks', 'History']
		segment_ctrl.width = 170
		segment_ctrl.center = popup.center
		segment_ctrl.y = label.height
		segment_ctrl.selected_index = 0
		segment_ctrl.action = self.bookmarks_or_history
		toolbar.add_subview(label)
		toolbar.add_subview(segment_ctrl)
		popup.add_subview(toolbar)
		data_source = ui.ListDataSource(sorted(self.bookmarks.keys()))
		popup.add_subview(self.list_bookmarks_and_history(data_source, width=320, height=toolbar.superview.height-toolbar.height, y=toolbar.height, name='bookmarks'))
		
		x, y = self['controlpanel']['bookmarks'].center
		popup.present('popover', popover_location=(x, y), hide_title_bar=True)
		
	def bookmarks_or_history(self, sender):
		toolbar = sender.superview
		if sender.selected_index == 0:
			toolbar['title'].text = 'Bookmarks'
			data_source = ui.ListDataSource(sorted(self.bookmarks.keys()))
			tv = self.list_bookmarks_and_history(data_source, width=320, height=toolbar.superview.height-toolbar.height, y=toolbar.height, name='bookmarks')
			toolbar.superview.remove_subview(toolbar.superview['history'])
		else: 
			toolbar['title'].text = 'History'
			data_source = ui.ListDataSource(self.history[::-1])
			tv = self.list_bookmarks_and_history(data_source, width=320, height=toolbar.superview.height-toolbar.height, y=toolbar.height, name='history')
			toolbar.superview['bookmarks'].hidden=True
			toolbar.superview.remove_subview(toolbar.superview['bookmarks'])
		sender.superview.superview.add_subview(tv)
		
	def list_bookmarks_and_history(self, data_source, **kwargs):
		tv = ui.TableView()
		tv.data_source = data_source
		tv.delegate = self
		for k, v in kwargs.items():
			setattr(tv, k, v)
		return tv
		
	def show_more_menu(self):
		popup = ui.TableView()
		popup.width = 250
		popup.height = 500
		popup.name = 'More'
		popup.data_source = self
		popup.delegate = self
		button = self['controlpanel']['more']
		x = button.x
		y = button.y+button.height
		popup.present('popover', popover_location=(x, y))
		
	def button_tapped(self, sender):
		if sender.name == 'favourite':
			if self.get_url() in self.bookmarks.values():
				self.remove_bookmark()
			else: 
				self.save_bookmark()
		elif sender.name == 'bookmarks':
			self.popup_menu()
		elif sender.name == 'more':
			self.show_more_menu()
		else: 
			eval("self['webview'].{}()".format(sender.name))
			
			
	def tableview_number_of_rows(self, tableview, section):
		if tableview.name == 'Bookmarks':
			return len(self.bookmarks)
		elif tableview.name == 'More':
			return 1
		
	def tableview_cell_for_row(self, tableview, section, row):
		if tableview.name == 'Bookmarks':
			cell = ui.TableViewCell()
			cell.text_label.text = sorted(self.bookmarks.keys())[row]
			cell.image_view.image = ui.Image.named('ionicons-ios7-bookmarks-outline-32')
			cell.image_view.tint_color = '#66CCFF'
			return cell
			
		elif tableview.name == 'More':
			cell = ui.TableViewCell()
			cell.text_label.text = 'Settings'
			cell.image_view.image = ui.Image.named('ionicons-wrench-32')
			return cell
			
	@ui.in_background
	def tableview_did_select(self, tableview, section, row):
		if tableview.name == 'bookmarks':
			url = self.bookmarks[sorted(self.bookmarks.keys())[row]]
			self.load_url(url)
			tableview.superview.close()
		elif tableview.name == 'history':
			url = tableview.data_source.items[row]
			tableview.superview.close()
			self.load_url(url)
		elif tableview.name == 'More':
			tableview.close()
			console.hud_alert('No settings yet...', 'error', 1)
		
	def tableview_can_delete(self, tableview, section, row):
		return True 
		
	def tableview_delete(self, tableview, section, row):
		item = sorted(self.bookmarks.keys())[row]
		self.remove_bookmark(item)
		tableview.reload()
		
			
	def textfield_did_begin_editing(self, textfield):
		self.addressbar_is_editing = True
		self.set_url()
		self['controlpanel']['reload'].hidden = True
		
	def textfield_did_end_editing(self, textfield):
		self.addressbar_is_editing = False
		self['controlpanel']['reload'].hidden = False
		self.set_url()
		
	def textfield_should_return(self, textfield):
		url = self['controlpanel']['addressbar'].text
		self.load_url(url)
		textfield.end_editing()
		return True 
		
		
	def webview_did_start_load(self, webview):
		self.webpage_has_loaded = False 
		
	def webview_did_finish_load(self, webview):
		if not self.addressbar_is_editing:
			self.set_url()
			self.webpage_has_loaded = True 
			
		page_is_bookmarked = unicode(self.get_url()) in self.bookmarks.values()
		self['controlpanel']['favourite'].image = self.favourite_images[page_is_bookmarked]
		
		self.save_history()
			
view = 'ipad' if ui.get_screen_size()[0] >= 768 else 'iphone'
root_view = ui.load_view(view)
root_view.present(hide_title_bar=True)
