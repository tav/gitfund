// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"fmt"
	"net"
	"net/http"
	"os"
	"runtime/debug"
	"strings"
	"time"

	"github.com/tav/gitfund/app/config"
	"github.com/tav/golly/log"
)

var (
	DevServer     = os.Getenv("MEMCACHE_PORT_11211_TCP_ADDR") == ""
	PageRenderers = []Renderer{}
	ServerHost    = ""
	ServerIP      = ""
	ServerPort    = "8080"
)

var (
	healthOK = []byte{'o', 'k'}
	serveMux = mux{}
	startup  = []Handler{}
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
	XSRF      bool
}

type Routes map[string]*Route

type Static struct {
	Directory  string
	Expiration time.Duration
	File       string
}

// TODO(tav): Test whether this is needed under the new App Engine flexible
// serving stack. But, for now, copy appengine.Main's approach.
func patchRemoteAddr(r *http.Request) {
	if addr := r.Header.Get("X-AppEngine-User-IP"); addr != "" {
		r.RemoteAddr = addr
	} else if addr = r.Header.Get("X-AppEngine-Remote-Addr"); addr != "" {
		r.RemoteAddr = addr
	} else {
		// Should not normally reach here, but pick a sensible default anyway.
		r.RemoteAddr = "127.0.0.1"
	}
	// The address in the headers will most likely be of these forms:
	//      123.123.123.123
	//      2001:db8::1
	// net/http.Request.RemoteAddr is specified to be in "IP:port" form.
	if _, _, err := net.SplitHostPort(r.RemoteAddr); err != nil {
		// Assume the remote address is only a host; add a default port.
		r.RemoteAddr = net.JoinHostPort(r.RemoteAddr, "80")
	}
}

func writeResponse(c *Context, w http.ResponseWriter) {
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
}

type Dispatcher struct {
	Path    string
	Routes  Routes
	Lookup  func(*Context) (*Route, bool)
	Statics map[string]*Static
}

func (d *Dispatcher) Dispatch(w http.ResponseWriter, r *http.Request) {
	c := newContext(r, 0)
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
				c.SetString("fatal/error", fmt.Sprintf("%s", err))
				c.SetString("fatal/stacktrace", string(debug.Stack()))
				c.Errorf("%v\n%s", err, c.GetString("fatal/stacktrace"))
				c.serve500()
			}
		}
		writeResponse(c, w)
	}()
	if !DevServer {
		badURL := false
		if r.TLS == nil {
			badURL = true
		} else if config.EnsureHost && r.Host != config.CanonicalHost && !c.IsCronRequest() {
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
	if !strings.HasPrefix(path, d.Path) {
		c.serve404()
		return
	}
	path = path[len(d.Path):]
	if len(path) > 0 && path[0] == '/' {
		path = path[1:]
	}
	elems := strings.Split(path, "/")
	if path == "" {
		elems[0] = "/"
	}
	pathArgs := []string{}
	for _, elem := range elems[1:] {
		if elem != "" {
			pathArgs = append(pathArgs, elem)
		}
	}
	c.SetPathArgs(pathArgs)
	route, exists := d.Routes[elems[0]]
	if !exists && d.Lookup != nil {
		route, exists = d.Lookup(c)
	}
	if !exists || route.Handler == nil {
		c.serve404()
		return
	}
	if route.Admin || !route.Anon {
		userID := c.UserID()
		if userID == 0 {
			// c.RaiseRedirect(c.LoginURL())
		}
	}
	if route.Cron && !c.IsCronRequest() {
		c.serve404()
		return
	}
	if route.XSRF && !c.ValidateXSRF() {
		c.serve404()
		return
	}
	route.Handler(c)
}

func (d *Dispatcher) StaticFile(expiration ...time.Duration) {

}

type mux []*Dispatcher

func (m mux) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if DevServer {
		log.Infof("[%s] %s", r.Method, r.URL)
	}
	path := r.URL.Path
	if path == "/_ah/health" {
		w.Write(healthOK)
		return
	}
	var match *Dispatcher
	found := false
	for _, d := range m {
		if strings.HasPrefix(path, d.Path) {
			found = true
			match = d
		}
	}
	if found {
		patchRemoteAddr(r)
		match.Dispatch(w, r)
		return
	}
	c := newContext(r, 0)
	c.serve404()
	writeResponse(c, w)
}

func OnStartup(h Handler) {
	startup = append(startup, h)
}

func Register(d *Dispatcher) {
	serveMux = append(serveMux, d)
}

func Run() {
	if port := os.Getenv("PORT"); port != "" {
		ServerPort = port
	}
	if DevServer {
		ServerHost = "localhost:" + ServerPort
	} else if config.CanonicalHost != "" {
		ServerHost = config.CanonicalHost
	} else {
		ServerHost = config.AppID + ".appspot.com"
	}
	if DevServer {
		fmt.Printf(">> Starting instance on port %s\n", ServerPort)
	}
	c := BackgroundContext()
	initCloud(c)
	if len(startup) > 0 {
		for _, handler := range startup {
			go handler(c)
		}
	}
	s := &http.Server{
		Addr:           ":" + ServerPort,
		Handler:        serveMux,
		MaxHeaderBytes: 1 << 20,
		ReadTimeout:    10 * time.Second,
		WriteTimeout:   10 * time.Second,
	}
	err := s.ListenAndServe()
	if err != nil {
		log.Fatalf("http.ListenAndServe: %v", err)
	}
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
