// Public Domain (-) 2015-2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package template

import (
	"strconv"
	"strings"

	"github.com/tav/gitfund/app/asset"
)

var (
	STATIC_CLIENT_JS = Static("client.js")
	STATIC_LIB_JS    = Static("lib.js")
	STATIC_SITE_CSS  = Static("site.css")
)

var chars = strings.NewReplacer(
	`&`, "&amp;",
	`'`, "&#39;",
	`<`, "&lt;",
	`>`, "&gt;",
	`"`, "&#34;",
)

func Escape(s string) []byte {
	return []byte(chars.Replace(s))
}

func EscapeString(s string) string {
	return chars.Replace(s)
}

func Static(path string) []byte {
	return []byte("/static/assets/" + asset.Files[path])
}

func String(any interface{}) string {
	switch v := any.(type) {
	case []byte:
		return string(v)
	case string:
		return v
	case int:
		strconv.FormatInt(int64(v), 10)
	case int64:
		strconv.FormatInt(v, 10)
	case uint:
		strconv.FormatUint(uint64(v), 10)
	case uint64:
		strconv.FormatUint(v, 10)
	}
	return ""
}
