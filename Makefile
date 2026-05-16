DOMAIN := messages
LOCALES_DIR := locales
BABEL_CFG := babel.cfg
POT_FILE := $(LOCALES_DIR)/$(DOMAIN).pot

.PHONY: i18n-extract i18n-update i18n-compile i18n all

i18n-extract:
	pybabel extract -F $(BABEL_CFG) -o $(POT_FILE) .

i18n-update: i18n-extract
	pybabel update -D $(DOMAIN) -i $(POT_FILE) -d $(LOCALES_DIR)

i18n-compile:
	pybabel compile -D $(DOMAIN) -d $(LOCALES_DIR)

i18n: i18n-update i18n-compile

all: i18n
