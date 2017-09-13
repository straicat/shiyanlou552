# -*- coding:utf-8 -*-
import sys, os, BaseHTTPServer, subprocess


class ServerException(Exception):
	pass


class base_case(object):
	def handle_file(self, handler, full_path):
		try: 
			with open(full_path) as f:
				content = f.read()
			handler.send_content(content)
		except IOError as ep:
			ep = "'%s' can't be read: %s" % (full_path, ep)
			handler.handle_err(ep)

	def index_path(self, handler):
		return os.path.join(handler.full_path, 'index.html')

	def test(self, handler):
		assert False, 'Not implemented.'

	def act(self, handler):
		assert False, 'Not implemented.'


class case_no_file(base_case):
	def test(self, handler):
		return not os.path.exists(handler.full_path)

	def act(self, handler):
		return ServerException("'%s' not found" % handler.path)


class case_cgi_file(base_case):
	def test(self, handler):
		return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')

	def act(self, handler):
		handler.run_cgi(handler.full_path)


class case_existing_file(base_case):
	def test(self, handler):
		return os.path.isfile(handler.full_path)

	def act(self, handler):
		handler.handle_file(handler.full_path)


class case_always_fail(base_case):
	def test(self, handler):
		return True

	def act(self, handler):
		raise ServerException("Unknown object '%s'" % handler.path)


class case_directory_index_file(base_case):
	def test(self, handler):
		return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))

	def act(self, handler):
		handler.handle_file(self.index_path(handler))


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	err_page = '''
<html>
<body>
<h1>Error access: {path}</h1>
<p>{msg}</p>
</body>
</html>
	'''
	cases = [
		case_no_file(),
		case_cgi_file(),
		case_existing_file(),
		case_directory_index_file(),
		case_always_fail(),
	]

	def do_GET(self):
		try:
			self.full_path = os.getcwd() + self.path
			for case in self.cases:
				if case.test(self):
					case.act(self)
					break
		except Exception as ep:
			self.handle_err(ep)

	def run_cgi(self, full_path):
		data = subprocess.check_output(['python', self.full_path])
		self.send_content(data)

	def handle_file(self, full_path):
		try:
			with open(full_path) as f:
				content = f.read()
			self.send_content(content)
		except IOError as ep:
			ep = "'%s' can't be read: %s" % (self.path, ep)
			self.handle_err(ep)

	def handle_err(self, msg):
		content = self.err_page.format(path=self.path, msg=msg)
		self.send_content(content, 404)

	def create_page(self):
		value = {
			'date_time': self.date_time_string(),
			'client_host': self.client_address[0],
			'client_port': self.client_address[1],
			'command': self.command,
			'path': self.path
		}
		return self.page.format(**value)

	def send_content(self, page, status=200):
		self.send_response(status)
		self.send_header('Content-Type', 'text/html')
		self.send_header('Content-Length', str(len(page)))
		self.end_headers()
		self.wfile.write(page)


if __name__ == '__main__':
	addr = ('', 8080)
	server = BaseHTTPServer.HTTPServer(addr, RequestHandler)
	server.serve_forever()
