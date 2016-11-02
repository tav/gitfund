// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package model

import "time"

type Login struct {
	Email string `model:"a,noindex"`
}

type User struct {
	Created time.Time `model:"a,now"`
	Name    string    `model:"b"`
	Tags    []byte    `model:"c"`
	Version int64     `model:"d,1"`
	Words   []string  `model:"e"`
}
