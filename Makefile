###########################################################
# This variables may be overriden to match you environment
###########################################################

# If locales are enabled, set the name of the lrelease binary on your system. If
# you have trouble compiling the translations, you may have to specify the full path to
# lrelease
#LRELEASE = lrelease
#LRELEASE = lrelease-qt4

# QGISDIR points to the location where your plugin should be installed.
# This varies by platform, relative to your HOME directory:
# * Linux:
#   .local/share/QGIS/QGIS3/profiles/default/python/plugins/
# * Mac OS X:
#   Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins
# * Windows:
#   AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins'
QGISDIR ?= .local/share/QGIS/QGIS3/profiles/default

###############################################################
# Normally you would not need to override variables below here
###############################################################

PLUGINNAME = groupLayers

default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'

deploy: ## Deploy plugin archive to your QGIS plugin directory (for archive testing)
deploy: package derase
	unzip dist/$(PLUGINNAME).zip -d $(HOME)/$(QGISDIR)/python/plugins/

derase: ## Remove deployed plugin from your QGIS plugin directory
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

package: ## Create a zip package of the plugin named $(PLUGINNAME).zip.
package:
	mkdir -p dist
	rm -f dist/$(PLUGINNAME).zip
	git archive -o dist/$(PLUGINNAME).zip HEAD $(PLUGINNAME)
	echo "Created package: dist/$(PLUGINNAME).zip"

.PHONY: link
link: ## Create symbolic link to this folder in your QGIS plugins folder (for development)
link: derase
	ln -s $(shell pwd)/$(PLUGINNAME) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

.PHONY: unlink
unlink: ## Unlink $(PLUGINNAME) from your QGIS plugins folder
unlink: derase
