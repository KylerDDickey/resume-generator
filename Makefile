DATA_DIR = ./data
TEMPLATES_DIR = ./templates
STYLING_DIR = ./styling

TEMP_DIR = ./tmp
OUT_DIR = ./out
STATIC_DEV_DOC_DIR = ./static/doc

NOW := $(shell date '+%Y-%m-%dT%H:%M:%S')
RESUME_FILE_NAME := resume_$(NOW)
OUT_MARKDOWN = $(OUT_DIR)/$(RESUME_FILE_NAME).md
TEMP_MARKDOWN = $(TEMP_DIR)/$(RESUME_FILE_NAME).md.tmp
DEV_TEMP_MARKDOWN = $(TEMP_DIR)/resume_dev.md.tmp
OUT_PDF = $(OUT_DIR)/$(RESUME_FILE_NAME).pdf
DEV_OUT_PDF = $(STATIC_DEV_DOC_DIR)/resume_dev.pdf

source ?= default
DATA_FILE = $(DATA_DIR)/$(source).json

pdf: init
	python3 main.py pdf -t $(TEMPLATES_DIR) -i $(DATA_FILE) -o $(TEMP_MARKDOWN)
	pandoc $(TEMP_MARKDOWN) \
		-o $(OUT_PDF) \
		--pdf-engine=weasyprint \
		--css $(STYLING_DIR)/pdf.css \
		--from="markdown"

pdf-dev: init
	mkdir -p $(STATIC_DEV_DOC_DIR)
	python3 main.py pdf -t $(TEMPLATES_DIR) -i $(DATA_FILE) -o $(DEV_TEMP_MARKDOWN)
	pandoc $(DEV_TEMP_MARKDOWN) \
		-o $(DEV_OUT_PDF) \
		--pdf-engine=weasyprint \
		--css $(STYLING_DIR)/pdf.css \
		--from="markdown"

markdown: init
	python3 main.py markdown -t $(TEMPLATES_DIR) -i $(DATA_FILE) -o $(OUT_MARKDOWN)

init:
	mkdir -p $(TEMP_DIR)
	mkdir -p $(OUT_DIR)

clean:
	rm -f $(TEMP_DIR)/*.tmp

.PHONY: clean init markdown pdf pdf-dev
