// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"fmt"
	"net/http"
	"os"
	"runtime/debug"
	"strings"

	"github.com/tav/gitfund/app/config"
	"github.com/tav/golly/log"
	"google.golang.org/appengine"
)

var (
	DevServer     = os.Getenv("MEMCACHE_PORT_11211_TCP_ADDR") == ""
	PageRenderers = []Renderer{}
)

type Handler func(*Context)

// raise301 can be used as a value to panic in order to interrupt the control
// flow and raise a 301 Permanent Redirect.
type raise301 struct {
	url string
}

// raise404 can be used as a value to panic in order to interrupt the control
// flow and raise a 404 Not Found.
type raise404 struct{}

type Renderer func(c *Context, content []byte)

type Route struct {
	Admin     bool
	Anon      bool
	Cron      bool
	Handler   Handler
	Renderers []Renderer
	Task      bool
	XSRF      bool
}

type RouteMap map[string]*Route

type dispatcher struct {
	path         string
	routeMap     RouteMap
	routeMissing func(*Context) Handler
}

func (d *dispatcher) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if DevServer {
		log.Infof("[%s] %s", r.Method, r.URL)
	}
	c := NewContext(w, r)
	defer func() {
		if err := recover(); err != nil {
			c.buffer.Reset()
			if redir, ok := err.(raise301); ok {
				c.headers = map[string]string{
					"Location": redir.url,
				}
				c.status = 301
			} else if _, ok := err.(raise404); ok {
				c.serve404()
			} else {
				c.Strings["fatal/error"] = fmt.Sprintf("%s", err)
				c.Strings["fatal/stacktrace"] = string(debug.Stack())
				c.Errorf("%v\n%s", err, c.Strings["fatal/stacktrace"])
				c.serve500()
			}
		}
		ct := false
		hdrs := w.Header()
		for k, v := range c.headers {
			switch strings.ToLower(k) {
			case "content-type":
				ct = true
			}
			hdrs.Set(k, v)
		}
		var out []byte
		if c.written {
			out = c.output
		} else {
			out = c.buffer.Bytes()
		}
		if !ct {
			hdrs.Set("Content-Type", "text/html; charset=utf-8")
		}
		for _, v := range c.cookies {
			hdrs.Set("Set-Cookie", v)
		}
		w.WriteHeader(c.status)
		if len(out) != 0 {
			w.Write(out)
		}
	}()
	if !DevServer {
		badURL := false
		if r.TLS == nil {
			badURL = true
		} else if config.EnsureHost && r.Host != config.CanonicalHost && !(c.IsCronRequest() || c.IsTaskRequest()) {
			badURL = true
		}
		if badURL {
			host := config.CanonicalHost
			if host == "" {
				host = r.Host
			}
			if r.Method == "GET" || r.Method == "HEAD" {
				url := r.URL
				url.Scheme = "https"
				url.Host = host
				c.RaiseRedirect(url.String())
			} else {
				c.RaiseRedirect("https://" + host + "/")
			}
		}
	}
	path := r.URL.Path
	if !strings.HasPrefix(path, d.path) {
		c.serve404()
		return
	}
	path = path[len(d.path):]
	if len(path) > 0 && path[0] == '/' {
		path = path[1:]
	}
	elems := strings.Split(path, "/")
	if path == "" {
		elems[0] = "/"
	}
	for _, elem := range elems[1:] {
		if elem != "" {
			c.Args = append(c.Args, elem)
		}
	}
	var handler Handler
	if route, exists := d.routeMap[elems[0]]; exists {
		handler = route.Handler
	} else {
		handler = d.routeMissing(c)
	}
	if handler == nil {
		c.serve404()
		return
	}
	handler(c)
}

func Handle(path string, routeMap RouteMap, routeMissing func(*Context) Handler) {
	http.Handle(path, &dispatcher{path, routeMap, routeMissing})
}

func Run() {
	if DevServer {
		fmt.Println(">> Started\n")
	}
	appengine.Main()
}

func init() {
	stdout := log.Must.StreamHandler(&log.Options{
		BufferSize: 4096,
		Formatter: log.Must.TemplateFormatter(
			`{{color "green"}}   [INFO] {{printf "%-60s" .Message}}{{if .Data}}{{json .Data}}{{end}}{{color "reset"}}
`, log.SupportsColor(os.Stdout) && DevServer, nil),
		LogType: log.InfoLog,
		Stream:  os.Stdout,
	})
	stderr := log.Must.StreamHandler(&log.Options{
		BufferSize: 4096,
		Formatter: log.Must.TemplateFormatter(
			`{{color "red"}}  [ERROR] {{printf "%-60s" .Message}}{{if .Data}}{{json .Data}}{{end}}{{if .File}}
{{.File}}:{{.Line}}{{end}}{{color "reset"}}
`, log.SupportsColor(os.Stderr) && DevServer, nil),
		LogType: log.ErrorLog,
		Stream:  os.Stderr,
	})
	log.SetHandler(log.MultiHandler(stdout, stderr))
}
