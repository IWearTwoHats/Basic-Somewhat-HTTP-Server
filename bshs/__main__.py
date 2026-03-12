#!/usr/bin/env python3

'''
Basic Somewhat HTTP Server (BSHS)

I'm just rewriting my old server.
'''

__version__ = '0.3.0'

import socket as s
from colorama import Fore, Back # For your convenience.
import os, sys, subprocess, json
from mimetypes import guess_type # Why did I do this manually before?
from thpath import Path # That's right, I made my own Path object.
from threading import Thread
from htmlificate import HTML
from typing import Any

from .changelog import CHANGELOG

# Codenames for HTTP status codes.
#STATUSCODES
HTTP_STATUS_CODES = {
	200: 'OK',
	201: 'Created',
	302: 'Found',
	303: 'See Other',
	400: 'Bad Request',
	403: 'Forbidden',
	404: 'Not Found',
	405: 'Method Not Allowed',
	408: 'Request Timeout',
	500: 'Internal Server Error',
	501: 'Not Implemented',
	505: 'HTTP Version Not Supported'
}

# Alternate paths to check when the requested resource does not exist.
# These must be relative paths.
#CHECKPATHS
CHECK_PATHS = [
	Path('index.html'),
	Path('index.htm'),
	Path('index.txt'),
	Path('index.py'),
	Path('index.sh')
]

# Files that will be executed and have their stdout redirected to the response body.
# The exit code will be the HTTP status code, or if the exit code is 0, the HTTP status code will be 200.
# The Content-Type header will ALWAYS be text/html.
#EXECPATHS
EXEC_NAMES = [
	Path('index.py'),
	Path('index.sh')
]
EXEC_MIMES = [
	'text/x-python',
	'text/x-sh'
]

# The paths that will be checked when a POST Request was recieved.
#POSTPATHS
POST_PATHS = [
	Path('post.py')
]

# By default, accept all connections.
#HOSTNAMES
# If hostnames are added to this list, only accept connections from those hostnames.
ALLOWED_HOSTNAMES = []

# What hostnames get routed where.
# All hostnames will get routed to * if that name was not found.
#ROUTING
WEBSITE_DIRS = {
	'*': Path(os.getcwd())
}

# Paths that will be captured for a URL.
CAPTURE_PATHS = {
	'*': [
		Path('server-capture-test')
	]
}

CAPTURE_SCRIPTS = [
	Path('capture.py'),
	Path('capture.sh')
]

# The builtin resources.
#BUILTINS
BUILTINS = {
	'builtins': Path(os.path.dirname(__file__)),
	'server': Path(os.path.dirname(__file__)),
	'server-capture-test': Path(os.path.dirname(__file__))
}

# By default, use port 8080 and run on all addresses.
PORT = 8080
ADDR = '0.0.0.0'

# Other config.
#MISCCONFIG

# If false, do not accept POST requests.
ACCEPT_POST = True

# When accessing the resource for a directory, 303 redirect to that same location, but with a slash at the end.
ADD_SLASH_TO_DIR = True

# If true, when a directory is requested, send a directory index.
CONSTRUCT_INDEX = True

# Exceptions.
#EXCEPTIONS
class HTTP2xx(BaseException):...
class HTTP3xx(BaseException):...
class HTTP4xx(BaseException):...
class HTTP5xx(BaseException):...

class OK(HTTP2xx):...
class Created(HTTP2xx):...
class Found(HTTP3xx):...
class SeeOther(HTTP3xx):...
class BadRequest(HTTP4xx):...
class Forbidden(HTTP4xx):...
class NotFound(HTTP4xx):...
class MethodNotAllowed(HTTP4xx):...
class RequestTimeout(HTTP4xx):...
class InternalServerError(HTTP5xx):...

EXCEPTIONS = {
	1: NotFound,
	2: Forbidden,
	3: SeeOther,
	4: MethodNotAllowed,
	5: InternalServerError,
	6: Created,
	7: Found
}

def index(path: Path, relpath: Path) -> str:
	h = HTML()
	h.start_tag('html', {'class': 'index'})
	h.start_tag('head', {'class': 'index'})
	h.link(
		{
			'rel': 'stylesheet',
			'href': '/style.css'
		}
	)
	h.link(
		{
			'rel': 'stylesheet',
			'href': '/index.css'
		}
	)
	h.end_tag()
	h.start_tag('body',{'class': 'index'})
	h.h1(f'Index of: /{relpath}/'.replace('//','/'))
	h.a('Back',{'class':'index','href':'..'})
	h.hr({'class':'index'})
	#MARKDOWN
	if (readme := path / Path('README.md')).exists():
		h.start_tag('div',attr={'class':'container'})
		h.start_tag('p',attr={'class':'index'})
		h.start_tag('span',attr={'class':'index_readme'})
		h.line('README.md')
		h.hr()
		h.end_tag() # span
		h.start_tag('div',attr={'class':'index-markdown'})
		h.start_tag('pre',attr={'class':'index'})
		with open(str(readme)) as f:
			for line in f:
				line = line.replace('\n','')
				if line.startswith('# '):
					line = line[2:]
					line = '<h1 class="index">' + line + '</h1>'
				elif line.startswith('## '):
					line = line[3:]
					line = '<h2 class="index">' + line + '</h2>'
				elif line.startswith('### '):
					line = line[4:]
					line = '<h3 class="index">' + line + '</h3>'
				format_code = False
				i = 0
				while True:
					if i >= len(line):
						break
					char = line[i]
					if char == '`':
						format_code = not format_code
						if format_code:
							line = line[:i] + '<code>' + line[i+1:]
							i += 5
						else:
							print(line[i+1:])
							line = line[:i] + '</code>' + line[i+1:]
							i += 6
					i += 1
				h.file.append(line)
		h.end_tag() # pre
		h.end_tag() # div
		h.end_tag() # p
		h.end_tag() # div
		h.hr({'class':'index'})

	h.start_tag('div',{'class':'index-list'})
	h.start_tag('ul',{'class': 'index'})
	for sub in sorted(os.listdir(str(path))):
		sub = Path(sub)
		h.start_tag('li',{'class':'index'})
		h.start_tag('a',{'class':'index','href':sub})
		if (path/sub).is_dir():
			h.img(attr={'class':'index','src':'/builtins/folder.png'})
		else:
			h.img(attr={'class':'index','src':'/builtins/file.png'})
		h.line(str(sub))
		h.end_tag() # a
		h.end_tag() # li
	h.end_tag() # ul
	h.end_tag() # div
	h.hr({'class':'index'})
	h.end_tag() # body
	h.end_tag() # html
	return h.get()

def read(path: Path) -> bytes:
	if not path.exists():
		raise FileNotFoundError
	if path.is_dir():
		raise IsADirectoryError
	with open(str(path), 'rb') as f:
		file = f.read()
	return file

def handle(conn: s.socket, addr: Any) -> None: # type: ignore
	global HTTP_STATUS_CODES, CHECK_PATHS, EXEC_NAMES, EXEC_MIMES, POST_PATHS, ALLOWED_HOSTNAMES, WEBSITE_DIRS, BUILTINS, ACCEPT_POST, ADD_SLASH_TO_DIR, CONSTRUCT_INDEX
	connection = ''
	while connection != 'close':
		code = 200
		resp_headers = {}
		body = ''
		base_path = WEBSITE_DIRS['*']
		was_executed = False
		try:
			conn.settimeout(3)
			req_raw = b''
			#RECIEVE
			try:
				while not b'\r\n\r\n' in req_raw:
					chunk = conn.recv(1024)
					if not chunk:
						break
					req_raw += chunk
				else:
					print(f'{addr}: Reached end of request.')
			except TimeoutError:
				raise RequestTimeout

			#PARSE
			req = req_raw.decode('UTF-8')
			req_lines = req.split('\n')
			req_header_lines = req.split('\r\n\r\n')[0].split('\r\n')
			req_body_lines = req.split('\r\n\r\n')[1]
			print(req_header_lines)

			try:
				method, path, http_ver = req_header_lines[0].split()
				while path.startswith('/'):
					path = path[1:]
				if '..' in path:
					raise NotFound
				path = path.split('?')[0]
			except ValueError:
				raise BadRequest
			headers = {}
			for line in req_header_lines[1:]:
				elements = line.split(': ')
				if len(elements) != 2:continue
				key = elements[0].replace('\r', '').replace('\n', '')
				val = elements[1].replace('\r', '').replace('\n', '')
				headers[key.lower()] = val

			#CONNCHECK
			if client_connection := headers.get('connection'):
				if client_connection == 'close':
					connection = 'close'
				elif client_connection == 'keep-alive':
					connection = 'keep-alive'
			else:
				connection = 'close'

			#HNCHECK
			if host := headers.get('host'):
				if host in ALLOWED_HOSTNAMES or len(ALLOWED_HOSTNAMES) == 0:
					if host in WEBSITE_DIRS.keys():base_path = WEBSITE_DIRS[host]
					else:base_path = WEBSITE_DIRS['*']
				else:raise Forbidden(f'Hostname "{host}" not allowed.')
			else:raise Forbidden('No Host header.')

			#GETMETHOD
			if method == 'GET':
				for check in CHECK_PATHS + ['']:
					# Check for builtins.
					if Path(path)[0] in BUILTINS.keys():
						full_path = (main_path := (base_path := BUILTINS[Path(path)[0]]) / Path(path)) / check
					else:
						full_path = (main_path := base_path / Path(path)) / check

					#CAPTURE
					to_check = []
					if host in CAPTURE_PATHS.keys():
						to_check += CAPTURE_PATHS[host]
					to_check += CAPTURE_PATHS['*']
					for capture_path in to_check:
						if Path(path) in capture_path:
							for capture_script in CAPTURE_SCRIPTS:
								if (full_capture_path := base_path / capture_path / capture_script).exists():
									result = subprocess.run(
										[str(full_capture_path), '--host', headers['host'], '--headers', json.dumps(headers), '--method', method, '--path', '/' + path],
										capture_output=True,
										text=True
									)
									resp_headers = {'Content-Type': 'text/html'}
									body = result.stdout
									if result.returncode == 3:
										raise SeeOther(body)
									elif result.returncode in EXCEPTIONS.keys():
										raise EXCEPTIONS[result.returncode]
									was_executed = True
									raise OK

					if full_path.exists():
						if main_path.is_dir() and not path.endswith('/') and path:
							raise SeeOther('/' + str(path) + '/')
						if not full_path.is_dir():
							print(f'{addr}: Resource is file.')
							resp_headers = {'Content-Type': (mime := guess_type(os.path.basename(str(full_path)))[0])}
							#EXECRESOURCE
							if mime in EXEC_MIMES and Path(full_path[-1]) in EXEC_NAMES:
								result = subprocess.run(
									[str(full_path), '--host', headers['host'], '--headers', json.dumps(headers), '--path', '/' + path],
									capture_output=True,
									text=True
								)
								resp_headers = {'Content-Type': 'text/html'}
								body = result.stdout
								if result.returncode == 3:
									raise SeeOther(body)
								elif result.returncode in EXCEPTIONS.keys():
									raise EXCEPTIONS[result.returncode]
								was_executed = True
							else:
								body = read(full_path)
							break
						else:
							#INDEX
							print(f'{addr}: Resource is directory.')
							if CONSTRUCT_INDEX:
								print(f'{addr}: Constructing index.')
								resp_headers = {'Content-Type': 'text/html'}
								body = index(full_path, Path(path))
								break
							else:
								raise NotFound('Directory listing not enabled.')
				else:
					raise NotFound('/' + path)
			#POSTMETHOD
			elif method == 'POST' and ACCEPT_POST:
				for check in POST_PATHS:
					full_path = (main_path := base_path / Path(path)) / check
					if full_path.exists():
						result = subprocess.run(
							[str(full_path), '--headers', json.dumps(headers)],
							input=req_body_lines,
							capture_output=True,
							text=True
						)
						body = result.stdout
						print(result.stderr)
						print(code := result.returncode)
						if code in EXCEPTIONS.keys():
							raise EXCEPTIONS[code](full_path)
						break
				else:
					raise NotFound('/' + path)
			else:
				raise MethodNotAllowed(method)

		#ASSIGNCODE
		except OK as e:
			code = 200
		except Created as e:
			print(Fore.LIGHTGREEN_EX + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			code = 201
		except Found as e:
			print(Fore.LIGHTYELLOW_EX + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			redirect_path = str(e)
			code = 302
		except SeeOther as e:
			print(Fore.LIGHTYELLOW_EX + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			redirect_path = str(e)
			code = 303
		except BadRequest as e:
			print(Fore.RED + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			code = 400
		except Forbidden as e:
			print(Fore.RED + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			code = 403
		except NotFound as e:
			print(Fore.RED + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			code = 404
		except MethodNotAllowed as e:
			print(Fore.RED + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			code = 405
		except RequestTimeout as e:
			print(Fore.RED + f'{addr}: {type(e).__name__} ({e})' + Fore.RESET)
			code = 408
		except Exception as e:
			code = 500

		#SENDRESPONCE
		good = [200,201]
		redirect = [302,303]
		bad = [400,403,404,405,408,500]

		#SENDREDIRECT
		if code in redirect:
			resp_headers = {'Location':redirect_path}
			body = ''

		#SENDBAD
		elif code in bad:
			connection = 'close'
			resp_headers = {
				'Content-Type': 'text/html',
				'Content-Disposition': f'inline; filename="{code}.html"'
			}
			if (error_page := (base_path / f'{code}.html')).exists():
				body = read(error_page)
			else:
				body = f'<html><head></head><body><p>{code} {HTTP_STATUS_CODES[code]}</p></body></html>'
		else:
			if was_executed:
				resp_headers['Content-Disposition'] = f'inline; filename="{os.path.basename(full_path.__str__()).split(".")[0]}.html"'
			else:
				resp_headers['Content-Disposition'] = f'inline; filename="{os.path.basename(full_path.__str__())}"'
		print(Fore.YELLOW + f'{addr}: {code} {HTTP_STATUS_CODES[code]}' + Fore.RESET)
		print(Fore.MAGENTA + f'{addr}: Sending response.' + Fore.RESET)
		if type(body) == str:
			body = body.encode('UTF-8')
		resp_headers['Access-Control-Allow-Origin'] = '*'
		resp_headers['Content-Length'] = str(len(body))
		hstring = ''.join([f'\n{key}: {value}' for key, value in resp_headers.items()])
		hstring += '\r\n\r\n'
		conn.sendall((f'HTTP/1.1 {code} {HTTP_STATUS_CODES[code]}{hstring}').encode('UTF-8'))
		conn.sendall(body)
	print(Fore.MAGENTA + f'{addr}: Closed connection.' + Fore.RESET)
	conn.close()

def usage() -> None:
	print(
		"""Basic Somewhat HTTP Server (BSHS)

Usage:
bshs [args]
	-h, --help
	bshs -h
	Show this message.

	--help-all
	bshs --help-all
	Print more information.

	-a, --allow-hostname
	bshs -a <hostname>
	Add a hostname to the allowed hostnames list.

	-p, --port
	bshs -p <port>
	Set the server port.

	-r, --route-dir
	bshs -r <hostname> <directory>
	Route a hostname to a directory on the system.

	-s, --source
	bshs -s <directory>
	Set the global directory route.

	-v, --version
	bshs -v
	Print the current version and other information.

Information:
	Routing a hostname with -r will configure bshs to look in said directory when connecting from the desired hostname.

	Setting a global directory route with -s will route all incoming connections (with an allowed hostname) to the desired directory.

	Allowing a hostname with -a will configure bshs to allow said hostname to access the global directory route.
""")

def usage_all() -> None:
	print(
		"""Basic Somewhat HTTP Server (BSHS)

Usage:
bshs [args]
	-h, --help
		bshs -h
		Print less information.

	--help-all
		bshs --help-all
		Show this message.

	-a, --allow-hostname
		bshs -a <hostname>
		Add a hostname to the allowed hostnames list.

	-p, --port
		bshs -p <port>
		Set the server port.

	-r, --route-dir
		bshs -r <hostname> <directory>
		Route a hostname to a directory on the system.

	-s, --source
		bshs -s <directory>
		Set the global directory route.

	-v, --version
		bshs -v
		Print the current version and other information.

	--changelog
		bshs --changelog
		Print the latest changelog.

	--get-log
		bshs --get-log <version>
		Print the changelog for a specific version.

	--all-versions
		bshs --all-versions
		Print all versions known to the changelog.

	--capture-path <host> <path>
		Add a path capture to a hostname. (see --get-log 0.1.8)

	--no-index
		Disable directory indexing.

	--no-post
		Do not accept POST requests.

	--prepend-get-index <path>

	--append-get-index <path>

	--prepend-post-index <path>

	--append-post-index <path>

	--prepend-exec-index <path>

	--append-exec-index <path>

Information:
	Routing a hostname with -r will configure bshs to look in said directory when connecting from the desired hostname.

	Setting a global directory route with -s will route all incoming connections (with an allowed hostname) to the desired directory.

	Allowing a hostname with -a will configure bshs to allow said hostname to access the global directory route.
""")

def main() -> None:
	global HTTP_STATUS_CODES, CHECK_PATHS, EXEC_NAMES, EXEC_MIMES, ALLOWED_HOSTNAMES, WEBSITE_DIRS, CAPTURE_PATHS, PORT, ADDR, CONSTRUCT_INDEX
	# Handle arguments.
	#ARGS
	args = sys.argv[1:]

	current = None
	for arg in args:
		if current:
			if current == 'source':
				WEBSITE_DIRS['*'] = Path(arg)
				current = None
			elif current == 'allow_hostname':
				ALLOWED_HOSTNAMES.append(arg)
				current = None
			elif current == 'routedir1':
				if (routehn := arg) != '*':
					ALLOWED_HOSTNAMES.append(arg)
				current = 'routedir2'
			elif current == 'routedir2':
				WEBSITE_DIRS[routehn] = Path(arg)
				current = None 
			elif current == 'port':
				PORT = int(arg)
				current = None
			elif current == 'getlog':
				if arg in CHANGELOG.keys():
					print(CHANGELOG[arg])
					exit(0)
				else:
					print(f'Log "{arg}" not found.')
					exit(1)
			elif current == 'config':
				#CONFIG
				try:
					conf_path = Path(arg)
				except Exception:
					print('Invalid config path.')
					exit(1)
				if conf_path.exists():
					with open(str(conf_path)) as f:
						config = json.load(f)
				else:
					print('Configuration file does not exist.')
					exit(1)
				if 'port' in config.keys():
					PORT = config['port']
				if 'addr' in config.keys():
					ADDR = config['addr']
				if 'capture-paths' in config.keys():
					for hostname, pathlist in config['capture-paths'].items():
						if not CAPTURE_PATHS.get(hostname):
							CAPTURE_PATHS[hostname] = []
						for path in pathlist:
							while path.startswith('/'):path = path[1:]
							CAPTURE_PATHS[hostname].append(Path(path))
				if 'allowed-hostnames' in config.keys():
					for hostname in config['allowed-hostnames']:
						ALLOWED_HOSTNAMES.append(hostname)
				if 'website-dirs' in config.keys():
					for hostname, path in config['website-dirs'].items():
						WEBSITE_DIRS[hostname] = Path(path)
						ALLOWED_HOSTNAMES.append(hostname)
				current = None
			elif current == 'prepend_get_index':
				try:
					CHECK_PATHS.insert(0, Path(arg))
				except Exception:
					print(f'Invalid path provided: {arg}')
					exit(1)
				current = None
			elif current == 'append_get_index':
				try:
					CHECK_PATHS.append(Path(arg))
				except Exception:
					print(f'Invalid path provided: {arg}')
					exit(1)
				current = None
			elif current == 'prepend_post_index':
				try:
					POST_PATHS.insert(0, Path(arg))
				except Exception:
					print(f'Invalid path provided: {arg}')
					exit(1)
				current = None
			elif current == 'append_post_index':
				try:
					POST_PATHS.append(Path(arg))
				except Exception:
					print(f'Invalid path provided: {arg}')
					exit(1)
				current = None
			elif current == 'prepend_exec_index':
				try:
					EXEC_NAMES.insert(0, Path(arg))
				except Exception:
					print(f'Invalid path provided: {arg}')
					exit(1)
				current = None
			elif current == 'append_exec_index':
				try:
					EXEC_NAMES.append(Path(arg))
				except Exception:
					print(f'Invalid path provided: {arg}')
					exit(1)
				current = None
			elif current == 'capture_path1':
				cap_host = arg
				current = 'capture_path2'
			elif current == 'capture_path2':
				if not cap_host in CAPTURE_PATHS.keys():
					CAPTURE_PATHS[cap_host] = []
				while arg.startswith('/'):
					arg = arg[1:]
				CAPTURE_PATHS[cap_host].append(Path(arg))
				current = None
		else:
			if arg in ['-h', '--help']:
				usage()
				exit(0)
			elif arg in ['--help-all']:
				usage_all()
				exit(0)
			elif arg in ['-s', '--source']:
				current = 'source'
			elif arg in ['-a', '--allow-hostname']:
				current = 'allow_hostname'
			elif arg in ['-r', '--route-dir']:
				current = 'routedir1'
			elif arg in ['-p', '--port']:
				current = 'port'
			elif arg in ['-v', '--version']:
				print(f'BSHS {__version__}')
				print('by IWearTwoHats (Rowan Denny)')
				print('http://repo.somethingfunny.xyz/bshs')
				exit(0)
			elif arg in ['--changelog']:
				print(CHANGELOG[__version__])
				exit(0)
			elif arg in ['--get-log']:
				current = 'getlog'
			elif arg in ['--all-versions']:
				for ver in CHANGELOG.keys():
					print(ver)
				exit(0)
			elif arg in ['--no-index']:
				CONSTRUCT_INDEX = False
			elif arg in ['--no-post']:
				ACCEPT_POST = False
			elif arg in ['-c', '--config']:
				current = 'config'
			elif arg in ['--prepend-get-index']:
				current = 'prepend_get_index'
			elif arg in ['--append-get-index']:
				current = 'append_get_index'
			elif arg in ['--prepend-post-index']:
				current = 'prepend_post_index'
			elif arg in ['--append-post-index']:
				current = 'append_post_index'
			elif arg in ['--prepend-exec-index']:
				current = 'prepend_exec_index'
			elif arg in ['--append-exec-index']:
				current = 'append_exec_index'
			elif arg in ['--capture-path']:
				current = 'capture_path1'

	#BIND
	sock = s.socket(s.AF_INET, s.SOCK_STREAM)

	waiting = True
	print(Fore.LIGHTBLUE_EX + 'Binding...' + Fore.RESET)
	while waiting:
		try:
			sock.bind(('0.0.0.0', PORT))
			waiting = False
		except PermissionError:
			print(Fore.RED + f'Permission denyed binding to port {PORT}.' + Fore.RESET)
			exit(1)
		except OSError:pass
	for name in ALLOWED_HOSTNAMES:
		print(Fore.LIGHTBLUE_EX + f'HN {name} in allowed hostnames' + Fore.RESET)
	for key, val in WEBSITE_DIRS.items():
		print(Fore.LIGHTBLUE_EX + f'HN {key} routed to {val}' + Fore.RESET)
	for path in CHECK_PATHS:
		print(Fore.MAGENTA + f'Will check path: {path}' + Fore.RESET)
	for path in EXEC_NAMES:
		print(Fore.MAGENTA + f'Will execute path: {path}' + Fore.RESET)
	for path in EXEC_MIMES:
		print(Fore.MAGENTA + f'Will execute mime: {path}' + Fore.RESET)
	for host, paths in CAPTURE_PATHS.items():
		print(f'{host} will capture:')
		for path in paths:
			print(f'\t{path}')

	print(Fore.LIGHTMAGENTA_EX + '' + Fore.RESET)
	print(Fore.LIGHTMAGENTA_EX + '' + Fore.RESET)
	sock.listen(15)
	print(Fore.LIGHTBLUE_EX + f'http://{ADDR}:{PORT}' + Fore.RESET)

	#LOOP
	try:
		while True:
			conn, addr = sock.accept()
			print(Fore.LIGHTGREEN_EX + f'Starting thread for connection from {addr[0]}' + Fore.RESET)
			t = Thread(target=handle, args=[conn, addr[0]])
			t.start()
	except KeyboardInterrupt:
		print('Done.')
		sock.close()
		exit(0)
	except Exception as e:
		print(Fore.RED + f'Encountered unexpected exception: {e}' + Fore.RESET)
		sock.close()
		exit(1)

if __name__ == '__main__':
	main()
