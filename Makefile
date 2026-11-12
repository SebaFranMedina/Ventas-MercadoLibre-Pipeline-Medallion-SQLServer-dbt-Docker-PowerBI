up:        ## build and run everything
	docker compose up --build --abort-on-container-exit pipeline
real:      ## run with a real export placed in data/raw/
	INPUT_FILE=$(FILE) docker compose run --rm pipeline
test:
	pytest -q
sample:
	python scripts/generate_sample_data.py
down:
	docker compose down -v
