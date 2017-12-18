
IMAGE=sorend/keepmyphotos
VER=$(shell git describe --long --match ?.? --dirty=-dirty)

default:
	@echo Please select target

build:
	docker build -t $(IMAGE):latest -t $(IMAGE):$(VER) .

deploy:
	docker tag $(IMAGE):$(VER) cloud.canister.io:5000/$(IMAGE):$(VER)
	docker push cloud.canister.io:5000/$(IMAGE):$(VER)
