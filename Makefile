create-venv:
	@pyenv virtualenv 3.7.13 ableton-control-surface-faderfox-venv-3.7.13
	#pyenv activate ableton-control-surface-faderfox-venv-3.7.13

install-deps:
	@pip install --upgrade pip && pip install -r requirements.txt

launch:
	@open /Applications/Ableton*12*

kill:
	@pkill -KILL -f "Ableton Live" || echo "Ableton was not running, so just starting it" && sleep .5

tail:
	@tail -n 50 -f ~/Library/Preferences/Ableton/*/Log.txt | grep --line-buffered -i -e FaderFoxOslo1989Surface

tail-all:
	@tail -n 50 -f ~/Library/Preferences/Ableton/*/Log.txt

copy-controller-script:
	@rm -rf ~/Music/Ableton"/User Library/Remote Scripts/FaderFoxOslo1989Surface"
	@cp -r "FaderFoxOslo1989Surface" ~/Music/Ableton"/User Library/Remote Scripts"
	@rm -rf ~/Music/Ableton"/User Library/Remote Scripts/FaderFoxOslo1989Surface/__pycache__"

lint-fix:
	@ruff FaderFoxOslo1989Surface  --quiet --fix --unsafe-fixes

lint:
	@ruff FaderFoxOslo1989Surface --quiet
	@mypy FaderFoxOslo1989Surface

format:
	@ruff format FaderFoxOslo1989Surface

lint-format: lint-fix format lint

restart: kill copy-controller-script launch

build: lint-fix lint