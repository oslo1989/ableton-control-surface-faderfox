launch12:
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

install-deps:
	@pip install -r requirements.txt

restart-12: kill copy-controller-script launch12

restart: restart-12

build: lint-fix lint