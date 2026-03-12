CHANGELOG = {
'0.1.0': """0.1.0
	- Initial release.
""",
'0.1.1': """0.1.1
	- 303 return code from index script now returns redirect to stdout.
""",
'0.1.2': """0.1.2
	- Prints more information on startup.
""",
'0.1.3': """0.1.3
	- Fixed a very silly error.
""",
'0.1.4': """0.1.4
	- Now supports HTTP filename suggestion.
""",
'0.1.5': """0.1.5
	- POST support.
	- If a post request is recieved, search for post.py in the requested dir. If found, run it with the request body passed as stdin, and the request headers passed as a json string appended to --headers.
""",
'0.1.6': """0.1.6
	- README.md will now show up in directory indexes.
""",
'0.1.7': """0.1.7
	- Added new command line options.
		* --no-index
			Disable directory indexing.

		* --no-post
			Do not accept POST requests.

		* --prepend-get-index <path>

		* --append-get-index <path>

		* --prepend-post-index <path>

		* --append-post-index <path>

		* --prepend-exec-index <path>

		* --append-exec-index <path>
""",
'0.1.8': """0.1.8
	- New command line options:
		* --capture-path <host> <path>
			Add a path capture to a hostname.

	- New Features
		* Path capture
			Adding a path capture will cause any requests in the specified directory, or any subdirectories goto the file 'capture.*'. The name will vary by an internal list similar to the GET index list.

			Arguments for capture file:
				* --host {host}
				* --headers {json_string}
				* --method {method}
				* --path {path}

			It will follow the same return code mapping.
			Mapping:
				- 1 = 404 Not Found
				- 2 = 403 Forbidden
				- 3 = 303 See Other
				- 4 = 405 Method not Allowed
				- 5 = 500 Internal Server Error
				- 6 = 201 Created
				- 7 = 302 Found
""",
'0.2.0': """0.2.0
	- New Command Line Options:
		* --config

	- New Features:
		* JSON config files
			- Example:
{
	"port": 80,
	"website-dirs": {
		"*": "/path/to/website",
		"somethingfunny.xyz": "/path/to/website"
	}
}
""",
'0.3.0': """0.3.0
	- New Features:
		* Keep-Alive support
			When a client requests a resource with the header "Connection: Keep-Alive", the server will now keep the socket open until it is requested to close.
"""
}
