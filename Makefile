lint:
	# gofumpt is a tool for formatting the code, strickter that go fmt.
	# To find out how to set up autoformatting in your IDE, visit
	# https://github.com/mvdan/gofumpt#visual-studio-code
	golangci-lint run -j8 --enable-only gofumpt ./... --fix
	golangci-lint run -j8 --enable-only gci ./... --fix
	golangci-lint run -j8 ./...

regen:
	python scripts/cli_assign_door_ids.py -i media/улк-5.svg -o media/улк-5.svg 
	python scripts/cli_svg_to_json.py -i media/улк-5.svg -t 5
