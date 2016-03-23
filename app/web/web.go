// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"net/http"
	"strings"
)

var (
	Routes RouteMap
	Router func(*Context, RouteMap)
)

type RouteMap map[string]*Handler

type Handler struct {
	Admin  bool
	Anon   bool
	Cron   bool
	Method func(*Context)
	Task   bool
	XSRF   bool
}

func (h *Handler) Call(c *Context) {
	h.Method(c)
}

func Dispatch(w http.ResponseWriter, r *http.Request) {
	c := NewContext(w, r)
	path := r.URL.Path
	// defer func() {
	// 	if err := recover(); err != nil {
	// 		c.Errorf("%v\n%s", err, string(debug.Stack()))
	// 		c.Serve500()
	// 	}
	// }()
	if !strings.HasPrefix(path, "/") {
		c.Serve404()
		return
	}
	path = path[1:]
	if path == "" {
		// c.Pipe(site.RenderHome(c), site.Page, site.Main)
		return
	}
	elems := strings.Split(path, "/")
	if handler, ok := Routes[elems[0]]; ok {
		for _, elem := range elems[1:] {
			if elem != "" {
				c.Args = append(c.Args, elem)
			}
		}
		handler.Call(c)
		return
	}
	c.Serve404()
}
