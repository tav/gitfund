# Public Domain (-) 2016 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

APP_FILES := $(shell find app -name \*.go -print)
BROWSER_FILES := $(shell find browser -type f -print)
GENERATED := app/asset/files.go app/model/fields.go app/template/ego.go
HDR = `date +'[%H:%M:%S]'` ">>"

.PHONY: all buildapp clean datastore deployapp describe gopkgs indexes memcached pubsub runapp vacuum watch watchloop wipedata

describe:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[31m%-10s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

all: $(GENERATED) ## Generate dependent source files for services
	@true

app/.gopkgs.json: $(APP_FILES) environ/gopkgs $(GENERATED)
	@echo $(HDR) "Generating gopkgs.json"
	@./environ/gopkgs app -i github.com/tav/gitfund

app/asset/files.go: environ/assets.json environ/genasset
	@echo $(HDR) "Generating asset/files.go"
	@./environ/genasset asset environ/assets.json > files.go
	@gofmt -w files.go
	@mkdir -p app/asset
	@mv files.go app/asset/files.go

app/model/fields.go: environ/genmodel
	@echo $(HDR) "Generating model/fields.go + web/model.go"
	@./environ/genmodel app/model/fields.go app/web/model.go
	@gofmt -w app/model/fields.go app/web/model.go

app/template/ego.go: template/*.ego
	@echo $(HDR) "Generating template/ego.go"
	@ego -o app/template/ego.go -package template
	@gofmt -w app/template/ego.go

buildapp: environ/builder environ/gopkgs $(GENERATED) ## Build the docker image for the app service
	@echo $(HDR) "Ensuring local packages matches the gopkgs manifest"
	@./environ/gopkgs -c app -i github.com/tav/gitfund
	@echo $(HDR) "Building image for app"
	@./environ/builder gitfund app

clean: ## Remove all built/generated files and directories
	@assetgen assetgen.yaml --clean
	@rm -rf \
	 .emulators \
	 app/asset/files.go \
	 app/model/fields.go \
	 app/template/ego.go \
	 app/web/model.go \
	 environ/assets.json \
	 environ/build \
	 environ/builder \
	 environ/genasset \
	 environ/genmodel \
	 environ/gopkgs \
	 environ/run \
	 fields.go \
	 files.go

datastore: ## Run the local datastore emulator
	@mkdir -p .emulators/datastore/WEB-INF
	@test -f .emulators/datastore/WEB-INF/index.yaml || ln index.yaml .emulators/datastore/WEB-INF/
	@gcloud beta emulators datastore start --data-dir .emulators/datastore --no-legacy --host-port localhost:8801

deployapp: buildapp ## Deploy a new version of the app service
	@true

environ/assets.json: assetgen.yaml $(BROWSER_FILES)
	@echo $(HDR) "Building assets.json"
	@assetgen assetgen.yaml

environ/builder: cmd/builder/builder.go
	@echo $(HDR) "Building builder"
	@go build -a -o environ/builder github.com/tav/gitfund/cmd/builder

environ/genasset: cmd/genasset/genasset.go
	@echo $(HDR) "Building genasset"
	@go build -a -o environ/genasset github.com/tav/gitfund/cmd/genasset

environ/genmodel: cmd/genmodel/genmodel.go app/model/model.go app/model/registry.go
	@echo $(HDR) "Building genmodel"
	@go build -o environ/genmodel github.com/tav/gitfund/cmd/genmodel

environ/gopkgs: cmd/gopkgs/gopkgs.go
	@echo $(HDR) "Building gopkgs"
	@go build -a -o environ/gopkgs github.com/tav/gitfund/cmd/gopkgs

environ/run: cmd/run/run.go
	@echo $(HDR) "Building run"
	@go build -a -o environ/run github.com/tav/gitfund/cmd/run

gopkgs: app/.gopkgs.json ## Generate .gopkg.json manifest files
	@true

indexes: ## Update datastore indexes based on index.yaml
	@gcloud preview datastore create-indexes index.yaml

memcached: ## Run the local memcached server
	@memcached -m 128

pubsub: ## Run the local pubsub emulator
	@mkdir -p .emulators/pubsub
	@gcloud beta emulators pubsub start --data-dir .emulators/pubsub --host-port localhost:8802

runapp: environ/run $(GENERATED) ## Run the app service
	@./environ/run app -w private

vacuum: ## Remove unused datastore indexes
	@gcloud preview datastore cleanup-indexes index.yaml

watch: ## Automatically run `make all` when a relevant file change is detected
	@make all
	@fswatch -0 -o \
	 -e .emulators \
	 -e app/.gopkgs.json \
	 -e app/asset/files.go \
	 -e app/model/fields.go \
	 -e app/web/model.go \
	 -e environ/build \
	 -e environ/builder \
	 -e environ/genasset \
	 -e environ/genmodel \
	 -e environ/gopkgs \
	 -e environ/run \
	 . | xargs -0 -n1 -I{} make all

watchloop: ## Use this instead of `make watch` if you don't have fswatch installed
	@while true; do make all; sleep 1; done

wipedata: ## Nuke the data stored in the local datastore
	@rm -rf .emulators
