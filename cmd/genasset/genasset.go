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

	// Read the JSON assets manifest.
	assets, err := ioutil.ReadFile("assets.json")
	if err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: %s", err)
		return
	}

	// Parse the manifest.
	assets = assets[1 : len(assets)-1]
	split := bytes.Split(assets, []byte{',', ' '})
	assets = bytes.Join(split, []byte{',', '\n', '\t'})

	// Write out the package header.
	fmt.Print(`package asset

var Files = map[string]string{
	`)

	// Write the asset mappings, footer, and close the file.
	fmt.Print(string(assets))
	fmt.Print(`,
}
`)

}
