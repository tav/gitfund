// Public Domain (-) 2015-2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"os"
)

func main() {

	if len(os.Args) != 3 {
		fmt.Println("Usage: genasset PACKAGE_NAME MANIFEST_FILE")
		os.Exit(1)
	}

	// Read the JSON assets manifest.
	assets, err := ioutil.ReadFile(os.Args[2])
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: %s", err)
		return
	}

	// Parse the manifest.
	assets = assets[1 : len(assets)-1]
	split := bytes.Split(assets, []byte{',', ' '})
	assets = bytes.Join(split, []byte{',', '\n', '\t'})

	// Write out the package header.
	fmt.Printf(`package %s

var Files = map[string]string{
	`, os.Args[1])

	// Write the asset mappings, footer, and close the file.
	fmt.Print(string(assets))
	fmt.Print(`,
}
`)

}
