lint:
	# gofumpt is a tool for formatting the code, strickter that go fmt.
	# To find out how to set up autoformatting in your IDE, visit
	# https://github.com/mvdan/gofumpt#visual-studio-code
	golangci-lint run -j8 --enable-only gofumpt ./... --fix
	golangci-lint run -j8 --enable-only gci ./... --fix
	golangci-lint run -j8 ./...
