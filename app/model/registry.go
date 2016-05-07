// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

// +build !appengine
package model

import (
	"fmt"
)

var KindRegistry = map[string]interface{}{}

func reg(kind string, model interface{}) {
	if prev, exists := KindRegistry[kind]; exists {
		panic(fmt.Sprintf("kind: %s already registered for %#v", kind, prev))
	}
	KindRegistry[kind] = model
}

func init() {
	reg("L", Login{})
	reg("U", User{})
}
