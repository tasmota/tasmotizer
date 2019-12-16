venv:
	@echo "creating Virtualenv..."
	virtualenv -p python3 venv
	. venv/bin/activate; \
	pip install --upgrade pip setuptools; \
	pip install -r requirements.txt;

build: venv
	@echo "creating Application..."
	. venv/bin/activate; \
	pip install -U pyinstaller; \
	pyinstaller --console --onefile --name=tasmotizer tasmotizer.py;

clean: 
	@echo "cleaning..."
	@rm -f *.spec
	@rm -rf __pycache__
	@rm -rf build


run: venv
	. venv/bin/activate; \
	python3 tasmotizer.py


