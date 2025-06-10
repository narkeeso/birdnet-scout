install:
		poetry install

dev:
		@command -v mprocs >/dev/null 2>&1 || npm install -g mprocs
		mprocs
