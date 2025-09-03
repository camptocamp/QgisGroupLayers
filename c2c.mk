LOCAL_PLUGINS_PATH = dist
PLUGIN_REPO_PATH = s3://qgis.camptocamp.net/plugins/mki
PLUGIN_REPO_URL = https://qgis.camptocamp.net/plugins/mki
S3_CP_OPTIONS = --cache-control no-cache

include Makefile

.PHONY: sync
sync:
	aws --profile qgis.camptocamp.net s3 sync --exclude "*" --include "*.txt" $(PLUGIN_REPO_PATH) $(LOCAL_PLUGINS_PATH)/

$(LOCAL_PLUGINS_PATH)/plugins.xml: $(LOCAL_PLUGINS_PATH)/$(PLUGINNAME).zip
	unzip -p $(LOCAL_PLUGINS_PATH)/$(PLUGINNAME).zip $(PLUGINNAME)/metadata.txt > $(LOCAL_PLUGINS_PATH)/$(PLUGINNAME).txt
	qgis-plugins.xml $(LOCAL_PLUGINS_PATH)/ $(PLUGIN_REPO_URL)

.PHONY: upload
upload: ## Deploy plugin on qgis.camptocamp.net
upload: package sync $(LOCAL_PLUGINS_PATH)/plugins.xml
	aws --profile qgis.camptocamp.net s3 cp $(S3_CP_OPTIONS) $(LOCAL_PLUGINS_PATH)/$(PLUGINNAME).zip $(PLUGIN_REPO_PATH)/
	aws --profile qgis.camptocamp.net s3 cp $(S3_CP_OPTIONS) $(LOCAL_PLUGINS_PATH)/$(PLUGINNAME).txt $(PLUGIN_REPO_PATH)/
	aws --profile qgis.camptocamp.net s3 cp $(S3_CP_OPTIONS) $(LOCAL_PLUGINS_PATH)/plugins.xml $(PLUGIN_REPO_PATH)/
