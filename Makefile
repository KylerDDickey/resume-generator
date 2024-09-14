DATA_FILE = ./data.json
TEMPLATES_DIR = ./templates

TEMP_DIR = ./tmp
OUT_DIR = ./out

NOW := $(shell date '+%Y-%m-%dT%H:%M:%S')
RESUME_FILE_NAME := resume_$(NOW)
OUT_MARKDOWN = $(OUT_DIR)/$(RESUME_FILE_NAME).md
TEMP_MARKDOWN = $(TEMP_DIR)/$(RESUME_FILE_NAME).md.tmp
OUT_PDF = $(OUT_DIR)/$(RESUME_FILE_NAME).pdf

init:
	mkdir -p $(TEMP_DIR)
	mkdir -p $(OUT_DIR)

markdown: init
	python3 main.py $@ -t $(TEMPLATES_DIR) -i $(DATA_FILE) -o $(OUT_MARKDOWN)

pdf: init
	python3 main.py $@ -t $(TEMPLATES_DIR) -i $(DATA_FILE) -o $(TEMP_MARKDOWN)
	pandoc $(TEMP_MARKDOWN) -o $(OUT_PDF) --pdf-engine=weasyprint --from="markdown"
